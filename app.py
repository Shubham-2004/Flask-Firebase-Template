from flask import Flask, redirect, render_template, request, session, url_for, flash
from datetime import timedelta
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Session cookie settings
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db_sql = SQLAlchemy(app)
mail = Mail(app)

# User Model
class User(db_sql.Model):
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    username = db_sql.Column(db_sql.String(80), unique=True, nullable=False)
    email = db_sql.Column(db_sql.String(120), unique=True, nullable=False)
    password_hash = db_sql.Column(db_sql.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Todo Model
class Todo(db_sql.Model):
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    user_id = db_sql.Column(db_sql.String(120), nullable=False)
    title = db_sql.Column(db_sql.String(200), nullable=False)
    completed = db_sql.Column(db_sql.Boolean, default=False)

    def __repr__(self):
        return f"<Todo {self.title}>"

# Create database tables
with app.app_context():
    db_sql.create_all()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Public Routes
@app.route('/')
def home():
    return render_template('home.html')  # Render home.html instead of redirecting

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db_sql.session.add(new_user)
        db_sql.session.commit()

        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.')
    return redirect(url_for('home'))

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    todos = Todo.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', todos=todos)

# Add Todo Route
@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    user_id = session['user_id']
    title = request.form.get('title')

    if not title:
        flash('Todo title cannot be empty.')
        return redirect(url_for('dashboard'))

    new_todo = Todo(user_id=user_id, title=title)
    db_sql.session.add(new_todo)
    db_sql.session.commit()

    try:
        user = User.query.get(user_id)
        send_email_notification(user.email, title)
    except Exception as e:
        print(f"Error sending email: {e}")

    flash('Todo added successfully!')
    return redirect(url_for('dashboard'))

# Toggle Todo Route
@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    user_id = session['user_id']
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        flash('Todo not found.')
        return redirect(url_for('dashboard'))

    todo.completed = not todo.completed
    db_sql.session.commit()
    flash('Todo updated successfully!')
    return redirect(url_for('dashboard'))

# Delete Todo Route
@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    user_id = session['user_id']
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        flash('Todo not found.')
        return redirect(url_for('dashboard'))

    db_sql.session.delete(todo)
    db_sql.session.commit()
    flash('Todo deleted successfully!')
    return redirect(url_for('dashboard'))

# Email Notification Function
def send_email_notification(user_email, todo_title):
    subject = "New Todo Created!"
    body = f"You have created a new todo: {todo_title}"

    try:
        msg = Message(subject, recipients=[user_email], body=body)
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Debug settings
mail.debug = True
app.logger.setLevel("DEBUG")

if __name__ == '__main__':
    app.run(debug=True)
