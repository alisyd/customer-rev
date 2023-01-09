from datetime import datetime
from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,BooleanField,TextAreaField,SubmitField
from wtforms.validators import DataRequired,Length,Email,EqualTo,ValidationError
from flask_bootstrap import Bootstrap
from flask_bcrypt import Bcrypt
from flask_login import LoginManager,UserMixin, login_user, current_user,logout_user,login_required


app = Flask(__name__)
app.config['SECRET_KEY']="codename47"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///mydatabase.db'
db = SQLAlchemy(app)
bcrypt=Bcrypt(app)
login_manager=LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# all the database instances
class User(db.Model, UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True, nullable=False)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.String(60), nullable=False)
    reviews=db.relationship("Review",backref="author",lazy=True)

    def __repr__(self):
        return f"User('{self.username}','{self.email}','{self.image_file}')"

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"), nullable=False)
    upvotes=db.Column(db.Integer,default=0)
    downvotes=db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"Review('{self.product_name}','{self.date_posted}')"

# all the forms used in the app are put here

class RegisterationForm(FlaskForm):
    username=StringField("Username",validators=[DataRequired(message="This field is required"),Length(min=3,max=20,message=None)])
    email=StringField("Email",validators=[DataRequired(message="This is required"),Email(message="Enter a valid Email address")])
    password=PasswordField("Password",validators=[DataRequired(message="This field is required"),Length(min=3,max=20,message=None)])
    confirm_password=PasswordField("Confirm Password",validators=[DataRequired(message="This field is required"),Length(min=3,max=20,message=None),EqualTo("password")])
    submit=SubmitField("Sign Up")

    def validate_username(self,username):
        user=User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Sorry, that username is already taken")
    
    def validate_email(self,email):
        user=User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Sorry, that email is already taken")


class LoginForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(message="This is required"),Email(message="Enter a valid Email addresss")])
    password=PasswordField("Password",validators=[DataRequired(message="This field is required"),Length(min=3,max=20,message=None)])
    remember=BooleanField("Remember me")
    submit=SubmitField("Sign In")


class ReviewForm(FlaskForm):
    title=StringField("Title",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    product_name=StringField("Product Name",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    content=TextAreaField("Content",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    submit=SubmitField("Submit")


class EditForm(FlaskForm):
    title=StringField("Title",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    product_name=StringField("Product Name",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    content=TextAreaField("Content",validators=[DataRequired(message="This field is required"),Length(min=3,message=None)])
    submit=SubmitField("Save")

# all app routes

# for home page
@app.route('/')
def home():
    reviews=Review.query.order_by(Review.upvotes.desc())
    return render_template("index.html",reviews=reviews)
    #return "hello world"
#creating a new post
@app.route('/new_post', methods=["GET","POST"] )
@login_required
def new_post():
    post=ReviewForm()
    if post.validate_on_submit():
        review=Review(title=post.title.data,product_name=post.product_name.data, content=post.content.data, author=current_user)
        db.session.add(review)
        db.session.commit()        
        return redirect(url_for('view_posts'))
    return render_template('new_post.html',post=post)

#viewing the posts of current user
@app.route('/user_post', methods=["GET","POST"] )
@login_required
def view_posts():
    reviews=current_user.reviews
    return render_template("user_posts.html",reviews=reviews)  
# deleting a post 
@app.route('/user_posts/delete/<int:id>')
def delete(id):
    post=Review.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('view_posts'))

# editing a post
@app.route('/user_posts/edit/<int:id>', methods=["GET","POST"])
def edit(id):
    edit=EditForm()
    post=Review.query.get_or_404(id)
    if edit.validate_on_submit():
        post.title=edit.title.data
        post.product_name=edit.product_name.data
        post.content=edit.content.data
        db.session.commit()
        return redirect(url_for('view_posts'))
    else:
        edit.title.data=post.title
        edit.product_name.data=post.product_name
        edit.content.data=post.content
        return render_template("edit.html",post=post,edit=edit)

# upvote a post
@app.route('/home/upvotes/<int:id>',methods=["GET","POST"])
def upvote(id):
    post=Review.query.get_or_404(id)  
    upvotes=post.upvotes
    post.upvotes=upvotes+1
    db.session.commit()
    return redirect(url_for('home'))
# downvote a post
@app.route('/home/downvotes/<int:id>',methods=["GET","POST"])
def downvote(id):
    post=Review.query.get_or_404(id)
    downvotes=post.downvotes
    post.downvotes=downvotes+1
    db.session.commit()
    return redirect(url_for('home'))

# To register, login, user authentication, logout

@app.route('/register', methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form=RegisterationForm()
    if form.validate_on_submit():
        hashed_pw=bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user=User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return   redirect(url_for('login'))    
    return render_template("register.html" ,form=form)

@app.route('/login', methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for("home"))    
    return render_template("login.html" ,form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))





if __name__=="__main__":
    app.run(port=5000, debug = True)
