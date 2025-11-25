from functools import wraps
from flask import request, redirect, session, url_for
import sqlite3

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("bp.login"))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    sqls = [
        '''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT NOT NULL UNIQUE, 
            hash TEXT NOT NULL)
        ''',
        '''
        CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL UNIQUE)
        ''',
        '''
        CREATE TABLE IF NOT EXISTS members(
            chat_id INTEGER, 
            user_id INTEGER, 
            FOREIGN KEY(chat_id) REFERENCES chats(id), 
            FOREIGN KEY(user_id) REFERENCES users(id))
        ''',
        '''
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER, 
            username TEXT NOT NULL, 
            message TEXT NOT NULL, 
            datetime TEXT NOT NULL,
            FOREIGN KEY(chat_id) REFERENCES chats(id), 
            FOREIGN KEY(username) REFERENCES users(username))
        '''
    ]
    with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            # Create necessary tables
            for sql in sqls:
                db.execute(sql)
    


def format_date(date):
    year = date.year
    month = date.month if date.month > 9 else f"0{date.month}"
    day = date.day if date.day > 9 else f"0{date.day}"
    hour = date.hour if date.hour > 9 else f"0{date.hour}"
    minute = date.minute if date.minute > 9 else f"0{date.minute}"
    second = date.second if date.second > 9 else f"0{date.second}"

    return f"{year}{month}{day}T{hour}{minute}{second}"
