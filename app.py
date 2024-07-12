#!/usr/bin/env python

import json
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Global chats variable
chats = []

app = Flask(__name__)
sock = Sock(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    '''
    Display all chats
    '''
    chats_processed = []
    
    with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT id, name FROM chats WHERE id IN(SELECT chat_id FROM members WHERE user_id = ?)", (session["user_id"],))
            chats = db.fetchall()
            
            for chat in chats:
                db.execute("SELECT username FROM users WHERE id IN(SELECT user_id FROM members WHERE chat_id = ?)", (chat[0],))
                members = db.fetchall()
                chats_processed.append({
                    "id": chat[0],
                    "name": chat[1],
                    "members": members
                })

    '''
    Create a WebSocket Connection
    '''

    # Render home page
    return render_template("index.html", chats=chats_processed)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    if request.method == "POST":
        # Ensure everything was submitted
        if not username or not password:
            print("Missing inputs")
            return render_template("login.html", error="Missing Inputs")

        # Query database for username
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT * FROM users WHERE username = ?", (username,))
            rows = db.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], password):
            print("invalid username")
            return render_template("login.html", error="Invalid Username or Password")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if request.method == "POST":
        # Ensure everything was submitted
        if not username or not password or not confirmation:
            return render_template("register.html", error="Missing Inputs")

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", error="Passwords Don't Match")

        # Try to insert the new user
        try:
            with sqlite3.connect("app.db") as conn:
                db = conn.cursor()
                db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", 
                           (username, generate_password_hash(password)))
                conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username Already Taken")

        # Redirect user to login page
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/chat")
def chat():
    return render_template("chat.html")
