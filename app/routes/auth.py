from urllib.parse import urljoin, urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from .. import db
from ..models import User
from ..forms import (
    ForgotPasswordForm, LoginForm, RegisterForm, SetNewPasswordForm,
    VerifyEmailForm, VerifyResetCodeForm,
)
from ..email import send_password_reset_code_email, send_verification_email

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

        code = user.set_verification_code()
        db.session.commit()
        print(f"CALLING send_verification_email FOR {user.email}")
        send_verification_email(user, code)
        session["pending_verification_user_id"] = user.id
        flash("Check your email for a 6-digit verification code.", "info")
        return redirect(url_for("auth.verify_email"))

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
            if not user.email_verified:
                code = user.set_verification_code()
                db.session.commit()
                print(f"CALLING send_verification_email FOR {user.email}")
                send_verification_email(user, code)
                session["pending_verification_user_id"] = user.id
                flash("Please verify your email first — we've sent you a new code.", "info")
                return redirect(url_for("auth.verify_email"))
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name.split()[0]}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if is_safe_redirect_target(next_page) else url_for("main.home"))
        flash("Incorrect email or password. Please try again.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    user_id = session.get("pending_verification_user_id")
    if not user_id:
        flash("There is no email verification in progress.", "info")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if not user:
        session.pop("pending_verification_user_id", None)
        flash("There is no email verification in progress.", "info")
        return redirect(url_for("auth.login"))
    if user.email_verified:
        session.pop("pending_verification_user_id", None)
        return redirect(url_for("auth.login"))

    form = VerifyEmailForm()
    if form.validate_on_submit():
        if user.verify_code(form.code.data):
            user.email_verified = True
            user.verification_code_hash = None
            user.verification_code_expires_at = None
            db.session.commit()
            session.pop("pending_verification_user_id", None)
            login_user(user)
            flash("Email verified — welcome to Haven & Co.!", "success")
            return redirect(url_for("main.home"))
        flash("That code is incorrect or has expired.", "error")

    return render_template("auth/verify_email.html", form=form, user=user)


@auth_bp.route("/resend-verification-code", methods=["POST"])
def resend_verification_code():
    user_id = session.get("pending_verification_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user or user.email_verified:
        session.pop("pending_verification_user_id", None)
        flash("There is no email verification in progress.", "info")
        return redirect(url_for("auth.login"))

    # Production should rate-limit this endpoint per user/IP to prevent email abuse.
    code = user.set_verification_code()
    db.session.commit()
    print(f"CALLING send_verification_email FOR {user.email}")
    send_verification_email(user, code)
    flash("A new code has been sent.", "info")
    return redirect(url_for("auth.verify_email"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        # Production should rate-limit this endpoint per IP/email (e.g. Flask-Limiter).
        session.pop("password_reset_user_id", None)
        session.pop("password_reset_verified", None)
        # Keep the next screen identical for known and unknown email addresses.
        session["password_reset_requested"] = True
        if user:
            code = user.set_reset_code()
            db.session.commit()
            print(f"CALLING send_password_reset_code_email FOR {user.email}")
            send_password_reset_code_email(user, code)
            session["password_reset_user_id"] = user.id
        flash("If an account with that email exists, we've sent a password reset code.", "info")
        return redirect(url_for("auth.verify_reset_code"))

    if request.method == "POST":
        # Keep validation failures visible instead of silently re-rendering the form.
        flash("Please check the email address and try again.", "error")

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/verify-reset-code", methods=["GET", "POST"])
def verify_reset_code():
    user_id = session.get("password_reset_user_id")
    if not session.get("password_reset_requested"):
        flash("There is no password reset in progress.", "info")
        return redirect(url_for("auth.forgot_password"))

    user = db.session.get(User, user_id) if user_id else None

    form = VerifyResetCodeForm()
    if form.validate_on_submit():
        if user and user.verify_reset_code(form.code.data):
            user.set_password(form.password.data)
            user.reset_code_hash = None
            user.reset_code_expires_at = None
            db.session.commit()
            session.pop("password_reset_user_id", None)
            session.pop("password_reset_verified", None)
            session.pop("password_reset_requested", None)
            flash("Your password has been updated. Please log in.", "success")
            return redirect(url_for("auth.login"))
        flash("That code is incorrect or has expired.", "error")

    return render_template("auth/verify_reset_code.html", form=form)


@auth_bp.route("/resend-reset-code", methods=["POST"])
def resend_reset_code():
    user_id = session.get("password_reset_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user:
        session.pop("password_reset_user_id", None)
        session.pop("password_reset_verified", None)
        session.pop("password_reset_requested", None)
        flash("There is no password reset in progress.", "info")
        return redirect(url_for("auth.forgot_password"))

    # Production should rate-limit this endpoint per user/IP to prevent email abuse.
    code = user.set_reset_code()
    db.session.commit()
    print(f"CALLING send_password_reset_code_email FOR {user.email}")
    send_password_reset_code_email(user, code)
    flash("A new code has been sent.", "info")
    return redirect(url_for("auth.verify_reset_code"))


@auth_bp.route("/set-new-password", methods=["GET", "POST"])
def set_new_password():
    user_id = session.get("password_reset_user_id")
    if not user_id or not session.get("password_reset_verified"):
        flash("Verify your reset code before choosing a new password.", "info")
        return redirect(url_for("auth.forgot_password"))

    user = db.session.get(User, user_id)
    if not user:
        session.pop("password_reset_user_id", None)
        session.pop("password_reset_verified", None)
        session.pop("password_reset_requested", None)
        flash("There is no password reset in progress.", "info")
        return redirect(url_for("auth.forgot_password"))

    form = SetNewPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        session.pop("password_reset_user_id", None)
        session.pop("password_reset_verified", None)
        session.pop("password_reset_requested", None)
        flash("Your password has been updated. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/set_new_password.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.home"))
