FROM python:3.11-slim

WORKDIR /app

# Copy dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Default command can be bash, you can override it when running
ENTRYPOINT ["python", "cli.py"]
