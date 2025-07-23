import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# flash() 函数需要一个密钥
app.config['SECRET_KEY'] = 'dev'

db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'

@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

# --- 路由逻辑 ---

# 首页：展示所有文章
@app.route('/')
def index():
    # 从数据库查询所有文章，按ID倒序排列（最新的在前面）
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)

# 创建新文章的页面
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            # 创建新的Post对象并存入数据库
            new_post = Post(title=title, content=content)
            db.session.add(new_post)
            db.session.commit()
            # 操作完成后，重定向到首页
            return redirect(url_for('index'))

    return render_template('create.html')

# 删除文章的功能
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash(f'"{post.title}" was successfully deleted!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
