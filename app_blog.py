import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime, timedelta
import markdown
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

# 加载环境变量
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# 会话配置
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---- 登录与权限 ----
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        if current_user.role != 'admin':
            abort(403)
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

    if current_user.is_authenticated and current_user.role == 'admin':
        # 管理员评论
        author_name = '管理员'
        author_email = None
        is_admin = True
    else:
        # 匿名用户评论
        author_name = (request.form.get('name') or '').strip()
        author_email = (request.form.get('email') or '').strip()
        is_admin = False
        if not author_name:
            flash('昵称不能为空。', 'error')
            return redirect(url_for('post', id=post.id))

    comment = Comment(
        post_id=post.id,
        author_name=author_name,
        author_email=author_email,
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
    return redirect(url_for('login', next=request.args.get('next', '')))

@app.route('/admin/logout')
def admin_logout():
    return redirect(url_for('logout'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # 验证输入
        if not username or not email or not password:
            flash('所有字段都是必填的', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('用户名至少需要3个字符', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密码至少需要6个字符', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被使用', 'error')
            return render_template('register.html')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        next_page = request.form.get('next', url_for('index'))
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # 登录成功
            login_user(user)
            session.permanent = True
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(next_page)
        else:
            flash('用户名或密码错误', 'error')
    
    next_page = request.args.get('next', '')
    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('index'))


# ---- 模型定义 ----
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


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='visitor', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """设置密码（哈希存储）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# ---- 评论与访客 ----
last_comment_time_by_ip = {}


# ---- 记录访客访问 ----
@app.before_request
def log_visit():
    try:
        # 跳过静态资源和管理登录提交等不必要记录
        path = request.path or '/'
        if any([
            path.startswith('/static'),
            path.startswith('/favicon')
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


@app.errorhandler(403)
def forbidden(_error):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run(debug=True)
