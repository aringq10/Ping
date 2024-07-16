# Ping
## Video Demo:  <URL HERE>
## Description:
**Ping** is a basic messenger app I've created as my final project for CS50x. It incorporates the fundamental features of a messenger app such as creating and logging in via an account, creating new chats, instant messaging etc.\
**Flask**, **SQLite** and **flask-socketio** were used to build this app.
## Setup:
To run **Ping** you need to have ```python```, ```pip``` and ```git``` installed on your computer.

Clone the remote git repository onto your computer and go into the new directory:
```
git clone https://github.com/aringq10/Ping.git
cd Ping
```
Create a virtual environment and activate it,
```
python -m venv venv
source venv/bin/activate
```
download the necessary dependancies,
```
pip install -r requirements.txt
```
and finally, run the project:
```
python app.py
```
The app should be running on all addresses(0.0.0.0) on port 5000 unless you changed the ```IP``` and/or ```PORT``` variables in the ```app.py``` file.
## About:
### /templates
This is a standard Flask app directory for all the html templates.

```layout.html``` - a generic layout that is extended through other templates.

```form.html``` - a dynamic template for all the forms used in this app.

```index.html``` - home page template.

```user_settings``` - template for the user settings tab found in the home page.

```chat.html``` - the actual chat UI and chat settings tab.

---

### /static
All of the static stylesheets and scripts are stored in this directory.

```styles.css```, ```home.css```, ```form.css```, ```chat.css``` - all correspond to their respective html template.

```chat.js``` - a script used solely in the ```chat.html``` template to add the ability to toggle between the chat UI and its settings. It also plays the role of communicating with the backend server using WebSockets to send out, receive, load chat messages and enable the user to leave, add a user or change the name of the chat.

---

### requirements.txt
A ```.txt``` file specifying the necessary dependancies for **Ping** to run.

---

### helpers.py
A python script including 3 helper functions that are used later on in the main ```app.py``` script:

```login_required``` - a decorator function that acts as a gateway for some app routes, allowing only a logged-in user to access that route.

```init_db``` - a function that creates(If not already present) an **SQLite** database and the required **users**, **chats**, **members** and **messages** tables.

```format_date``` - a function that takes a ```datetime``` object as an input and returns a formated datetime string e.g. "20240101T010101".

---

### app.py
This is the main script responsible for all of the backend functionality.

#### VIEW ROUTES
If the user provides invalid inputs in any of the forms, the corresponding error message appears beneath the form e.g. "Missing Inputs", "Username Already Taken" etc. 
##### /register
Returns a register form with 3 input fields: username, password and confirmation. 
##### /login
Returns a login form with 2 input fields: username and password.
##### /index
Returns an html template, which includes a list of all chats and their links that the user is a member of and a navigation bar with 3 paths: /user_settings, /logout, /new_chat.
##### /user_settings
Returns an html template, which includes the user's username, ID and the options to change their username and/or password.
##### /change_password
Returns a change_password form with 3 input fields: old_password, new_password and confirmation.
##### /change_username
Returns a change_username form with 3 input fields: new_username, password and confirmation.
##### /logout
Simply logs out a user and deletes their session cookie.
##### /new_chat
Returns a new_chat form with 1 input field: name.\
If the inputs are valid, a new chat with the new name is created.
##### /\<int:chat_id>
This is a dynamic route which returns a chat.html template of the chat with an ID of **chat_id**. If the user isn't a member of the chat, a "Unauthorized!" string is returned. If the user is authorized to access the chat, all of its messages are loaded into the UI.

#### WEBSOCKET ROUTES
##### handle_custom_message
This custom_message handler receives a message from a user, formats it and then broadcasts it to the rest of the connected users in the chat while also adding the message to the database.
##### handle_leave_chat
This function handles a leave_chat event by removing the user from the chat, broadcasting a "user left the chat" message to the chat and recording this message in the database.
##### handle_add_user
This function handles an add_user event by adding a user to the chat by the given username, broadcasting a "user joined the chat" message to the chat and recording this message in the database.
##### handle_change_chat_name
This function handles an change_chat_name event by changing the chat's name to the given new_name, broadcasting a "user changed the chat name to new_name" message to the chat and recording this message in the database.