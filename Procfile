# Heroku Procfile for Send-Pakket Platform
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn sendpakket.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 4
worker: celery -A sendpakket worker -l info --concurrency=2
beat: celery -A sendpakket beat -l info