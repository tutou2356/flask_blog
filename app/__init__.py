import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError

from .config import DevConfig, ProdConfig
from .extensions import csrf, db, login_manager, migrate
from .models import User


def create_app():
    load_dotenv()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static'),
    )

    env = os.getenv('FLASK_ENV', 'development').lower()
    config_class = ProdConfig if env == 'production' else DevConfig
    app.config.from_object(config_class)
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(minutes=30))
    app.config.setdefault(
        'BLOG_IMAGE_UPLOAD_FOLDER',
        os.path.join(app.static_folder, app.config['BLOG_IMAGE_UPLOAD_SUBDIR']),
    )
    os.makedirs(app.config['BLOG_IMAGE_UPLOAD_FOLDER'], exist_ok=True)

    if env == 'production' and app.config.get('SECRET_KEY') in (None, '', 'dev'):
        raise RuntimeError(
            "生产环境必须通过环境变量设置安全的 SECRET_KEY，不能使用默认值 'dev'。"
        )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    from .blog import blog_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        return {'now': lambda: datetime.now(timezone.utc)}

    @app.cli.command('init-db')
    def init_db_command():
        with app.app_context():
            db.create_all()
        print('Initialized the database.')

    @app.before_request
    def log_visit():
        try:
            path = request.path or '/'
            if any([
                path.startswith('/static'),
                path.startswith('/favicon'),
            ]):
                return

            ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()

            ua = request.user_agent.string if request.user_agent else ''
            ref = request.referrer
            post_id = None

            if path.startswith('/post/'):
                try:
                    parts = path.split('/')
                    if 'post' in parts:
                        idx = parts.index('post')
                        if idx + 1 < len(parts):
                            post_id = int(parts[idx + 1])
                except Exception:
                    post_id = None

            from .models import Visit

            visit = Visit(path=path, method=request.method, ip=ip, user_agent=ua, referrer=ref, post_id=post_id)
            db.session.add(visit)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning("记录访问失败: %s", exc)

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("403 Forbidden: %s", error)
        message = getattr(error, 'description', None)
        return render_template('403.html', message=message), 403

    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning("400 Bad Request: %s", error)
        message = getattr(error, 'description', None)
        return render_template('400.html', message=message), 400

    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.info("404 Not Found: %s", error)
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("500 Internal Server Error: %s", error)
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_error):
        return render_template('400.html', message='CSRF 校验失败，请刷新页面后重试。'), 400

    return app
