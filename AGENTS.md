# Repository Guidelines

## Project Structure & Module Organization
- `run.py` boots the app and initializes `blog.db` if missing.
- `wsgi.py` is the production WSGI entry point.
- `app/` contains the Flask application factory, blueprints (auth, blog, admin), models, forms, and extensions.
- `templates/` contains Jinja2 HTML templates (base layout + page templates + error pages).
- `static/` holds assets (e.g., `static/blog11.jpeg`).
- `blog.db` is a local SQLite database (do not commit).
- `Dockerfile`, `docker-compose.yml`, and `Procfile` provide deployment configs.
- `.env.example` documents required environment variables.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `python run.py` starts the dev server on `http://127.0.0.1:5000`.
- `flask init-db` (with `FLASK_APP=wsgi.py`) creates tables.
- `python create_admin.py --username admin --email admin@example.com --password "ChangeMe123"` creates an admin user.
- Production: `gunicorn --bind 0.0.0.0:8000 wsgi:app` or PythonAnywhere WSGI config.

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes.
- Routes and templates: keep endpoint names aligned with template filenames (e.g., `post()` → `templates/post.html`).
- Use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`.
- Prefer explicit imports at top; avoid adding global state unless necessary.

## Testing Guidelines
- No test suite is present. If adding tests, consider `pytest` and place files under `tests/` using `test_*.py` naming.

## Commit & Pull Request Guidelines
- Commit history uses short Chinese summaries (e.g., "修订4", "安全加固、功能完善与部署准备"). Follow that style.
- PRs should describe user-visible changes, list any new dependencies, and include screenshots for template/UI updates.

## Security & Configuration Tips
- Use a `.env` file to set `SECRET_KEY` for local runs (see `.env.example`).
- Production requires `FLASK_ENV=production` and a non-default `SECRET_KEY`.
- Markdown output is sanitized via `bleach` before rendering with `| safe`.
- Login redirect (`next` param) is validated to prevent open redirects.
- Avoid committing credentials or `blog.db` snapshots.
