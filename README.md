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

## What you can do

**Guests** browse the catalogue (search as you type) and species pages, sign up and log in.

**Customers**
1. Create one or more **grow profiles** (region, indoor/outdoor, sunlight, soil, water, goal) under
   *Find plants* / *My profiles*; edit or delete them.
2. Click **Find plants** on a profile for a ranked list of native species with a 0-100% score, the reasons
   (✔ match, ◐ partial, ✘ no match) and the ecological benefit. Invasive species never appear.
   Filter by purpose, indoor/outdoor and price, and sort, without a page reload.
3. **Add to cart**, review the cart, enter delivery details, place the order (Cash on Delivery) and see
   it under *My orders*. Pending orders can be cancelled and the stock returns.
4. Manage the **profile** (*Profile*), change the password, or reset a forgotten one (the email is printed
   in the terminal when running locally).

**Sellers** (`seller@basera.test`) manage **My listings** (create, edit, remove, stock, active/inactive,
search, filter) and move orders for their plants through Pending → Confirmed → Shipped → Delivered on
**Orders**.

**Admins** (`admin@basera.test`, at `/admin/`) manage regions (a region in use cannot be deleted),
flag invasive species, deactivate listings and manage users.

## Sprint 1 demo script

1. **Sign up** at `/accounts/signup/` as a Customer (or use the demo customer).
2. **Log in** at `/accounts/login/`; you land on "My Grow Profiles".
3. **Create a grow profile** with "New profile".
4. Click **Find plants**: a ranked list with scores and reasons; invasive species are never shown.
5. Click **View details** on a species.
6. Open the **Catalogue** and search. Invasive species appear there with a red warning and no cart button.

## Sprint 2 demo script

1. As the customer, on a match card press **Add to cart** (the button turns into "Added ✔" and the cart
   count in the navbar updates). Open **Cart**, change a quantity, then **Checkout**.
2. Enter delivery details (phone like `03001234567`), review the summary and **Place order**. The
   confirmation email appears in the terminal.
3. Log out and log in as `seller@basera.test`. Under **Orders** press *Mark as Confirmed*. Log back in as the
   customer and open **My orders** to see the new status.
4. As the seller, create a listing under **My listings**; it appears in the catalogue at once.

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

**Before presenting:** the botanical attributes in the seed data are an illustrative starting set. Check
them against a reliable source such as Flora of Pakistan.

## Project layout

`accounts` (users, login, profile) · `growprofiles` (regions, grow profiles) · `catalog` (species,
catalogue, seller listings) · `matching` (scoring in `services.py`, results page) · `orders` (cart, checkout,
orders, seller fulfilment). Shared templates are in `templates/`, shared helpers in `basera/forms.py` and
`basera/htmx.py`. Every view's docstring names its user story. No automated tests were written, as the spec
asks; every story was checked by running it.
