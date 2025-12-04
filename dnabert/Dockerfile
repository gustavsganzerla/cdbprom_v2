
FROM python:3.11-slim


ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt


EXPOSE 5000

CMD ["flask", "--app", "main", "run", "--host=0.0.0.0", "--reload"]
