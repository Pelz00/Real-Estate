from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


def resolve_image_url(image_path):
    """Resolve either a Cloudinary URL or a filename stored under static/uploads."""
    if not image_path:
        return None
    if image_path.startswith(("http://", "https://")):
        return image_path
    from flask import url_for
    return url_for("static", filename="uploads/" + image_path)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="buyer")  # 'buyer', 'agent', or 'admin'
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_code_hash = db.Column(db.String(255), nullable=True)
    verification_code_expires_at = db.Column(db.DateTime, nullable=True)
    reset_code_hash = db.Column(db.String(255), nullable=True)
    reset_code_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    properties = db.relationship(
        "Property", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    inquiries_sent = db.relationship(
        "Inquiry", backref="sender", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_verification_code(self, expires_minutes=15):
        """Generate and store a short-lived email-verification code."""
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        self.verification_code_hash = generate_password_hash(code)
        self.verification_code_expires_at = datetime.utcnow() + timedelta(
            minutes=expires_minutes
        )
        return code

    def verify_code(self, submitted_code):
        """Return whether a submitted verification code is valid and current."""
        return bool(
            self.verification_code_hash
            and self.verification_code_expires_at
            and self.verification_code_expires_at >= datetime.utcnow()
            and check_password_hash(self.verification_code_hash, submitted_code)
        )

    def set_reset_code(self, expires_minutes=15):
        """Generate and store a short-lived password-reset code."""
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        self.reset_code_hash = generate_password_hash(code)
        self.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        return code

    def verify_reset_code(self, submitted_code):
        """Return whether a submitted password-reset code is valid and current."""
        return bool(
            self.reset_code_hash
            and self.reset_code_expires_at
            and self.reset_code_expires_at >= datetime.utcnow()
            and check_password_hash(self.reset_code_hash, submitted_code)
        )

    @property
    def is_agent(self):
        return self.role == "agent"

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"


class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    price = db.Column(db.Float, nullable=False)
    listing_type = db.Column(db.String(10), nullable=False, default="sale")  # 'sale' or 'rent'
    property_type = db.Column(db.String(30), nullable=False, default="house")

    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    area_sqft = db.Column(db.Integer, default=0)

    address = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False, index=True)

    image_filename = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    inquiries = db.relationship(
        "Inquiry", backref="property", lazy="dynamic", cascade="all, delete-orphan"
    )
    images = db.relationship(
        "PropertyImage",
        backref="property",
        order_by="PropertyImage.position",
        cascade="all, delete-orphan",
    )

    @property
    def formatted_price(self):
        suffix = "/mo" if self.listing_type == "rent" else ""
        return f"${self.price:,.0f}{suffix}"

    @property
    def image_url(self):
        if self.images:
            return resolve_image_url(self.images[0].image_path)
        return resolve_image_url(self.image_filename)

    @property
    def gallery_urls(self):
        if self.images:
            return [resolve_image_url(image.image_path) for image in self.images]
        legacy_url = resolve_image_url(self.image_filename)
        return [legacy_url] if legacy_url else []

    def __repr__(self):
        return f"<Property {self.title}>"


class PropertyImage(db.Model):
    __tablename__ = "property_images"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    image_path = db.Column(db.String(500), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def url(self):
        return resolve_image_url(self.image_path)

    def __repr__(self):
        return f"<PropertyImage {self.id} for property {self.property_id}>"


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="new")  # 'new' or 'responded'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Inquiry {self.id} for property {self.property_id}>"
