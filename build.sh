#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser automatically from environment variables
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --no-input || true
fi

# Automatically configure Site and Google SocialApp
python setup_socialapp.py