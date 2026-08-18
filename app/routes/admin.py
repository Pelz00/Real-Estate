from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from .. import db
from ..models import User, Property, Inquiry

admin_bp = Blueprint("admin", __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "agents": User.query.filter_by(role="agent").count(),
        "buyers": User.query.filter_by(role="buyer").count(),
        "listings": Property.query.count(),
        "active_listings": Property.query.filter_by(is_available=True).count(),
        "inquiries": Inquiry.query.count(),
        "new_inquiries": Inquiry.query.filter_by(status="new").count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html", stats=stats,
        recent_users=recent_users, recent_properties=recent_properties,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role not in ("buyer", "agent", "admin"):
        flash("Invalid role.", "error")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id and new_role != "admin":
        flash("You can't remove your own admin role.", "error")
        return redirect(url_for("admin.users"))
    user.role = new_role
    db.session.commit()
    flash(f"{user.name} is now a{'n' if new_role == 'admin' else ''} {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't deactivate your own account.", "error")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.name} was {'reactivated' if user.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "error")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"{user.name}'s account and all their listings were deleted.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/properties")
@login_required
@admin_required
def properties():
    all_properties = Property.query.order_by(Property.created_at.desc()).all()
    return render_template("admin/properties.html", properties=all_properties)


@admin_bp.route("/properties/<int:property_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_property(property_id):
    prop = Property.query.get_or_404(property_id)
    prop.is_available = not prop.is_available
    db.session.commit()
    flash(f"'{prop.title}' is now {'active' if prop.is_available else 'off market'}.", "info")
    return redirect(url_for("admin.properties"))


@admin_bp.route("/properties/<int:property_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_property(property_id):
    prop = Property.query.get_or_404(property_id)
    db.session.delete(prop)
    db.session.commit()
    flash("Listing removed by admin.", "info")
    return redirect(url_for("admin.properties"))


@admin_bp.route("/inquiries")
@login_required
@admin_required
def inquiries():
    all_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template("admin/inquiries.html", inquiries=all_inquiries)
