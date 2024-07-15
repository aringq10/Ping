#!/usr/bin/env python

import datetime
import json
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_socketio import SocketIO, send, emit

from helpers import login_required, init_db, format_date

# Configure app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=30)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# VIEW ROUTES
@app.route("/")
@login_required
def index():
    # Display all chats
    chats_processed = []

    with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute('''SELECT id, name FROM chats 
                        WHERE id IN
                        (SELECT chat_id FROM members WHERE user_id = ?)''', 
                        (session["user_id"],))
            chats = db.fetchall()
            
            for chat in chats:
                db.execute('''SELECT username FROM users 
                            WHERE id IN
                            (SELECT user_id FROM members WHERE chat_id = ?)''', 
                            (chat[0],))
                members = db.fetchall()
                chats_processed.append({
                    "id": chat[0],
                    "name": chat[1],
                    "members": members
                })

    # Render home page
    return render_template("index.html", chats=chats_processed)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Log user in

    # Forget any user_id
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    if request.method == "POST":
        # Ensure everything was submitted
        if not username or not password:
            print("Missing inputs")
            return render_template("form.html", 
                                    type="login", 
                                    error="Missing Inputs")

        # Query database for username
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT * FROM users WHERE username = ?", (username,))
            rows = db.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], password):
            print("invalid username")
            return render_template("form.html", 
                                    type="login", 
                                    error="Invalid Username or Password")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("form.html", type="login")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Register user
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if request.method == "POST":
        # Ensure everything was submitted
        if not username or not password or not confirmation:
            return render_template("form.html", 
                                    type="register", 
                                    error="Missing Inputs")

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("form.html", 
                                    type="register", 
                                    error="Passwords Don't Match")

        # Try to insert the new user
        try:
            with sqlite3.connect("app.db") as conn:
                db = conn.cursor()
                db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", 
                           (username, generate_password_hash(password)))
                conn.commit()
        except sqlite3.IntegrityError:
            # If username isn't available
            return render_template("form.html", 
                                    type="register", 
                                    error="Username Already Taken")

        # Redirect user to login page
        return redirect("/login")

    else:
        return render_template("form.html", type="register")

@app.route("/logout")
def logout():
    # Log user out

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/<int:chat_id>")
@login_required
def chat(chat_id):
    with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            # Check if access to chat is authorized
            db.execute("SELECT user_id FROM members WHERE chat_id = ?", 
                        (chat_id,))
            raw = db.fetchall()
            members = []
            for member in raw:
                members.append(member[0])
            if len(members) == 0 or session["user_id"] not in members:
                return "Unauthorized!"
            
            # Pass username to html
            db.execute("SELECT username FROM users WHERE id = ?", 
                        (session["user_id"],))
            username = db.fetchall()[0][0]

            # Get all chat messages
            db.execute('''SELECT datetime, username, message FROM messages 
                        WHERE chat_id = ? LIMIT 100''', 
                        (chat_id,))
            raw_messages = db.fetchall()
            messages = []
            # Format the datetime
            for message in raw_messages:
                messages.append([f"{datetime.datetime.fromisoformat(message[0])}",
                                message[1],
                                message[2]])
    
    return render_template("chat.html", 
                            username=username, 
                            messages=messages)

@app.route("/new_chat", methods=["GET", "POST"])
@login_required
def new_chat():
    if request.method == "POST":
        chat_name = request.form.get("name")

        # Ensure everything is submitted
        if not chat_name:
            return render_template("form.html", 
                                    type="new_chat", 
                                    error="Missing Inputs")

        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            # Check if the chat name is available
            db.execute("SELECT * FROM chats WHERE name = ?", (chat_name,))
            chats = db.fetchall()
            if len(chats) != 0:
                return render_template("form.html", 
                                        type="new_chat", 
                                        error="Chat Name Is Already Taken")
                                        
            # Create new chat and add the creator as a member
            db.execute("INSERT INTO chats(name) VALUES(?)", (chat_name,))
            db.execute("SELECT id FROM chats WHERE name = ?", (chat_name,))
            chat_id = db.fetchall()[0][0]
            db.execute("SELECT username FROM users WHERE id = ?", 
                        (session["user_id"],))
            username = db.fetchall()[0][0]
            db.execute("INSERT INTO members(chat_id, user_id) VALUES(?, ?)",
                        (chat_id, session["user_id"]))
            date = format_date(datetime.datetime.now())
            db.execute('''INSERT INTO messages(chat_id, username, message, datetime) 
                        VALUES(?, ?, ?, ?)''', 
                        (chat_id, "Server", 
                        f"{username} created the group chat {chat_name}", date))

        return redirect("/")
    else:
        return render_template("form.html", type="new_chat")

@app.route("/settings")
@login_required
def user_settings():
    with sqlite3.connect("app.db") as conn:
        db = conn.cursor()
        db.execute("SELECT username FROM users WHERE id = ?", 
                    (session["user_id"],))
        username = db.fetchall()[0][0]
    return render_template("user_settings.html", username=username)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT hash FROM users WHERE id = ?", 
                        (session["user_id"],))
            actual_hash = db.fetchall()[0][0]
        
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # Ensure everything was submitted
        if not old_password or not new_password or not confirmation:
            return render_template("form.html", 
                                    type="change_password", 
                                    error="Missing Inputs")
        
        # Ensure correct password
        if not check_password_hash(actual_hash, old_password):
            return render_template("form.html", 
                                    type="change_password", 
                                    error="Incorrect Password")
        
        #Ensure new passwords match
        if new_password != confirmation:
            return render_template("form.html", 
                                    type="change_password", 
                                    error="New Passwords Don't Match")

        # Change password
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("UPDATE users SET hash = ? WHERE id = ?", 
                        (generate_password_hash(new_password), 
                        session["user_id"]))

        return redirect("/logout")

    else:
        return render_template("form.html", type="change_password")

@app.route("/change_username", methods=["GET", "POST"])
@login_required
def change_username():
    if request.method == "POST":
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT hash FROM users WHERE id = ?", (
                        session["user_id"],))
            actual_hash = db.fetchall()[0][0]

        new_username = request.form.get("new_username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure everything was submitted
        if not new_username or not password or not confirmation:
            return render_template("form.html", 
                                    type="change_username", 
                                    error="Missing Inputs")
        
        # Ensure correct password
        if not check_password_hash(actual_hash, password):
            return render_template("form.html", 
                                    type="change_username", 
                                    error="Incorrect Password")
        
        #Ensure new passwords match
        if password != confirmation:
            return render_template("form.html", 
                                    type="change_username", 
                                    error="Passwords Don't Match")

        # Ensure username doesn't already exist
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("SELECT * FROM users WHERE username = ?", 
                        (new_username,))
            usernames = db.fetchall()
            if len(usernames) != 0:
                return render_template("form.html", 
                                        type="change_username", 
                                        error="Username Already Taken")

        # Change username
        with sqlite3.connect("app.db") as conn:
            db = conn.cursor()
            db.execute("UPDATE users SET username = ? WHERE id = ?", 
                        (new_username, session["user_id"]))

        return redirect("/logout")
    else:
        return render_template("form.html", type="change_username")
    
# WEBSOCKET ROUTES
@socketio.on('custom_message')
@login_required
def handle_custom_message(data):
    # Check if the message isn't empty
    length = len(data["message"].replace(" ", ""))
    if length == 0:
        return

    chat_id = data["chat"].replace("/", "")

    # Add message to DB
    with sqlite3.connect("app.db") as conn:
        db = conn.cursor()
        db.execute("SELECT username FROM users WHERE id = ?", 
                    (session["user_id"],))
        username = db.fetchall()[0][0]
        data["username"] = username
        date = format_date(datetime.datetime.now())
        data["datetime"] = f"{datetime.datetime.fromisoformat(date)}"
        sql = (chat_id, username, data["message"], date)
        db.execute('''INSERT INTO messages
                    (chat_id, username, message, datetime) 
                    VALUES(?, ?, ?, ?)''', sql)

    # Send the message to everyone in the chat
    emit("custom_response", data, broadcast=True)

@socketio.on('leave_chat')
@login_required
def handle_leave_chat(data):

    chat_id = data["chat"].replace("/", "")

    with sqlite3.connect("app.db") as conn:
        db = conn.cursor()
        # Get username
        db.execute("SELECT username FROM users WHERE id = ?", 
                    (session["user_id"],))
        username = db.fetchall()[0][0]
        # Delete user from chat members
        db.execute("DELETE FROM members WHERE chat_id = ? AND user_id = ?", 
                    (chat_id, session["user_id"]))

        # Send message to chat saying that a user left
        date = format_date(datetime.datetime.now())
        db.execute('''INSERT INTO messages(chat_id, username, message, datetime) 
                    VALUES(?, ?, ?, ?)''', 
                    (chat_id, "Server", f"{username} left the chat", date))
        
        # Check if there are any members left
        db.execute("SELECT user_id FROM members WHERE chat_id = ?", (chat_id,))
        members = db.fetchall()
        if len(members) == 0:
            # Delete the chat and its messages
            db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))

    # Send the message to everyone in the chat
    emit("custom_response", 
        { 
            "username": "Server", 
            "message": f"{username} left the chat",
            "datetime": f"{datetime.datetime.fromisoformat(date)}"
        }, broadcast=True)

@socketio.on('add_user')
@login_required
def handle_add_user(data):
    # Ensure everything was submitted
    if not data["username"] or not data["chat"]:
        emit("custom_error_add", { "error": "Missing Inputs" })
        return

    username = data["username"]
    chat_id = data["chat"].replace("/", "")

    with sqlite3.connect("app.db") as conn:
        db = conn.cursor()
        # Check that user exists
        db.execute("SELECT id FROM users WHERE username = ?", (username,))
        users = db.fetchall()
        if len(users) != 1:
            emit("custom_error_add", { "error": "User Doesn't Exist" })
            return
        user_id = users[0][0]

        # Check if user is already in chat
        db.execute("SELECT * FROM members WHERE user_id = ? AND chat_id = ?", 
                    (user_id, chat_id))
        exists = db.fetchall()
        if len(exists) != 0:
            emit("custom_error_add", { "error": "User already in chat" })
            return
        
        # Add User to members table
        db.execute("INSERT INTO members(chat_id, user_id) VALUES(?, ?)", 
                    (chat_id, user_id))

        # Send message to chat that a member has joined
        date = format_date(datetime.datetime.now())
        db.execute('''INSERT INTO messages(chat_id, username, message, datetime) 
                    VALUES(?, ?, ?, ?)''', 
                    (chat_id, "Server", 
                    f"{username} joined the chat", date))
        emit("custom_response", 
            { 
                "username": "Server", 
                "message": f"{username} joined the chat",
                "datetime": f"{datetime.datetime.fromisoformat(date)}"
            }, broadcast=True)
        emit("reload")

@socketio.on('change_chat_name')
@login_required
def handle_change_chat_name(data):
    # Ensure everything was submitted
    if not data["new_name"] or not data["chat"]:
        emit("custom_error_change", { "error": "Missing Inputs" })
        return

    new_name = data["new_name"]
    chat_id = data["chat"].replace("/", "")

    with sqlite3.connect("app.db") as conn:
        db = conn.cursor()
        
        # Change chat name
        db.execute("UPDATE chats SET name = ? WHERE id = ?", 
                    (new_name, chat_id))
        # Check who changed the name
        db.execute("SELECT username FROM users WHERE id = ?", 
                    (session["user_id"],))
        username = db.fetchall()[0][0]

        # Send message to chat that the name was changed
        date = format_date(datetime.datetime.now())
        db.execute('''INSERT INTO messages(chat_id, username, message, datetime) 
                    VALUES(?, ?, ?, ?)''', 
                    (chat_id, "Server", 
                    f"{username} changed the chat name to {new_name}", date))
        emit("custom_response", 
            { 
                "username": "Server", 
                "message": f"{username} changed the chat name to {new_name}", 
                "datetime": f"{datetime.datetime.fromisoformat(date)}"
            }, broadcast=True)
        emit("reload")

if __name__ == '__main__':
    init_db()
    socketio.run(app, '0.0.0.0', 5000)