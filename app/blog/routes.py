from datetime import datetime, timezone

import bleach
import markdown
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_

from . import blog_bp
from ..admin import admin_required
from ..extensions import db
from ..forms import CommentForm, DeleteCommentForm, DeletePostForm, PostCreateForm, PostEditForm
from ..models import Comment, Post


last_comment_time_by_ip = {}

BLEACH_ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr', 'blockquote', 'pre', 'code',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'a', 'img', 'strong', 'em', 'del', 'sup', 'sub',
    'span', 'div',
]
BLEACH_ALLOWED_ATTRS = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'td': ['align'], 'th': ['align'],
}


def _sanitize_html(raw_html: str) -> str:
    return bleach.clean(
        raw_html,
        tags=BLEACH_ALLOWED_TAGS,
        attributes=BLEACH_ALLOWED_ATTRS,
        strip=True,
    )


def _render_markdown(text: str) -> str:
    try:
        html_content = markdown.markdown(
            text,
            extensions=[
                'markdown.extensions.codehilite',
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True,
                    'noclasses': False,
                }
            },
        )
    except Exception:
        from flask import current_app
        current_app.logger.exception("Markdown 渲染异常")
        html_content = markdown.markdown(text)
    return _sanitize_html(html_content)


def _render_post_detail(post_item, comment_form=None, delete_post_form=None, delete_comment_form=None):
    html_content = _render_markdown(post_item.content)

    comments = (
        Comment.query.filter_by(post_id=post_item.id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return render_template(
        'post.html',
        post=post_item,
        content_html=html_content,
        comments=comments,
        comment_form=comment_form or CommentForm(),
        delete_post_form=delete_post_form or DeletePostForm(),
        delete_comment_form=delete_comment_form or DeleteCommentForm(),
    )


PER_PAGE = 10


@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    delete_post_form = DeletePostForm()
    return render_template('index.html', posts=pagination.items, pagination=pagination, delete_post_form=delete_post_form)


@blog_bp.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', '')

    posts = Post.query

    if query:
        posts = posts.filter(
            or_(
                Post.title.contains(query),
                Post.content.contains(query),
                Post.tags.contains(query),
            )
        )

    if category:
        posts = posts.filter(Post.category == category)

    page = request.args.get('page', 1, type=int)
    pagination = posts.order_by(Post.id.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)

    delete_post_form = DeletePostForm()
    return render_template(
        'search.html',
        posts=pagination.items,
        pagination=pagination,
        query=query,
        category=category,
        delete_post_form=delete_post_form,
    )


@blog_bp.route('/post/<int:id>')
def post(id):
    post_item = Post.query.get_or_404(id)
    return _render_post_detail(post_item)


@blog_bp.route('/post/<int:id>/comment', methods=['POST'])
def add_comment(id):
    post_item = Post.query.get_or_404(id)
    form = CommentForm()
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))

    now = datetime.now(timezone.utc)
    last = last_comment_time_by_ip.get(ip)
    if last and (now - last).total_seconds() < 30:
        form.content.errors.append('评论过于频繁，请稍后再试。')
        return _render_post_detail(post_item, comment_form=form)

    if not form.validate_on_submit():
        return _render_post_detail(post_item, comment_form=form)

    content = form.content.data.strip()

    if current_user.is_authenticated and current_user.role == 'admin':
        author_name = '管理员'
        author_email = None
        is_admin = True
    else:
        author_name = (form.name.data or '').strip()
        author_email = (form.email.data or '').strip()
        is_admin = False
        if not author_name:
            form.name.errors.append('昵称不能为空。')
            return _render_post_detail(post_item, comment_form=form)

    comment = Comment(
        post_id=post_item.id,
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
    return redirect(url_for('blog.post', id=post_item.id) + '#comments')


@blog_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    form = DeleteCommentForm()
    if not form.validate_on_submit():
        abort(400)

    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除。', 'info')
    return redirect(url_for('blog.post', id=post_id) + '#comments')


@blog_bp.route('/create', methods=('GET', 'POST'))
@admin_required
def create():
    form = PostCreateForm()
    if form.validate_on_submit():
        category = form.category.data or '未分类'
        new_post = Post(
            title=form.title.data.strip(),
            content=form.content.data,
            category=category,
            tags=form.tags.data or '',
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('blog.index'))

    return render_template('create.html', form=form)


@blog_bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@admin_required
def edit(id):
    post_item = Post.query.get_or_404(id)
    form = PostEditForm(obj=post_item)
    if form.validate_on_submit():
        post_item.title = form.title.data.strip()
        post_item.content = form.content.data
        post_item.category = form.category.data or '未分类'
        post_item.tags = form.tags.data or ''
        db.session.commit()
        return redirect(url_for('blog.post', id=post_item.id))

    return render_template('edit.html', post=post_item, form=form)


@blog_bp.route('/<int:id>/delete', methods=('POST',))
@admin_required
def delete(id):
    form = DeletePostForm()
    if not form.validate_on_submit():
        abort(400)

    post_item = Post.query.get_or_404(id)
    db.session.delete(post_item)
    db.session.commit()
    flash(f'"{post_item.title}" was successfully deleted!')
    return redirect(url_for('blog.index'))
