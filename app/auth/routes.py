from flask import flash, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user

from . import auth_bp
from ..extensions import db
from ..forms import LoginForm, RegisterForm
from ..models import User


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return redirect(url_for('auth.login', next=request.args.get('next', '')))


@auth_bp.route('/admin/logout')
def admin_logout():
    return redirect(url_for('auth.logout'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.strip(), email=form.email.data.strip())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        form.next.data = request.args.get('next', '')

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        next_page = form.next.data or url_for('blog.index')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            session.permanent = True
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(next_page)

        form.password.errors.append('用户名或密码错误')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('blog.index'))
