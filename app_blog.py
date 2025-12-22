import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime, timedelta
import markdown
from functools import wraps
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin123')

# 会话配置
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)

from datetime import datetime
from flask import request


# ---- 新增：访客与评论模型 ----
class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), default='GET')
    ip = db.Column(db.String(64))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<Visit {self.ip} {self.path}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_name = db.Column(db.String(80), nullable=False)
    author_email = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    ip = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.author_name} on {self.post_id}>'


# ---- ✅ 修复重点：初始化数据库表 ----
# 删除旧的 @app.before_first_request，改为直接执行
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"创建表时出错: {e}")

# 简单的评论限流（内存，进程内）
last_comment_time_by_ip = {}


# ---- 记录访客访问 ----
@app.before_request
def log_visit():
    try:
        # 跳过静态资源和管理登录提交等不必要记录
        path = request.path or '/'
        if any([
            path.startswith('/static'),
            path.startswith('/favicon'),
            # 如果是管理员登录的POST请求，通常不记录，避免日志杂乱
            path.startswith('/admin/login') and request.method == 'POST'
        ]):
            return

        # 获取真实 IP (PythonAnywhere 位于反向代理之后，必须用 HTTP_X_FORWARDED_FOR)
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        # 如果有多个代理IP，通常取第一个
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        ua = request.user_agent.string if request.user_agent else ''
        ref = request.referrer
        post_id = None

        # 如果是文章详情页，尝试解析 post_id
        if path.startswith('/post/'):
            try:
                # 假设 URL 结构是 /post/123...
                parts = path.split('/')
                # 找到 'post' 后面紧跟的那个数字
                if 'post' in parts:
                    idx = parts.index('post')
                    if idx + 1 < len(parts):
                        post_id = int(parts[idx + 1])
            except Exception:
                post_id = None

        v = Visit(path=path, method=request.method, ip=ip, user_agent=ua, referrer=ref, post_id=post_id)
        db.session.add(v)
        # 提交到数据库
        db.session.commit()
    except Exception as e:
        # 发生错误回滚，以免影响后续的主业务逻辑
        db.session.rollback()
        print(f"记录访问失败: {e}")
# IP锁定存储 (重启后清空)
failed_attempts = {}
locked_ips = {}

def is_ip_locked(ip):
    """检查IP是否被锁定"""
    if ip in locked_ips:
        if datetime.now() < locked_ips[ip]:
            return True
        else:
            # 锁定时间已过，清除记录
            del locked_ips[ip]
            if ip in failed_attempts:
                del failed_attempts[ip]
    return False

def record_failed_attempt(ip):
    """记录失败尝试"""
    if ip not in failed_attempts:
        failed_attempts[ip] = []
    
    # 清除1小时前的记录
    one_hour_ago = datetime.now() - timedelta(hours=1)
    failed_attempts[ip] = [attempt for attempt in failed_attempts[ip] if attempt > one_hour_ago]
    
    # 添加当前失败记录
    failed_attempts[ip].append(datetime.now())
    
    # 检查是否需要锁定
    if len(failed_attempts[ip]) >= 3:
        locked_ips[ip] = datetime.now() + timedelta(minutes=15)
        return True
    return False

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='未分类')
    tags = db.Column(db.Text, default='')

    def __repr__(self):
        return f'<Post {self.title}>'
    
    def get_tags_list(self):
        """返回标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    posts = Post.query
    
    if query:
        posts = posts.filter(
            or_(
                Post.title.contains(query),
                Post.content.contains(query),
                Post.tags.contains(query)
            )
        )
    
    if category:
        posts = posts.filter(Post.category == category)
    
    posts = posts.order_by(Post.id.desc()).all()
    
    return render_template('search.html', posts=posts, query=query, category=category)

@app.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    
    try:
        html_content = markdown.markdown(
            post.content,
            extensions=[
                'markdown.extensions.codehilite',
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables'
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True,
                    'noclasses': False
                }
            }
        )
    except Exception as e:
        print(f"Markdown错误: {e}")
        # 降级处理
        html_content = markdown.markdown(post.content)
    
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.asc()).all()
    return render_template('post.html', post=post, content_html=html_content, comments=comments)

@app.route('/post/<int:id>/comment', methods=['POST'])
def add_comment(id):
    post = Post.query.get_or_404(id)
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))

    # 简单限流：同一IP 30秒内只允许一次
    now = datetime.utcnow()
    last = last_comment_time_by_ip.get(ip)
    if last and (now - last).total_seconds() < 30:
        flash('评论过于频繁，请稍后再试。', 'error')
        return redirect(url_for('post', id=post.id))

    content = (request.form.get('content') or '').strip()
    if not content:
        flash('评论内容不能为空。', 'error')
        return redirect(url_for('post', id=post.id))

    if session.get('admin_logged_in'):
        author_name = '管理员'
        author_email = None
        is_admin = True
    else:
        author_name = (request.form.get('name') or '').strip()
        author_email = (request.form.get('email') or '').strip()
        is_admin = False
        if not author_name:
            flash('昵称不能为空。', 'error')
            return redirect(url_for('post', id=post.id))

    comment = Comment(
        post_id=post.id,
        author_name=author_name,
        author_email=author_email if not session.get('admin_logged_in') else None,
        content=content,
        is_admin=is_admin,
        ip=ip,
    )
    db.session.add(comment)
    db.session.commit()

    last_comment_time_by_ip[ip] = now

    flash('评论已发布！', 'success')
    return redirect(url_for('post', id=post.id) + '#comments')

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    post_id = c.post_id
    db.session.delete(c)
    db.session.commit()
    flash('评论已删除。', 'info')
    return redirect(url_for('post', id=post_id) + '#comments')

@app.route('/admin/visits')
@admin_required
def admin_visits():
    visits = Visit.query.order_by(Visit.id.desc()).limit(200).all()
    return render_template('visits.html', visits=visits)

@app.route('/create', methods=('GET', 'POST'))
@admin_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', '未分类')
        tags = request.form.get('tags', '')

        if not title:
            flash('Title is required!')
        else:
            new_post = Post(
                title=title, 
                content=content,
                category=category if category else '未分类',
                tags=tags
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
@admin_required
def edit(id):
    post = Post.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', '未分类')
        tags = request.form.get('tags', '')

        if not title:
            flash('Title is required!')
        else:
            post.title = title
            post.content = content
            post.category = category if category else '未分类'
            post.tags = tags
            db.session.commit()
            return redirect(url_for('post', id=post.id))

    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=('POST',))
@admin_required
def delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash(f'"{post.title}" was successfully deleted!')
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # 检查IP是否被锁定
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
    
    if is_ip_locked(client_ip):
        flash('IP已被锁定，请15分钟后再试', 'error')
        return render_template('admin_login.html'), 429
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        next_page = request.form.get('next', url_for('index'))
        
        if password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            session.permanent = True
            flash('登录成功！', 'success')
            return redirect(next_page)
        else:
            # 记录失败尝试
            is_locked = record_failed_attempt(client_ip)
            if is_locked:
                flash('登录失败次数过多，IP已被锁定15分钟', 'error')
            else:
                remaining = 3 - len(failed_attempts.get(client_ip, []))
                flash(f'密码错误，还有{remaining}次尝试机会', 'error')
    
    next_page = request.args.get('next', '')
    return render_template('admin_login.html', next=next_page)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('已成功登出', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
