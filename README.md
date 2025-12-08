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

## Configuration

The application supports multiple configuration methods (in order of precedence):

1. **Environment variables** (highest precedence)
2. **System TOML file**: `/etc/tidal-dl/config.toml` 
3. **Local TOML file**: `config.toml` next to `app.py`
4. **Built-in defaults** (lowest precedence)

### TOML Configuration

Create `/etc/tidal-dl/config.toml` for system-wide deployment:

```toml
# System configuration for tidal-dl
template_folder = "/path/to/tidal-dl/templates"
static_folder = "/path/to/tidal-dl/static"
tidal_dl_bin = "/path/to/venv/bin/tidal-dl-ng"
download_timeout = 0
flask_host = "0.0.0.0"
flask_port = 5050
# Note: store secrets like download_token in /etc/default/tidal-dl instead
```

For secrets, create `/etc/default/tidal-dl` (restrict permissions):

```bash
# /etc/default/tidal-dl
DOWNLOAD_TOKEN="your-secret-token"
```

See `config.example.toml` for all available options.

### Environment Variables

Alternatively, configure via environment variables:

- `TIDAL_DL_BIN` - path to tidal-dl-ng binary
- `TEMPLATE_FOLDER` - Flask template folder path
- `STATIC_FOLDER` - Flask static folder path  
- `FLASK_HOST` - bind address (default: 0.0.0.0)
- `FLASK_PORT` - port (default: 5050)
- `DOWNLOAD_TIMEOUT` - seconds, 0 = no timeout
- `DOWNLOAD_TOKEN` - optional access token

## Features

- Web UI to paste Tidal URLs and start downloads
- Real-time streaming output via SSE
- Stop running downloads
- Optional token-based access control
- TOML and environment variable configuration
- Docker support

## Quick start (local)

1. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install tidal-dl-ng  # Install tidal-dl-ng in the venv
```

2. Configure the application:

**Option A: TOML config (recommended)**

Copy the example and edit:
```bash
cp config.example.toml config.toml
# Edit config.toml with your settings
# Add config.toml to .gitignore if using for development
```

**Option B: Environment variables**

```bash
export TIDAL_DL_BIN=venv/bin/tidal-dl-ng              # path to venv binary
export FLASK_HOST=0.0.0.0                              # bind address
export FLASK_PORT=5050                                 # port
export DOWNLOAD_TIMEOUT=0                              # seconds, 0 = no timeout
export DOWNLOAD_TOKEN="your-strong-token-here"         # optional access token
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

1. Install dependencies in a virtual environment:

```bash
sudo mkdir -p /opt/tidal-dl-web
sudo cp -r . /opt/tidal-dl-web/
cd /opt/tidal-dl-web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn tidal-dl-ng
```

2. Create system configuration:

```bash
# Create system config directory
sudo mkdir -p /etc/tidal-dl

# Create main config (edit paths as needed)
sudo tee /etc/tidal-dl/config.toml > /dev/null <<'EOF'
template_folder = "/opt/tidal-dl-web/templates"
static_folder = "/opt/tidal-dl-web/static"
tidal_dl_bin = "/opt/tidal-dl-web/venv/bin/tidal-dl-ng"
download_timeout = 0
flask_host = "127.0.0.1"
flask_port = 5050
EOF

# Create secrets file (restrict permissions)
sudo tee /etc/default/tidal-dl > /dev/null <<'EOF'
DOWNLOAD_TOKEN="your-secret-token"
EOF
sudo chmod 600 /etc/default/tidal-dl
```

3. Create a systemd service file `/etc/systemd/system/tidal-dl.service`:

```ini
[Unit]
Description=TIDAL-DL Web Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/tidal-dl-web
EnvironmentFile=/etc/default/tidal-dl
ExecStart=/opt/tidal-dl-web/venv/bin/gunicorn -w 1 -b 127.0.0.1:5050 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

4. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tidal-dl
sudo systemctl start tidal-dl
sudo systemctl status tidal-dl
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
