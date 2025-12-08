tidal-dl scripts
=================

This directory contains helper scripts for running `tidal-dl` in a systemd-managed environment.

tidal-dl-pipx-wrapper
----------------------

- Purpose: a small wrapper that prefers an already-installed `tidal-dl-ng` in the user's `~/.local/bin`, then checks PATH, and finally falls back to `pipx run`.
- Installation (system-wide):

```bash
sudo install -m 755 scripts/tidal-dl-pipx-wrapper /usr/local/bin/tidal-dl-pipx-wrapper
```

- After installing the wrapper, update your systemd unit to use the wrapper as the binary, for example:

```ini
[Service]
Environment=PATH=/home/nathan/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/local/bin/tidal-dl-pipx-wrapper dl <args>
EnvironmentFile=/etc/default/tidal-dl
```

Replace `/home/nathan` with the target user's home directory in the `PATH` entry in the unit file, or omit if you use the wrapper which prefers `$HOME/.local/bin`.

Configuration
-------------

You can provide a TOML configuration at `/etc/tidal-dl/config.toml` or as `config.toml` next to `app.py`. Example keys are in `config.example.toml`.

Secrets (tokens)
-----------------

For secrets (like `DOWNLOAD_TOKEN`), prefer using an `EnvironmentFile` referenced by the systemd unit (e.g. `/etc/default/tidal-dl`) rather than committing them to repo files.
