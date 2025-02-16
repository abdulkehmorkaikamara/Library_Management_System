import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')

app.secret_key = 'Abkamara@2024'

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables (Users, Books, Borrowed)."""
    conn = get_db()
    cursor = conn.cursor()

    # Create the Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    ''')

    # Create the Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT,
            quantity INTEGER NOT NULL DEFAULT 1
        );
    ''')

    # Create the Borrowed table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            borrower_name TEXT NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            returned INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(book_id) REFERENCES books(id)
        );
    ''')

    conn.commit()
    conn.close()

# Decorator can be removed if your Flask version is older than 0.7;
# then just call init_db() manually in the __main__ block.

def before_first_request_func():
    init_db()

def is_logged_in():
    """Check if a librarian (user) is logged in."""
    return 'user_id' in session

def get_current_user():
    """Get the current user from the database based on session['user_id']."""
    if not is_logged_in():
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return user

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route('/')
def home():
    """
    Show all books to everyone (logged in or not).
    If the user is logged in, they can see extra action buttons 
    (Borrow, Edit, Delete). If not logged in, they only see the list.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()

    # We'll reuse a "home.html" or "dashboard.html"-like template, 
    # but it won't require login. 
    # If not logged in, disable action buttons in the template.
    return render_template('home.html', books=books, user=is_logged_in())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route to register a new user (librarian).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, hashed_password))
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.', 'danger')
        finally:
            conn.close()

    return render_template('login.html', register=True)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        quantity = request.form.get('quantity', type=int)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, genre, quantity)
            VALUES (?, ?, ?, ?)
        """, (title, author, genre, quantity))
        conn.commit()
        conn.close()

        flash('Book added successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        quantity = request.form.get('quantity', type=int)

        cursor.execute("""
            UPDATE books
            SET title = ?, author = ?, genre = ?, quantity = ?
            WHERE id = ?
        """, (title, author, genre, quantity, book_id))
        conn.commit()
        conn.close()

        flash('Book updated successfully!', 'success')
        return redirect(url_for('home'))
    else:
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        conn.close()

        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('home'))

        return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    flash('Book deleted.', 'info')
    return redirect(url_for('home'))

@app.route('/borrow_book/<int:book_id>', methods=['GET', 'POST'])
def borrow_book(book_id):
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        flash('Book not found.', 'danger')
        conn.close()
        return redirect(url_for('home'))

    if request.method == 'POST':
        borrower_name = request.form.get('borrower_name')
        borrow_date = request.form.get('borrow_date')
        due_date = request.form.get('due_date')

        cursor.execute("""
            INSERT INTO borrowed (book_id, borrower_name, borrow_date, due_date, returned)
            VALUES (?, ?, ?, ?, 0)
        """, (book_id, borrower_name, borrow_date, due_date))

        # Decrease the quantity by 1
        new_quantity = book['quantity'] - 1 if book['quantity'] > 0 else 0
        cursor.execute("""
            UPDATE books
            SET quantity = ?
            WHERE id = ?
        """, (new_quantity, book_id))

        conn.commit()
        conn.close()

        flash('Book borrowed successfully!', 'success')
        return redirect(url_for('home'))

    conn.close()
    return render_template('borrow_book.html', book=book)

@app.route('/borrowed_books')
def borrowed_books():
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id AS borrowed_id, bo.title, bo.author, bo.genre, 
               b.borrower_name, b.borrow_date, b.due_date, b.returned
        FROM borrowed b
        JOIN books bo ON b.book_id = bo.id
        ORDER BY b.id DESC
    """)
    borrowed_list = cursor.fetchall()
    conn.close()
    return render_template('borrowed_books.html', borrowed_list=borrowed_list)

@app.route('/return_book/<int:borrowed_id>', methods=['POST'])
def return_book(borrowed_id):
    if not is_logged_in():
        flash('Please log in first.', 'info')
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM borrowed WHERE id = ?", (borrowed_id,))
    record = cursor.fetchone()
    if not record:
        flash('Borrowed record not found.', 'danger')
        conn.close()
        return redirect(url_for('borrowed_books'))

    # Mark as returned
    cursor.execute("""
        UPDATE borrowed
        SET returned = 1
        WHERE id = ?
    """, (borrowed_id,))

    # Increase quantity by 1
    cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (record['book_id'],))
    conn.commit()
    conn.close()

    flash('Book returned successfully!', 'success')
    return redirect(url_for('borrowed_books'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()
        conn.close()
    return render_template('search.html', results=results, query=query)

if __name__ == '__main__':
    # If your Flask is older than 0.7, remove @app.before_first_request 
    # and call init_db() here manually:
    init_db()
    app.run(debug=True)
