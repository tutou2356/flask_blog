import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
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
            db.or_(
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
    
    return render_template('post.html', post=post, content_html=html_content)

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
