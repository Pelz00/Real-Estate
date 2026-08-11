from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="buyer")  # 'buyer', 'agent', or 'admin'
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
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

    @property
    def formatted_price(self):
        suffix = "/mo" if self.listing_type == "rent" else ""
        return f"${self.price:,.0f}{suffix}"

    @property
    def cover_image(self):
        return self.image_filename or None

    def __repr__(self):
        return f"<Property {self.title}>"


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
