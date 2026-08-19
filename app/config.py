import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _normalize_db_url(url):
    """Render (and Heroku) hand out 'postgres://' URLs, but SQLAlchemy 2.x
    requires the 'postgresql://' scheme. Rewrite it if needed."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    # Resolve local relative SQLite paths from the project root. Flask-
    # SQLAlchemy otherwise interprets them relative to Flask's instance path.
    if url and url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        sqlite_path = url.removeprefix("sqlite:///")
        if sqlite_path != ":memory:":
            return "sqlite:///" + os.path.abspath(os.path.join(BASE_DIR, sqlite_path))
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL")
    ) or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'haven.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB max upload

    PROPERTIES_PER_PAGE = 9
