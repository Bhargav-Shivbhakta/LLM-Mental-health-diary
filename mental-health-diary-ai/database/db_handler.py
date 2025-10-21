# database/db_handler.py
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "diary.db")

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS entries(
            date TEXT,
            entry TEXT,
            emotion TEXT,
            suggestion TEXT
        )""")
        con.commit()

def ensure_migrations():
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS runlog(
            timestamp TEXT,
            prompt_version TEXT,
            model TEXT,
            temperature REAL,
            max_tokens INTEGER,
            user_input TEXT,
            raw_request TEXT,
            raw_response TEXT
        )""")
        con.commit()

def insert_entry(date, entry, emotion, suggestion):
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO entries(date, entry, emotion, suggestion) VALUES(?,?,?,?)",
            (date, entry, emotion, suggestion)
        )
        con.commit()

def get_all_entries():
    with _conn() as con:
        cur = con.cursor()
        cur.execute("SELECT date, entry, emotion, suggestion FROM entries ORDER BY date ASC")
        return cur.fetchall()

def insert_runlog(timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response):
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO runlog(timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response)
            VALUES(?,?,?,?,?,?,?,?)
        """, (timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response))
        con.commit()

def get_all_runlogs():
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT timestamp, prompt_version, model, temperature, max_tokens, user_input, raw_request, raw_response
            FROM runlog ORDER BY timestamp DESC
        """)
        return cur.fetchall()
