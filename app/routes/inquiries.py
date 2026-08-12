from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from .. import db
from ..models import Property, Inquiry
from ..forms import InquiryForm

inquiries_bp = Blueprint("inquiries", __name__)


@inquiries_bp.route("/property/<int:property_id>/send", methods=["POST"])
def send(property_id):
    prop = Property.query.get_or_404(property_id)
    form = InquiryForm()

    if not prop.is_available:
        flash("This listing is no longer accepting inquiries.", "error")
        return redirect(url_for("properties.detail", property_id=prop.id))

    if current_user.is_authenticated and current_user.id == prop.owner_id:
        flash("You cannot send an inquiry about your own listing.", "error")
        return redirect(url_for("properties.detail", property_id=prop.id))

    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            message=form.message.data.strip(),
            property_id=prop.id,
            sender_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Your inquiry was sent! The agent will reach out to you shortly.", "success")
    else:
        flash("Please check your inquiry details and try again.", "error")

    return redirect(url_for("properties.detail", property_id=prop.id))


@inquiries_bp.route("/received")
@login_required
def received():
    if not current_user.is_agent:
        flash("Only agents receive property inquiries.", "error")
        return redirect(url_for("main.home"))

    my_property_ids = [p.id for p in current_user.properties]
    inquiries = (
        Inquiry.query.filter(Inquiry.property_id.in_(my_property_ids))
        .order_by(Inquiry.created_at.desc())
        .all()
        if my_property_ids
        else []
    )
    return render_template("inquiries/received.html", inquiries=inquiries)


@inquiries_bp.route("/<int:inquiry_id>/resolve", methods=["POST"])
@login_required
def resolve(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    if inquiry.property.owner_id != current_user.id:
        abort(403)
    inquiry.status = "responded" if inquiry.status == "new" else "new"
    db.session.commit()
    return redirect(url_for("inquiries.received"))


@inquiries_bp.route("/sent")
@login_required
def sent():
    inquiries = (
        Inquiry.query.filter_by(sender_id=current_user.id)
        .order_by(Inquiry.created_at.desc())
        .all()
    )
    return render_template("inquiries/sent.html", inquiries=inquiries)
