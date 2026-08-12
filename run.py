"""
Entry point for the Haven & Co. real estate platform.

Run with:
    python run.py

The app will be available at http://127.0.0.1:5000
"""
import os
from app import create_app, db
from app.models import User, Property, Inquiry

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Property": Property, "Inquiry": Inquiry}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(debug=debug, port=port)
