from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bs4 import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sigma'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    books = Book.query.all()
    return render_template('dashboard.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        year = request.form['year']
        description = request.form['description']
        image = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
            else:
                flash('Nieprawidłowy format pliku! Dozwolone: PNG, JPG, JPEG, GIF', 'danger')
                return redirect(url_for('add_book'))

        book = Book(title=title, author=author, genre=genre, year=int(year), description=description, image=image)
        db.session.add(book)
        db.session.commit()
        flash('Dodano książkę!', 'success')
        return redirect(url_for('index'))
    return render_template('add_book.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form['genre']
        book.year = int(request.form['year'])
        book.description = request.form['description']

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                book.image = filename
            elif file.filename != '':
                flash('Nieprawidłowy format pliku! Dozwolone: PNG, JPG, JPEG, GIF', 'danger')
                return redirect(url_for('edit_book', id=id))

        db.session.commit()
        flash('Zaktualizowano książkę!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_book.html', book=book)

@app.route('/delete/<int:id>')
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    if book.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.image))
        except OSError:
            pass
    db.session.delete(book)
    db.session.commit()
    flash('Usunięto książkę!', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email istnieje!', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, name=name, lastname=lastname)
        db.session.add(user)
        db.session.commit()
        flash('Zarejestrowano!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Złe dane logowania', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | (Book.author.ilike(f'%{query}%'))
        ).all()
        return render_template('dashboard.html', books=books, query=query)
    return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)