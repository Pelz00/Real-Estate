from flask import Blueprint, render_template
from ..models import Property

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    featured = (
        Property.query.filter_by(is_available=True)
        .order_by(Property.created_at.desc())
        .limit(6)
        .all()
    )
    stats = {
        "listings": Property.query.filter_by(is_available=True).count(),
        "cities": len({p.city for p in Property.query.with_entities(Property.city).distinct()}),
    }
    return render_template("index.html", featured=featured, stats=stats)
