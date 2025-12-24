# Repository Guidelines

## Project Structure & Module Organization
- `app_blog.py` hosts the Flask app, models, and routes.
- `run.py` boots the app and initializes `blog.db` if missing.
- `migrate_db.py` performs SQLite schema updates with backups.
- `templates/` contains Jinja2 HTML templates.
- `static/` holds assets (e.g., `static/blog11.jpeg`).
- `blog.db` is a local SQLite database (do not commit regenerated copies).

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `python run.py` starts the dev server on `http://127.0.0.1:5000`.
- `flask init-db` (with `FLASK_APP=app_blog.py`) creates tables.
- `python migrate_db.py` migrates an existing `blog.db` and writes a timestamped backup.
- `python create_admin.py --username admin --email admin@example.com --password "ChangeMe123"` creates an admin user.

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes.
- Routes and templates: keep endpoint names aligned with template filenames (e.g., `post()` → `templates/post.html`).
- Prefer explicit imports at top; avoid adding global state unless necessary.

## Testing Guidelines
- No test suite is present. If adding tests, consider `pytest` and place files under `tests/` using `test_*.py` naming.

## Commit & Pull Request Guidelines
- Commit history uses short Chinese summaries (e.g., “修订4”, “增加了访问记录和评论功能”). Follow that style unless the team agrees on a new convention.
- PRs should describe user-visible changes, list any new dependencies, and include screenshots for template/UI updates.

## Security & Configuration Tips
- Use a `.env` file to set `SECRET_KEY` for local runs.
- Avoid committing credentials or `blog.db` snapshots.
- Verify admin access by logging in at `/login` and opening `/create` or `/admin/visits`.
