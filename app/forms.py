from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, TextAreaField,
    FloatField, IntegerField, BooleanField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from wtforms.validators import ValidationError


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=30)])
    role = SelectField(
        "I am a...",
        choices=[("buyer", "Buyer / Renter"), ("agent", "Agent / Property Owner")],
        default="buyer",
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class PropertyForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[DataRequired()])

    price = FloatField("Price ($)", validators=[DataRequired(), NumberRange(min=0)])
    listing_type = SelectField(
        "Listing type", choices=[("sale", "For sale"), ("rent", "For rent")]
    )
    property_type = SelectField(
        "Property type",
        choices=[
            ("house", "House"),
            ("apartment", "Apartment"),
            ("condo", "Condo"),
            ("land", "Land"),
            ("commercial", "Commercial"),
        ],
    )

    bedrooms = IntegerField("Bedrooms", validators=[Optional(), NumberRange(min=0)], default=0)
    bathrooms = IntegerField("Bathrooms", validators=[Optional(), NumberRange(min=0)], default=0)
    area_sqft = IntegerField("Area (sqft)", validators=[Optional(), NumberRange(min=0)], default=0)

    address = StringField("Street address", validators=[Optional(), Length(max=200)])
    city = StringField("City", validators=[DataRequired(), Length(max=100)])
    state = StringField("State", validators=[DataRequired(), Length(max=100)])

    images = MultipleFileField(
        "Property photos",
        validators=[FileAllowed(["png", "jpg", "jpeg", "webp", "gif"], "Images only!")],
    )
    is_available = BooleanField("Listing is active", default=True)

    submit = SubmitField("Save listing")

    def validate_images(self, field):
        uploaded_images = [image for image in field.data if image and image.filename]
        if len(uploaded_images) > 8:
            raise ValidationError("You can upload a maximum of 8 images per listing.")


class InquiryForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Your email", validators=[DataRequired(), Email()])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=30)])
    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(max=1000)],
        default="Hi, I'm interested in this property. Please contact me with more details.",
    )
    submit = SubmitField("Send inquiry")


class SearchForm(FlaskForm):
    """Not rendered with WTF macros directly (uses GET), kept for reference/validation."""
    class Meta:
        csrf = False

    q = StringField("Keyword")
    city = StringField("City")
    listing_type = SelectField(
        "Listing type",
        choices=[("", "Any"), ("sale", "For sale"), ("rent", "For rent")],
        validators=[Optional()],
    )
    property_type = SelectField(
        "Property type",
        choices=[
            ("", "Any"),
            ("house", "House"),
            ("apartment", "Apartment"),
            ("condo", "Condo"),
            ("land", "Land"),
            ("commercial", "Commercial"),
        ],
        validators=[Optional()],
    )
    min_price = FloatField("Min price", validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField("Max price", validators=[Optional(), NumberRange(min=0)])
    bedrooms = SelectField(
        "Bedrooms",
        choices=[("", "Any"), ("1", "1+"), ("2", "2+"), ("3", "3+"), ("4", "4+"), ("5", "5+")],
        validators=[Optional()],
    )
