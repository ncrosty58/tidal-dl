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

# Document default env values (can be overridden at runtime)
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5050
ENV TIDAL_DL_BIN=tidal-dl-ng
ENV DOWNLOAD_TIMEOUT=0
ENV DOWNLOAD_TOKEN=

EXPOSE 5050

# Use the bundled app.py. For production consider using Gunicorn.
CMD ["python", "app.py"]
