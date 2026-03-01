#!/bin/bash
set -e

python backend/manage.py makemigrations users
python backend/manage.py makemigrations event
python backend/manage.py migrate
python backend/manage.py migrate django_celery_beat
python backend/manage.py collectstatic --noinput
python backend/manage.py runserver 0.0.0.0:8000
