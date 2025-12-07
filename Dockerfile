FROM python:3.11-slim

# Create app user
RUN useradd -m -d /home/appuser appuser || true

WORKDIR /app

# Install build deps then runtime deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5050

# Use the bundled app.py. For production consider using Gunicorn.
CMD ["python", "app.py"]
