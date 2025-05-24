import json
import base64
import sqlite3
from datetime import datetime

DB_FILE = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            name TEXT,
            content TEXT,
            files TEXT,
            timestamp TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def create_session(name, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (name, created_at) VALUES (?, ?)",
        (name, timestamp)
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_sessions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name FROM sessions ORDER BY created_at DESC")
    sessions = c.fetchall()
    conn.close()
    return sessions

def save_message(session_id, role, name, content, timestamp=None, files=None):
    files_json = None
    if files:
        # files: list of file-like objects (from Streamlit uploader)
        files_json = json.dumps([
            {
                "name": file.name,
                "mimetype": file.type,
                "data": base64.b64encode(file.getvalue()).decode("utf-8")
            }
            for file in files
        ])
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (session_id, role, name, content, files, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, role, name, content, files_json, timestamp)
    )
    conn.commit()
    conn.close()

def fetch_chat_history(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, name, content, files, timestamp FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "role": r, 
            "name": n, 
            "content": c, 
            "files": json.loads(f) if f else [], 
            "timestamp": t
        } 
        for r, n, c, f, t in rows
    ]