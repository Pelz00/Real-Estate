"""
Create a new admin account, or promote an existing user to admin, without
touching the rest of the database (unlike seed.py, which wipes everything).

Usage:
    python create_admin.py "Jane Doe" jane@example.com yourpassword

If the email already belongs to an existing user, that account is simply
promoted to the admin role (password left unchanged).
"""
import sys
from app import create_app, db
from app.models import User

app = create_app()


def main():
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py \"Full Name\" email@example.com password")
        sys.exit(1)

    name, email, password = sys.argv[1], sys.argv[2].lower().strip(), sys.argv[3]

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.role = "admin"
            user.is_active = True
            db.session.commit()
            print(f"Existing user '{email}' promoted to admin.")
        else:
            user = User(name=name, email=email, role="admin")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"Admin account created for '{email}'.")


if __name__ == "__main__":
    main()
