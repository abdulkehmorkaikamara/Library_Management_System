import sqlite3
import os

# You can adjust this path as needed.
# For example, if you want to place this script in the same directory
# as "database.db," just keep it as 'database.db'.
DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect(DATABASE)
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


    # Create the Borrowed table (Tracks which user borrowed which book, and due date)
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
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
