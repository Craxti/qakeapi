"""
QakeAPI JWT + SQLite Example.

Demonstrates:
- JWT authentication with SQLite database
- User registration and login
- Protected routes with @require_auth
- CRUD operations with SQLite
"""

import sqlite3
import secrets
import hashlib
from pathlib import Path

from qakeapi import (
    QakeAPI,
    CORSMiddleware,
    init_auth,
    require_auth,
    create_token,
)

app = QakeAPI(
    title="QakeAPI JWT + SQLite",
    version="1.3.1",
    description="JWT authentication with SQLite database",
    debug=True,
)
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# Initialize auth
SECRET_KEY = secrets.token_urlsafe(32)
init_auth(secret_key=SECRET_KEY, jwt_expiration=3600)

# SQLite database path
DB_PATH = Path(__file__).parent / "jwt_sqlite.db"


def get_db():
    """Get SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create users table if not exists."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


# Initialize DB on startup
init_db()


@app.post("/register")
async def register(request):
    """Register new user."""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email", "")

    if not username or not password:
        return {"error": "username and password required"}, 400

    conn = get_db()
    try:
        password_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"message": "User created", "user_id": user_id, "username": username}
    except sqlite3.IntegrityError:
        return {"error": "Username already exists"}, 409
    finally:
        conn.close()


@app.post("/login")
async def login(request):
    """Login and get JWT token."""
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "username and password required"}, 400

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, email FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return {"error": "Invalid credentials"}, 401

        token = create_token(
            {"user_id": row["id"], "username": row["username"]},
            expires_in=3600,
        )
        return {
            "message": "Login successful",
            "token": token,
            "user": {"id": row["id"], "username": row["username"], "email": row["email"]},
        }
    finally:
        conn.close()


@app.get("/users")
@require_auth()
def list_users(request, user: dict):
    """List all users (protected)."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, username, email, created_at FROM users").fetchall()
        return {"users": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/users/{id}")
@require_auth()
def get_user(id: int, request, user: dict):
    """Get user by ID (protected)."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (id,),
        ).fetchone()
        if not row:
            return {"error": "Not found"}, 404
        return dict(row)
    finally:
        conn.close()


@app.get("/me")
@require_auth()
def get_me(request, user: dict):
    """Get current user from JWT."""
    return {"user": user}


if __name__ == "__main__":
    import uvicorn
    print("JWT + SQLite API: http://127.0.0.1:8000")
    print("Docs: http://127.0.0.1:8000/docs")
    print("Register: POST /register {\"username\": \"test\", \"password\": \"test123\"}")
    print("Login: POST /login {\"username\": \"test\", \"password\": \"test123\"}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
