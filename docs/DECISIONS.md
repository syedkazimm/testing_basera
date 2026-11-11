# Decisions where the spec was silent

Each entry records a judgement call made while building Basera.

## EN-01
- **Repo root:** `manage.py` and the `basera/` project package live directly in the repository root (the folder that holds `SPEC.md`), rather than in a nested `basera/` folder.
- **Spec file name:** the spec is committed as `spec.md` (the name it was supplied with).
- **App templates:** each app keeps its templates in `<app>/templates/<app>/`; the project-level `templates/` folder holds only shared pages (`base.html`, navbar, home, error pages).
- **Python version:** developed on Python 3.12 in a local `.venv` (git-ignored). Dependencies are pinned in `requirements.txt`.
- **Static assets:** Bootstrap 5.3.3 from jsDelivr and HTMX 2.0.4 from unpkg, both pinned.
- **Home buttons:** the two home buttons are placeholders until the catalogue and grow profile pages exist; they are wired in later stories.
