from urllib.parse import urljoin, urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from .. import db
from ..models import User
from ..forms import RegisterForm, LoginForm

auth_bp = Blueprint("auth", __name__)


def is_safe_redirect_target(target):
    """Allow redirects only to paths on this application."""
    if not target:
        return False
    host_url = urlparse(request.host_url)
    target_url = urlparse(urljoin(request.host_url, target))
    return target_url.scheme in ("http", "https") and target_url.netloc == host_url.netloc


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with that email already exists. Try logging in instead.", "error")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to Haven & Co., {user.name.split()[0]}!", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account has been deactivated. Contact an administrator.", "error")
                return render_template("auth/login.html", form=form)
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name.split()[0]}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if is_safe_redirect_target(next_page) else url_for("main.home"))
        flash("Incorrect email or password. Please try again.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.home"))
