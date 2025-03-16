from flask import Flask, redirect, render_template, request, make_response, jsonify, url_for
from datetime import timedelta
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

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

# Public Routes
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    # Assuming a default user_id for simplicity
    user_id = "default_user"
    todos = Todo.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', todos=todos)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    # Assuming a default user_id for simplicity
    user_id = "default_user"
    title = request.form.get('title')

    if not title:
        return "Invalid todo", 400

    new_todo = Todo(user_id=user_id, title=title)
    db_sql.session.add(new_todo)
    db_sql.session.commit()

    try:
        send_email_notification("user@example.com", title)
    except Exception as e:
        print(f"Error sending email: {e}")

    return redirect(url_for('dashboard'))

@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    # Assuming a default user_id for simplicity
    user_id = "default_user"
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return "Todo not found", 404

    todo.completed = not todo.completed
    db_sql.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    # Assuming a default user_id for simplicity
    user_id = "default_user"
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return "Todo not found", 404

    db_sql.session.delete(todo)
    db_sql.session.commit()
    return redirect(url_for('dashboard'))

def send_email_notification(user_email, todo_title):
    subject = "New Todo Created!"
    body = f"You have created a new todo: {todo_title}"

    try:
        msg = Message(subject, recipients=[user_email], body=body)
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

mail.debug = True
app.logger.setLevel("DEBUG")

if __name__ == '__main__':
    app.run(debug=True)
