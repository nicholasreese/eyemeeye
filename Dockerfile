FROM python:3.11-slim

WORKDIR /app

# Install prod dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (excluded files are in .dockerignore)
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY main.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "main:app"]
