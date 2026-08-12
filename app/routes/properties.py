import os
import uuid
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from .. import db
from ..models import Property, PropertyImage
from ..forms import PropertyForm

properties_bp = Blueprint("properties", __name__)

# If CLOUDINARY_URL is set (e.g. cloudinary://key:secret@cloud_name), uploads
# go to Cloudinary and persist across deploys/restarts. Otherwise images are
# saved to the local static/uploads folder, which is fine for local
# development but does NOT persist on platforms with an ephemeral
# filesystem (e.g. Render's free tier) — see README "Deploying to Render".
CLOUDINARY_ENABLED = bool(os.environ.get("CLOUDINARY_URL"))
if CLOUDINARY_ENABLED:
    import cloudinary
    import cloudinary.uploader


def agent_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_agent:
            flash("Only agent accounts can manage listings.", "error")
            return redirect(url_for("properties.list_properties"))
        return func(*args, **kwargs)

    return wrapper


def save_image(file_storage):
    if isinstance(file_storage, (list, tuple)):
        return [saved for image in file_storage if (saved := save_image(image))]

    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return None

    if CLOUDINARY_ENABLED:
        result = cloudinary.uploader.upload(file_storage, folder="haven-listings")
        return result["secure_url"]

    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return unique_name


def uploaded_images(form):
    return [image for image in form.images.data if image and image.filename]


def next_image_position(prop):
    return max((image.position for image in prop.images), default=-1) + 1


def append_images(prop, images):
    for position, image_path in enumerate(save_image(images), start=next_image_position(prop)):
        db.session.add(PropertyImage(property_id=prop.id, image_path=image_path, position=position))


@properties_bp.route("/")
def list_properties():
    page = request.args.get("page", 1, type=int)

    q = request.args.get("q", "", type=str).strip()
    city = request.args.get("city", "", type=str).strip()
    listing_type = request.args.get("listing_type", "", type=str).strip()
    property_type = request.args.get("property_type", "", type=str).strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    bedrooms = request.args.get("bedrooms", type=int)

    query = Property.query.filter_by(is_available=True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Property.title.ilike(like),
                Property.description.ilike(like),
                Property.address.ilike(like),
            )
        )
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if listing_type in ("sale", "rent"):
        query = query.filter_by(listing_type=listing_type)
    if property_type:
        query = query.filter_by(property_type=property_type)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)

    query = query.order_by(Property.created_at.desc())

    per_page = current_app.config["PROPERTIES_PER_PAGE"]
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    filters = {
        "q": q, "city": city, "listing_type": listing_type,
        "property_type": property_type, "min_price": request.args.get("min_price", ""),
        "max_price": request.args.get("max_price", ""), "bedrooms": request.args.get("bedrooms", ""),
    }

    return render_template(
        "properties/list.html",
        pagination=pagination,
        properties=pagination.items,
        filters=filters,
    )


@properties_bp.route("/<int:property_id>")
def detail(property_id):
    prop = Property.query.get_or_404(property_id)
    from ..forms import InquiryForm
    form = InquiryForm()
    if current_user.is_authenticated:
        form.name.data = form.name.data or current_user.name
        form.email.data = form.email.data or current_user.email
    similar = (
        Property.query.filter(
            Property.city == prop.city,
            Property.id != prop.id,
            Property.is_available.is_(True),
        )
        .limit(3)
        .all()
    )
    return render_template("properties/detail.html", property=prop, form=form, similar=similar)


@properties_bp.route("/new", methods=["GET", "POST"])
@login_required
@agent_required
def create():
    form = PropertyForm()
    if form.validate_on_submit():
        images = uploaded_images(form)
        prop = Property(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            price=form.price.data,
            listing_type=form.listing_type.data,
            property_type=form.property_type.data,
            bedrooms=form.bedrooms.data or 0,
            bathrooms=form.bathrooms.data or 0,
            area_sqft=form.area_sqft.data or 0,
            address=form.address.data.strip() if form.address.data else None,
            city=form.city.data.strip(),
            state=form.state.data.strip(),
            is_available=form.is_available.data,
            owner_id=current_user.id,
        )
        db.session.add(prop)
        db.session.flush()
        append_images(prop, images)
        db.session.commit()
        flash("Listing published successfully.", "success")
        return redirect(url_for("properties.detail", property_id=prop.id))

    return render_template("properties/form.html", form=form, mode="create")


@properties_bp.route("/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
@agent_required
def edit(property_id):
    prop = Property.query.get_or_404(property_id)
    if prop.owner_id != current_user.id:
        abort(403)

    form = PropertyForm(obj=prop)
    if form.validate_on_submit():
        images = uploaded_images(form)
        if len(prop.images) + len(images) > 8:
            form.images.errors.append("A listing can have a maximum of 8 images.")
            return render_template("properties/form.html", form=form, mode="edit", property=prop)

        prop.title = form.title.data.strip()
        prop.description = form.description.data.strip()
        prop.price = form.price.data
        prop.listing_type = form.listing_type.data
        prop.property_type = form.property_type.data
        prop.bedrooms = form.bedrooms.data or 0
        prop.bathrooms = form.bathrooms.data or 0
        prop.area_sqft = form.area_sqft.data or 0
        prop.address = form.address.data.strip() if form.address.data else None
        prop.city = form.city.data.strip()
        prop.state = form.state.data.strip()
        prop.is_available = form.is_available.data

        append_images(prop, images)

        db.session.commit()
        flash("Listing updated.", "success")
        return redirect(url_for("properties.detail", property_id=prop.id))

    return render_template("properties/form.html", form=form, mode="edit", property=prop)


@properties_bp.route("/<int:property_id>/images/<int:image_id>/delete", methods=["POST"])
@login_required
@agent_required
def delete_image(property_id, image_id):
    prop = Property.query.get_or_404(property_id)
    if prop.owner_id != current_user.id:
        abort(403)
    image = PropertyImage.query.filter_by(id=image_id, property_id=prop.id).first_or_404()
    was_cover = image.position == 0
    db.session.delete(image)
    db.session.flush()
    remaining_images = PropertyImage.query.filter_by(property_id=prop.id).order_by(PropertyImage.position).all()
    if was_cover and remaining_images:
        remaining_images[0].position = 0
    for position, remaining_image in enumerate(remaining_images):
        remaining_image.position = position
    db.session.commit()
    flash("Photo deleted.", "info")
    return redirect(url_for("properties.edit", property_id=prop.id))


@properties_bp.route("/<int:property_id>/images/<int:image_id>/make-cover", methods=["POST"])
@login_required
@agent_required
def make_cover(property_id, image_id):
    prop = Property.query.get_or_404(property_id)
    if prop.owner_id != current_user.id:
        abort(403)
    image = PropertyImage.query.filter_by(id=image_id, property_id=prop.id).first_or_404()
    cover = PropertyImage.query.filter_by(property_id=prop.id, position=0).first()
    if cover and cover.id != image.id:
        cover.position, image.position = image.position, cover.position
    db.session.commit()
    flash("Cover photo updated.", "success")
    return redirect(url_for("properties.edit", property_id=prop.id))


@properties_bp.route("/<int:property_id>/delete", methods=["POST"])
@login_required
@agent_required
def delete(property_id):
    prop = Property.query.get_or_404(property_id)
    if prop.owner_id != current_user.id:
        abort(403)
    db.session.delete(prop)
    db.session.commit()
    flash("Listing removed.", "info")
    return redirect(url_for("properties.my_properties"))


@properties_bp.route("/mine")
@login_required
@agent_required
def my_properties():
    props = (
        Property.query.filter_by(owner_id=current_user.id)
        .order_by(Property.created_at.desc())
        .all()
    )
    return render_template("properties/my_properties.html", properties=props)
