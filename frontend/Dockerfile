# Use an official Python runtime as a base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django project code into the container
COPY . /app/

# Expose the port Django will run on
EXPOSE 8000


ARG DJANGO_ENV=dev
ENV DJANGO_ENV=${DJANGO_ENV}


CMD if [ "$DJANGO_ENV" = "prod" ]; then \
        exec gunicorn django_web.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - ; \
    else \
        exec python manage.py runserver 0.0.0.0:8000 ; \
    fi

