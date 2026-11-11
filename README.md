# Basera

Basera helps people in Pakistan choose and buy **native plants** that suit their own growing conditions.
A customer describes their space once (a *grow profile*) and Basera ranks native species for it, explains
why each one fits, and hides invasive species. Sellers list plants; customers order with Cash on Delivery.

Built with Django 5, Bootstrap 5 and HTMX. Full specification: [spec.md](spec.md).
Choices made where the spec was silent: [docs/DECISIONS.md](docs/DECISIONS.md).

**Live site:** _add the Render URL here after the first deploy_

## Run it locally (under five minutes)

You need Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/. With no `DATABASE_URL` set the app uses a local SQLite file (`db.sqlite3`),
and emails (such as order confirmations and password resets) are printed in the terminal.

## Demo accounts (test values only)

`python manage.py seed_demo` creates these if they do not exist and prints their password.
Safe to run again at any time.

| Role | Email | Password |
|---|---|---|
| Customer | `customer@basera.test` | `Basera-demo-2026` |
| Seller | `seller@basera.test` | `Basera-demo-2026` |
| Admin | `admin@basera.test` | `Basera-demo-2026` |

Set the `DEMO_PASSWORD` environment variable before seeding to use a different password
(do this in production).

The seed data has 5 regions, 35 native species (4 flagged invasive), and a sample grow profile
called "Backyard" for the demo customer.

## Sprint 1 demo script

1. **Sign up** at `/accounts/signup/` as a Customer (or use the demo customer).
2. **Log in** at `/accounts/login/`; you land on "My Grow Profiles".
3. **Create a grow profile** with "New profile" (name, region, indoor/outdoor, sunlight, soil, water, goal).
4. Click **Find plants** on the profile. You see native species ranked by a 0-100% score, each with
   reasons (✔ match, ◐ partial, ✘ no match) and its ecological benefit. Invasive species never appear.
5. Click **View details** on a species to open its page.
6. Open the **Catalogue** and search (results update as you type). Invasive species appear there with a
   red "Invasive — not sold" warning.

## Environment variables

Also listed in `.env.example`. A local `.env` file is read automatically.

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key. **Required in production.** | insecure dev key |
| `DEBUG` | `True` / `False`. Must be `False` in production. | `True` |
| `ALLOWED_HOSTS` | Comma-separated host names | `localhost,127.0.0.1,testserver` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins, e.g. `https://basera.onrender.com` | none |
| `DATABASE_URL` | PostgreSQL connection string | local SQLite |
| `EMAIL_BACKEND` | Set to the SMTP backend to send real email | console backend |
| `DEMO_PASSWORD` | Password for the demo accounts created by `seed_demo` | `Basera-demo-2026` |

## Deployment (Render)

The app and a PostgreSQL database are deployed on [Render](https://render.com) using `render.yaml`.

1. Push this repository to GitHub.
2. In Render choose **New → Blueprint** and pick the repository. It creates the web service and the
   free `basera-db` database, and generates `SECRET_KEY` and `DEMO_PASSWORD`.
3. Render runs `build.sh` (install, `collectstatic`, `migrate`, `seed_demo`) and then
   `gunicorn basera.wsgi`.
4. Check the `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` values for your service URL, then copy the live
   URL into this README. The `DEMO_PASSWORD` value is in the service's Environment tab.

**To redeploy:** push to `main`; Render rebuilds automatically. `seed_demo` is idempotent, so redeploys
never duplicate data.

**Uploaded images:** free hosts have an ephemeral disk, so images uploaded in production may disappear on
redeploy. The demo species use the built-in placeholder image so the site always looks complete.

## Project layout

`accounts` (users, login) · `growprofiles` (regions, grow profiles) · `catalog` (species, catalogue) ·
`matching` (scoring service and results) · `orders` (cart and orders, Sprint 2). Shared templates are in
`templates/`, shared helpers in `basera/forms.py` and `basera/htmx.py`.
