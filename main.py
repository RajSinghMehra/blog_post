from datetime import date
from functools import wraps
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import os
from dotenv import load_dotenv



load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)


def admin_only(function):
    # This ensures that the original function's metadata is preserved.
    @wraps(function) 
    def decorator_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        
        #Otherwise continue with the function which is refering this decorator.
        return function(*args, **kwargs)
    return decorator_function


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI','sqlite:///posts.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    
    #creating many relationship with one (User Table).
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author:Mapped['User'] = relationship(back_populates='posts') 

    #Creating one relationship with many (comments inside Comment table)
    comments:Mapped[list['Comment']] = relationship(back_populates='parent_post')



class Comment(db.Model):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_body: Mapped[str] = mapped_column(String(250), nullable=False)
    
    # Get Author Post ID & Object.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    author: Mapped['User'] = relationship(back_populates='comments')

    # Get Parent Post ID & Object.
    parent_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('blog_posts.id'))
    parent_post: Mapped['BlogPost'] = relationship(back_populates='comments')



# TODO: Create a User table for all your registered users. 
class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id: Mapped[int] = mapped_column(Integer,primary_key=True)
        name: Mapped[str] = mapped_column(String,nullable=False)
        email: Mapped[str]= mapped_column(String,nullable=False,unique=True)
        password: Mapped[str]= mapped_column(String,nullable=False)

        #Creating one relationship with many (posts inside BlogPost table)
        posts:Mapped[list['BlogPost']] = relationship(back_populates='author')

        #Creating one relationship with many (comments inside Comment table)
        comments: Mapped[list['Comment']] = relationship(back_populates='author')


with app.app_context():
    db.create_all()



# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register',methods=['GET','POST'])
def register():
    register_form = RegisterForm()

    print('__________ validate __________',register_form.validate_on_submit())
    if register_form.validate_on_submit():
        print('__________ name __________',register_form.password.data)
        user_check = db.session.execute(db.select(User).where(User.email==register_form.email.data)).scalar()
        print('_______ User Already Exist? ________________', user_check)
        flash("User Already Exist!")
        if user_check:
            print('_______ User Already Exist! ________________')
            return redirect(url_for('register'))

        # hashing and salting the plaintext password.
        hash_password = generate_password_hash(password=register_form.password.data, method="pbkdf2:sha512",salt_length=16)
        new_user = User(
                            name = register_form.name.data,
                            email = register_form.email.data,
                            password = hash_password
                        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html",register_form=register_form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods=['GET','POST'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            print('__________ wrong email ____________',user)
            flash("Email does not exist!")
            return redirect(url_for('login'))
        
        if check_password_hash(user.password, password):
            print('__________ login success ____________')
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            print('__________ wrong password ____________')
            flash("Wrogn Password!")
            return redirect(url_for('login'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=['GET','POST'])
@login_required
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    print('______________ comment form Validate before _____________', comment_form.validate_on_submit())
    if comment_form.validate_on_submit():
        print('______________ comment form Validate afer _____________', comment_form.validate_on_submit())
        new_comment = Comment(
                                comment_body = comment_form.comment_body.data,
                                author = current_user,
                                parent_post = requested_post                        
                             )
        print('______________ comment_body _____________', new_comment.comment_body)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))
    return render_template("post.html", post=requested_post, form=comment_form)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    # if not current_user.id == 1:
        # return abort(403)
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
