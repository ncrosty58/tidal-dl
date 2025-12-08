**Editor settings (.vscode)**

- Commit only shareable, project-level editor files from `.vscode/`.
- Safe files to include: `settings.json`, `extensions.json`, `launch.json`, `tasks.json` — but only if they do not contain secrets or absolute, machine-specific paths.
- Avoid committing personal editor state or credentials (window layout, caches, tokens).

Recommended `.gitignore` rules (already applied):
```
.vscode/*
!.vscode/settings.json
!.vscode/extensions.json
!.vscode/launch.json
!.vscode/tasks.json
```

Before committing `settings.json`:
- Replace absolute interpreter paths with `${workspaceFolder}`-based paths, or remove the key if users use different virtualenv locations.
- Remove any secrets or machine-specific references.
