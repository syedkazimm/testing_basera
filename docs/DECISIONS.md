# Decisions where the spec was silent

Each entry records a judgement call made while building Basera.

## EN-01
- **Repo root:** `manage.py` and the `basera/` project package live directly in the repository root (the folder that holds `SPEC.md`), rather than in a nested `basera/` folder.
- **Spec file name:** the spec is committed as `spec.md` (the name it was supplied with).
- **App templates:** each app keeps its templates in `<app>/templates/<app>/`; the project-level `templates/` folder holds only shared pages (`base.html`, navbar, home, error pages).
- **Python version:** developed on Python 3.12 in a local `.venv` (git-ignored). Dependencies are pinned in `requirements.txt`.
- **Static assets:** Bootstrap 5.3.3 from jsDelivr and HTMX 2.0.4 from unpkg, both pinned.
- **Home buttons:** the two home buttons are placeholders until the catalogue and grow profile pages exist; they are wired in later stories.

## US-01
- **Shared form helper:** `basera/forms.py` holds `BootstrapFormMixin` (adds Bootstrap CSS classes to widgets) and `templates/_form_fields.html` renders any form with inline errors. Every form in the project reuses them.
- **Phone validator:** `accounts/validators.py` holds the Pakistani phone regex so checkout can reuse it later.
- **Sign-up form:** first and last name are required on sign-up (the model allows blank so admin-created accounts need not have them). Role choices are only Customer and Seller; `is_staff` is not on the form.
- **Sign-up with HTMX:** the form is a partial; errors swap in place and success uses `HX-Redirect` to the login page.
- **Login link:** until US-02 adds the named `login` URL, templates link to `/accounts/login/` directly.

## US-02
- **Role landing pages:** customer goes to `/profiles/`, seller to `/seller/listings/`, admin to `/admin/`. The customer and seller pages are built in later stories, so those two paths show a 404 until their stories land (the seller page arrives in Sprint 2).
- **Login form:** the generic error text is "Incorrect email or password." for wrong password, unknown email and inactive accounts alike. Email is lower-cased before checking.
- **Logout:** a POST button in the navbar (Django 5's `LogoutView` rejects GET); it lands on home.
- **Logged-in visitors** who open the login or sign-up page are sent on (login → their landing page, sign-up → home).

## EN-02
- **Where things live:** `Region` and the shared choice lists (sunlight, soil, water, purpose, space type) are in `growprofiles/models.py`; `Species` and `SpeciesRegion` are in `catalog/models.py`. The seed command is `catalog/management/commands/seed_demo.py` and its data table is `catalog/seed_data.py`.
- **Sample grow profile deferred:** the `GrowProfile` model is built in US-06 (a story creates only the models it needs), so the seed command gains the demo customer's sample profile in that story.
- **Species count:** the spec's table has 35 rows; all 35 are seeded (4 flagged invasive).
- **Prices and stock:** derived deterministically from each species' position in the list (Rs 188 - 2,418; stock 5 - 50), so repeated runs give the same data.
- **Idempotent seeding:** a species is matched by seller + scientific name and only created if absent, so a seller's later edits are never overwritten. Regions are matched by name; accounts by email.
- **Demo password:** a single demo password (`Basera-demo-2026`) is used for all three demo accounts, printed only when an account is created. Setting the `DEMO_PASSWORD` environment variable overrides it, which production should do because `build.sh` runs the seed.
- **Demo admin:** `admin@basera.test` is a superuser; its `role` stays CUSTOMER (role is irrelevant for admins).
- **Naturalised plants:** Aloe vera and Marigold are kept, with a note in their ecological benefit that they are widely naturalised rather than strictly native (as the spec allows).
- **Species images:** seeded species have no uploaded image and show `static/img/placeholder.png` (a generated leaf graphic), which the spec allows ("images may be placeholders"). `static/img/species/` is left empty.
- **Admin:** species can be edited in the admin with regions as an inline; `is_invasive` is editable there (and nowhere else).
