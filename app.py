import os
import psycopg2 # Replaces 'sqlite3'
from psycopg2.extras import RealDictCursor # Used to get dictionaries from queries
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# --- Database Setup ---

# Get the database URL from an environment variable first,
# or fall back to your hardcoded string.
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://myai_postgres_app_user:GSKtcpO4zpcVxSaA2JVn2cd2c9zOsQdi@dpg-d49685hr0fns738dhtd0-a.oregon-postgres.render.com/myai_postgres_app'
)

app = Flask(__name__)
CORS(app)

# --- Database Connection Functions (Updated for PostgreSQL) ---

def get_db():
    """Opens a new database connection if one doesn't exist in the context."""
    if 'db' not in g:
        # Connect to the PostgreSQL database
        g.db = psycopg2.connect(DATABASE_URL)
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initializes the database and creates the 'posts' table
    with the correct PostgreSQL schema.
    """
    print("Initializing database...")
    # Connect using the new connection string
    conn = psycopg2.connect(DATABASE_URL) 
    c = conn.cursor()
    
    # --- THIS IS THE CORRECTED TABLE SCHEMA FOR POSTGRESQL ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    ''')
    # Key changes:
    # 1. 'INTEGER PRIMARY KEY AUTOINCREMENT' -> 'SERIAL PRIMARY KEY'
    # 2. 'DEFAULT CURRENT_TIMESTAMP' -> 'DEFAULT NOW()'
    # --- END OF CORRECTION ---
    
    conn.commit()
    c.close()
    conn.close()
    print("Database initialized successfully.")

# --- API Routes (Updated for PostgreSQL) ---

@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Fetches all blog posts from the database."""
    db = get_db()
    
    # Use RealDictCursor to get results as dictionaries
    cur = db.cursor(cursor_factory=RealDictCursor) 
    
    cur.execute(
        "SELECT id, title, content, created_at FROM posts ORDER BY created_at DESC"
    )
    # fetchall() now returns a list of dictionaries directly
    posts = cur.fetchall() 
    cur.close()
    
    return jsonify(posts), 200

@app.route("/api/posts", methods=["POST"])
def add_post():
    """Adds a new blog post to the database."""
    data = request.get_json() or {}
    
    if 'title' not in data or 'content' not in data:
        return jsonify({"error": "Missing title or content"}), 400

    title = data['title']
    content = data['content']

    db = get_db()
    cur = db.cursor()
    
    # PostgreSQL uses '%s' as placeholders, not '?'
    cur.execute(
        "INSERT INTO posts (title, content) VALUES (%s, %s)",
        (title, content)
    )
    
    db.commit() # Commit the transaction
    cur.close()
    
    return jsonify({"message": "Post created successfully"}), 201

# --- Main entry point to run the app ---

if __name__ == '__main__':
    # Run the init_db function once when the server starts
    init_db() 
    
    # Start the Flask server
    app.run(debug=True, port=5000)