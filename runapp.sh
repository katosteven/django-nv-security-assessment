#!/bin/bash
# Activate venv if present, then run Django dev server.
set -e
[ -d .venv ] && . .venv/bin/activate
export DEBUG="${DEBUG:-True}"
python manage.py collectstatic --noinput >/dev/null
exec python manage.py runserver "${1:-127.0.0.1:8000}"
