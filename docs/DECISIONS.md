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
