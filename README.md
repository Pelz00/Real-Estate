# Haven & Co. — Real Estate Platform

A full-stack Flask real estate platform with authentication, property listings,
search, pagination, inquiries, and a light/dark theme toggle.

## Features

- **User accounts** — registration and login with hashed passwords (Flask-Login).
  Three roles: **admin** (moderates the whole platform), **agent** (can
  publish/manage listings), and **buyer** (can search and send inquiries).
- **Property listings** — full CRUD for agents, with photo upload, price, type
  (sale/rent), bedrooms/bathrooms/area, and location.
- **Property search** — filter by keyword, city, listing type, property type,
  price range, and minimum bedrooms, all via a live search panel.
- **Pagination** — listings page paginates results (9 per page by default).
- **Property inquiries** — buyers (or guests) can message an agent from a
  property page; agents see every inquiry in a dashboard and can mark it as
  responded.
- **Admin panel** — a dashboard with platform-wide stats, a users table
  (promote/demote roles, deactivate or delete accounts), a properties table
  (take any listing offline or delete it), and a site-wide view of every
  inquiry across all agents.
- **Light / dark mode** — a toggle in the navbar switches themes instantly,
  remembers the choice in `localStorage`, and respects the visitor's system
  preference on first visit (no flash of the wrong theme).

## Tech stack

- Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- SQLite (zero-config; swap `DATABASE_URL` for Postgres/MySQL in production)
- Vanilla CSS with design tokens (no framework) + vanilla JS for the theme
  toggle and mobile nav — nothing to build/compile

## Getting started

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) copy the env example and adjust it
cp .env.example .env

# 4. (Optional) load demo data — 3 accounts + 6 listings + 1 inquiry
python seed.py

# 5. Run the app
python run.py
```

Visit **http://127.0.0.1:5000**.

If you ran `seed.py`, log in with:

| Role  | Email            | Password    |
|-------|------------------|-------------|
| Admin | admin@haven.com  | password123 |
| Agent | agent@haven.com  | password123 |
| Buyer | buyer@haven.com  | password123 |

If you skip seeding, just register a new account — choose **Agent / Property
Owner** during sign-up to unlock listing management. New accounts can't
self-assign the admin role (by design); to create one, run:

```bash
python create_admin.py "Your Name" you@example.com yourpassword
```

This creates a new admin account, or promotes an existing user to admin if
the email already exists — without wiping the rest of the database (unlike
`seed.py`, which resets everything).

## Project structure

```
realestate/
├── run.py                  # entry point
├── seed.py                 # optional demo data
├── requirements.txt
├── app/
│   ├── __init__.py         # app factory
│   ├── config.py
│   ├── models.py           # User, Property, Inquiry
│   ├── forms.py            # Flask-WTF forms
│   ├── routes/
│   │   ├── auth.py         # register / login / logout
│   │   ├── main.py         # home page
│   │   ├── properties.py   # listing CRUD, search, pagination
│   │   ├── inquiries.py    # send / view inquiries
│   │   └── admin.py        # platform-wide moderation dashboard
│   ├── templates/
│   └── static/
│       ├── css/style.css   # theme tokens + all components
│       ├── js/main.js      # theme toggle, mobile nav
│       └── uploads/        # uploaded property photos
```

## Notes on production use

- Set a strong, random `SECRET_KEY` via environment variable.
- Point `DATABASE_URL` at Postgres/MySQL instead of SQLite.
- Put uploaded images behind a CDN or object storage (S3, Cloudinary, etc.)
  instead of the local `static/uploads` folder.
- Run behind Gunicorn/uWSGI + Nginx, with `debug=False`.
