import os


def _default_db_uri(project_root: str) -> str:
    return 'sqlite:///' + os.path.join(project_root, 'blog.db')


class BaseConfig:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', _default_db_uri(PROJECT_ROOT))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    BLOG_IMAGE_UPLOAD_SUBDIR = os.getenv('BLOG_IMAGE_UPLOAD_SUBDIR', 'uploads/posts')
    BLOG_IMAGE_ALLOWED_EXTENSIONS = ('png', 'jpg', 'jpeg', 'gif', 'webp')
    BLOG_IMAGE_MAX_BYTES = int(os.getenv('BLOG_IMAGE_MAX_BYTES', 5 * 1024 * 1024))


class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
