# 个人博客系统

一个基于 Flask 的现代化个人博客系统，支持 Markdown 写作、分类标签管理、全文搜索和深色模式。

**在线预览**: [tutou2356.pythonanywhere.com](https://tutou2356.pythonanywhere.com)

## 功能特性

- **Markdown 支持** - 完整的 Markdown 语法，代码高亮 (Pygments)，数学公式 (MathJax)
- **分类标签** - 灵活的文章分类和标签系统
- **全文搜索** - 支持标题、内容、标签搜索，带分页
- **深色模式** - 优雅的深色主题切换，状态本地持久化
- **响应式设计** - 适配桌面和移动设备，移动端搜索支持
- **评论系统** - 支持游客评论和管理员身份评论，频率限制
- **访问记录** - 管理员可查看访问日志
- **安全加固** - XSS 防护 (bleach)、CSRF 保护、开放重定向防御

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/tutou2356/flask_blog.git
cd flask_blog
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，设置 SECRET_KEY（开发环境可保持默认值）
```

### 3. 启动应用

```bash
python run.py
```

打开浏览器访问: http://127.0.0.1:5000

### 4. 创建管理员账号

```bash
python create_admin.py --username admin --email admin@example.com --password "YourPassword"
```

使用 `/login` 登录后，可在导航栏看到"写文章"和"访问记录"入口。

## 项目结构

```
flask_blog/
├── app/                  # 应用包
│   ├── __init__.py       # 应用工厂、错误处理、访问记录
│   ├── config.py         # 开发/生产配置
│   ├── extensions.py     # Flask 扩展实例
│   ├── models.py         # 数据模型 (Post, Comment, Visit, User)
│   ├── admin/            # 管理后台蓝图
│   ├── auth/             # 认证蓝图 (登录/注册/登出)
│   ├── blog/             # 博客蓝图 (文章CRUD/评论/搜索)
│   └── forms/            # WTForms 表单定义
├── templates/            # Jinja2 模板
├── static/               # 静态资源
├── migrations/           # Alembic 数据库迁移
├── run.py                # 开发启动脚本
├── wsgi.py               # 生产 WSGI 入口
├── create_admin.py       # 管理员创建工具
├── requirements.txt      # Python 依赖
├── Dockerfile            # Docker 镜像配置
├── docker-compose.yml    # Docker Compose 编排
├── Procfile              # Render/Railway 部署
└── .env.example          # 环境变量模板
```

## 部署

### PythonAnywhere

```bash
# 克隆代码
cd ~
git clone https://github.com/tutou2356/flask_blog.git
cd flask_blog

# 创建虚拟环境并安装依赖
mkvirtualenv flask_blog_env --python=python3.10
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
# 编辑 .env，填入生成的 SECRET_KEY，设置 FLASK_ENV=production

# 初始化数据库 + 创建管理员
export FLASK_APP=wsgi.py
flask init-db
python create_admin.py --username admin --email your@email.com --password "YourPassword"
```

Web 面板配置：
- **Source code**: `/home/你的用户名/flask_blog`
- **Virtualenv**: `/home/你的用户名/.virtualenvs/flask_blog_env`
- **Static files**: URL `/static` → `/home/你的用户名/flask_blog/static`
- **WSGI 文件**中写入：

```python
import sys, os
project_home = '/home/你的用户名/flask_blog'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))
from wsgi import app as application
```

### Docker

```bash
cp .env.example .env
# 编辑 .env 设置 SECRET_KEY 和 FLASK_ENV=production
docker compose up -d --build
```

### Render / Railway

推送代码到 GitHub 后连接仓库，平台会自动识别 `Procfile`，在环境变量中设置 `SECRET_KEY` 和 `FLASK_ENV=production` 即可。

## 数据库迁移

迁移目录已内置，无需重复 `flask db init`。

```bash
export FLASK_APP=wsgi.py

# 已有数据库标记基线
flask db stamp head

# 后续结构变更
flask db migrate -m "描述信息"
flask db upgrade
```

新库初始化：`flask db upgrade`

## 权限模型

- **角色**: `admin` (管理员) / `visitor` (普通用户)
- **策略**: 未登录 → 重定向到 `/login`；已登录但非 admin → 403
- **受保护路由**: `/create`、`/<id>/edit`、`/<id>/delete`、`/comment/<id>/delete`、`/admin/visits`
- **统一控制**: `@admin_required` 装饰器

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Flask 2.3 + SQLAlchemy + Flask-Login + Flask-WTF |
| 前端 | TailwindCSS 3.4 + Lucide Icons + highlight.js + MathJax |
| 数据库 | SQLite (可切换 PostgreSQL) |
| 安全 | bleach (XSS) + CSRFProtect + 开放重定向防御 |
| 部署 | Gunicorn / PythonAnywhere / Docker |

## 许可证

MIT License
