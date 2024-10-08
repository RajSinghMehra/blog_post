from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField(label='Name',validators=[DataRequired()])
    email = StringField(label='Email',validators=[DataRequired()])
    password = StringField(label='Password',validators=[DataRequired()])
    submit = SubmitField('Sign me up!')


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField(label='Email',validators=[DataRequired()])
    password = StringField(label='Password',validators=[DataRequired()])
    submit = SubmitField('Log me in!')
        


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment_body = CKEditorField('comment_body',validators=[DataRequired()])
    submit = SubmitField('Submit Comment')