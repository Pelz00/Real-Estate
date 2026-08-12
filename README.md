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

## Deploying to Render

This app is ready for Render as-is — it uses `gunicorn` as the production
server and automatically switches from SQLite to Postgres when a
`DATABASE_URL` environment variable is present.

**Before you deploy, know this:** Render's free web services have an
*ephemeral* filesystem. Anything written to disk — your SQLite file, and any
property photos uploaded through the app — is wiped on every restart,
redeploy, or spin-down. So:

- **Database:** use Render's managed Postgres (covered below), not SQLite.
- **Uploaded photos:** the local `static/uploads` folder will NOT persist on
  the free tier. This app already supports Cloudinary as a drop-in swap: set
  a `CLOUDINARY_URL` environment variable (format:
  `cloudinary://<api_key>:<api_secret>@<cloud_name>`, from your Cloudinary
  dashboard) and every new upload automatically goes there instead of local
  disk — no code changes needed. Leave it unset for local development.
  Alternatively, Render sells persistent disks on paid plans.

### Option A — one-click Blueprint (recommended)

The repo includes a `render.yaml` that provisions both the web service and a
free Postgres database together.

1. Push this project to a GitHub (or GitLab) repo.
2. In the Render dashboard: **New +** → **Blueprint** → connect your repo.
3. Render reads `render.yaml` and shows you a web service (`haven-realestate`)
   plus a database (`haven-db`) it's about to create. Click **Apply**.
4. Render builds and deploys automatically. `SECRET_KEY` is auto-generated
   and `DATABASE_URL` is wired to the new database for you — no manual env
   var setup needed. If you want photo uploads to persist, add a
   `CLOUDINARY_URL` environment variable to the service afterward (Environment
   tab → Add Environment Variable).
5. Once it's live, open a shell for the service in the Render dashboard (or
   run it once via a one-off job) and seed it:
   ```bash
   python seed.py      # demo data, OR:
   python create_admin.py "Your Name" you@example.com yourpassword
   ```

### Option B — manual setup

1. Push the project to GitHub.
2. **New +** → **PostgreSQL** in Render. Free plan is fine to start (note the
   30-day expiry mentioned above). Once created, copy the **Internal
   Database URL**.
3. **New +** → **Web Service** → connect your repo.
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn run:app`
4. Under the service's **Environment** tab, add:
   - `SECRET_KEY` — any long random string
   - `DATABASE_URL` — the Internal Database URL from step 2
   - `PYTHON_VERSION` — `3.11.9`
5. Deploy. Render gives you a live `https://your-app.onrender.com` URL.

### After it's live

- The free web service sleeps after 15 minutes of inactivity and takes about
  a minute to wake back up on the next visit — normal on the free tier, fixed
  by upgrading to a paid instance ($7/mo Starter) if that matters for your
  use case.
- Tables are created automatically on first boot (`db.create_all()` runs
  inside the app factory), so there's no separate migration step to run.

## Notes on production use

- Set a strong, random `SECRET_KEY` via environment variable (handled
  automatically if you used the Blueprint above).
- Point `DATABASE_URL` at Postgres/MySQL instead of SQLite (handled by
  Render's managed Postgres above).
- Put uploaded images behind a CDN or object storage (S3, Cloudinary, etc.)
  instead of the local `static/uploads` folder — required on Render's free
  tier since local files don't persist.
- Run behind Gunicorn/uWSGI + Nginx, with `debug=False` (Render's
  `gunicorn run:app` start command already does this).
