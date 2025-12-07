# tidal-dl Web Service

A Flask-based web wrapper for [tidal-dl-ng](https://github.com/exislow/tidal-dl-ng) that provides a simple UI and streams download progress over Server-Sent Events (SSE).

This repository contains a minimal web UI and Flask service to start/stop `tidal-dl-ng` jobs and stream progress to web clients.

> **Important:** This project executes a local binary and can expose system resources if deployed publicly. Read the Security section before deploying.

## Prerequisites

### tidal-dl-ng (Required)

This service is a web wrapper around **[tidal-dl-ng](https://github.com/exislow/tidal-dl-ng)** - you must install it first:

```bash
# Install via pip
pip install tidal-dl-ng

# Or install from source
git clone https://github.com/exislow/tidal-dl-ng.git
cd tidal-dl-ng
pip install .
```

After installation, configure `tidal-dl-ng` with your Tidal credentials:

```bash
tidal-dl-ng login
```

Verify it works:

```bash
tidal-dl-ng dl "https://tidal.com/browse/track/12345678"
```

### Python 3.8+

Required for running the Flask web service.

## Features

- Web UI to paste Tidal URLs and start downloads
- Real-time streaming output via SSE
- Stop running downloads
- Optional token-based access control
- Docker support

## Quick start (local)

1. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables (examples):

```bash
export TIDAL_DL_BIN=tidal-dl-ng                        # path to tidal-dl binary (default: looks in PATH)
export TEMPLATE_FOLDER=/path/to/templates              # optional: Flask template folder (default: app directory)
export STATIC_FOLDER=/path/to/static                   # optional: Flask static folder (default: app directory)
export FLASK_HOST=0.0.0.0                              # optional: bind address (default: 0.0.0.0)
export FLASK_PORT=5050                                 # optional: port (default: 5050)
export DOWNLOAD_TIMEOUT=0                              # seconds, 0 = no timeout
export DOWNLOAD_TOKEN="your-strong-token-here"         # optional: require token on requests
```

3. Run the app (development):

```bash
python app.py
# By default the app runs on the host/port configured in the script; for production use a WSGI server.
```

4. Open the UI at `http://localhost:5050/tidal-dl/` (adjust host/port).

## Endpoints

- `GET /tidal-dl/` - UI page
- `POST /tidal-dl/download` - Start download (form field `url=`). If `DOWNLOAD_TOKEN` is set, include header `X-Download-Token: <token>`.
- `POST /tidal-dl/stop` - Stop running download.
- `GET /tidal-dl/stream` - SSE stream for live output.

## Deployment Options

### Option 1: Docker (Recommended)

**Note:** The Docker image does NOT include `tidal-dl-ng`. You must mount it from the host or install it in a custom image.

```bash
# Build the image
docker build -t tidal-dl-web .

# Run with tidal-dl-ng mounted from host
docker run -d \
  --name tidal-dl-web \
  -p 5050:5050 \
  -v /path/to/tidal-dl-ng:/usr/local/bin/tidal-dl-ng:ro \
  -v /path/to/downloads:/downloads \
  -e TIDAL_DL_BIN=/usr/local/bin/tidal-dl-ng \
  -e DOWNLOAD_TOKEN="your-secret-token" \
  tidal-dl-web
```

Or create a custom Dockerfile that includes `tidal-dl-ng`:

```dockerfile
FROM python:3.11-slim
RUN pip install tidal-dl-ng
# ... rest of setup
```

### Option 2: Systemd Service (Linux)

1. Install dependencies system-wide or in a virtual environment:

```bash
sudo mkdir -p /opt/tidal-dl-web
sudo cp -r . /opt/tidal-dl-web/
cd /opt/tidal-dl-web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn tidal-dl-ng
```

2. Create a systemd service file `/etc/systemd/system/tidal-dl-web.service`:

```ini
[Unit]
Description=Tidal-DL Web Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/tidal-dl-web
Environment="PATH=/opt/tidal-dl-web/venv/bin:/usr/local/bin:/usr/bin"
Environment="TIDAL_DL_BIN=tidal-dl-ng"
Environment="DOWNLOAD_TOKEN=your-secret-token"
Environment="FLASK_HOST=127.0.0.1"
Environment="FLASK_PORT=5050"
ExecStart=/opt/tidal-dl-web/venv/bin/gunicorn -w 1 -b 127.0.0.1:5050 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tidal-dl-web
sudo systemctl start tidal-dl-web
sudo systemctl status tidal-dl-web
```

### Option 3: Nginx Reverse Proxy

For HTTPS and public access, put the service behind Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name tidal.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /tidal-dl/ {
        proxy_pass http://127.0.0.1:5050/tidal-dl/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }
}
```

## Security

- **Do not** expose this service to the open internet without proper access controls. If `DOWNLOAD_TOKEN` is set, the server will require the token header — set a strong secret.
- Run the service behind a reverse proxy (Nginx) and a WSGI server (Gunicorn) for production.
- Run the `tidal-dl-ng` binary with a dedicated, unprivileged user and limit filesystem access.
- Validate inputs on any public-facing endpoint; the current UI is minimal and intended for trusted/internal use.

## Contributing

Feel free to open issues or PRs.

## License

MIT License - see LICENSE file.
