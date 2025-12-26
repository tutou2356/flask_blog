from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

CATEGORY_CHOICES = [
    ('', '选择分类'),
    ('技术', '技术'),
    ('生活', '生活'),
    ('随笔', '随笔'),
    ('学习', '学习'),
]


class PostCreateForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(max=100)])
    category = SelectField('分类', choices=CATEGORY_CHOICES, validators=[Optional()])
    tags = HiddenField('标签', validators=[Optional(), Length(max=255)])
    content = TextAreaField('内容', validators=[DataRequired()])


class PostEditForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(max=100)])
    category = SelectField('分类', choices=CATEGORY_CHOICES, validators=[Optional()])
    tags = StringField('标签', validators=[Optional(), Length(max=255)])
    content = TextAreaField('内容', validators=[DataRequired()])


class CommentForm(FlaskForm):
    name = StringField('昵称', validators=[Optional(), Length(max=80)])
    email = StringField('邮箱', validators=[Optional(), Email(), Length(max=120)])
    content = TextAreaField('内容', validators=[DataRequired()])


class DeletePostForm(FlaskForm):
    submit = SubmitField('删除')


class DeleteCommentForm(FlaskForm):
    submit = SubmitField('删除')
