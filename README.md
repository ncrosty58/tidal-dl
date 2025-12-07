# CosmosLab tidal-dl service

Small Flask-based wrapper that runs a local `tidal-dl` binary and streams its output over Server-Sent Events (SSE).

This repository contains a minimal UI and a tiny Flask service used to start/stop a `tidal-dl` job and stream progress to web clients.

Important: This project executes a local binary and can expose system resources if deployed publicly. Read the Security section before deploying.

## Features
- Start a download by POSTing a URL to `/tidal-dl/download` (UI available at `/tidal-dl/`).
- Stream live output via SSE at `/tidal-dl/stream`.
- Stop a running job via `/tidal-dl/stop`.
- Optional token-based access control via environment variable `DOWNLOAD_TOKEN`.

## Quick start (local)

1. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables (examples):

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

## Security

- **Do not** expose this service to the open internet without proper access controls. If `DOWNLOAD_TOKEN` is set, the server will require the token header — set a strong secret.
- Run the service behind a reverse proxy (Nginx) and a WSGI server (Gunicorn/Uvicorn) for production.
- Run the `tidal-dl` binary with a dedicated, unprivileged user and limit filesystem access.
- Validate inputs on any public-facing endpoint; the current UI is minimal and intended for trusted/internal use.

## Production suggestions

- Use Gunicorn or uWSGI with systemd to run the Flask app as a proper service.
- Place the app behind Nginx and enable TLS.
- Consider adding per-job isolation (job IDs, working directories), process quotas, and persistent logs.

## Contributing

Feel free to open issues or PRs. If you'd like me to help add job IDs, Docker, or CI, tell me and I can implement it.

## License

This repository does not include a license. Add a `LICENSE` file if you want to grant reuse rights publicly.
