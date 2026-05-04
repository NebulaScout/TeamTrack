#!/bin/sh
set -e

python manage.py migrate --noinput --fake-initial || true
python manage.py collectstatic --no-input
python manage.py init_roles || true
python manage.py seed_all || true

exec gunicorn team_track.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120