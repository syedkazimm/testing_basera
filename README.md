# Basera

Basera helps people in Pakistan choose and buy **native plants** that suit their own growing conditions.
(Full README is completed in the final stories.)

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/. With no `DATABASE_URL` set, the app uses a local SQLite file.
