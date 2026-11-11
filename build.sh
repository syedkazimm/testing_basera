#!/usr/bin/env bash
# Deployment build script (run by Render on every deploy).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_demo
