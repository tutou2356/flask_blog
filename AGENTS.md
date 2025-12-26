# Repository Guidelines

## Project Structure & Module Organization
- `run.py` boots the app and initializes `blog.db` if missing.
- `legacy/migrate_db.py` is deprecated (migrations now use Flask-Migrate).
- `templates/` contains Jinja2 HTML templates.
- `static/` holds assets (e.g., `static/blog11.jpeg`).
- `blog.db` is a local SQLite database (do not commit regenerated copies).

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `python run.py` starts the dev server on `http://127.0.0.1:5000`.
- `flask init-db` (with `FLASK_APP=wsgi.py`) creates tables.
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
