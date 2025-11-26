#!/bin/bash
set -e

python manage.py makemigrations users
python manage.py makemigrations event
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
