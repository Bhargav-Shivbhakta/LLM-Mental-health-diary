import sqlite3
from pathlib import Path

DB_PATH = Path("database/diary_entries.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            entry TEXT,
            emotion TEXT,
            suggestion TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_entry(date, entry, emotion, suggestion):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO entries (date, entry, emotion, suggestion)
        VALUES (?, ?, ?, ?)
    ''', (date, entry, emotion, suggestion))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT date, entry, emotion, suggestion FROM entries ORDER BY date DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows
