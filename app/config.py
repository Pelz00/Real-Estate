import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'haven.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB max upload

    PROPERTIES_PER_PAGE = 9
