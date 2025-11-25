window.addEventListener("DOMContentLoaded", () => {
    var socket = io();

    // toggle between chat and settings tab
    const settings_button = document.getElementById("chatSettings");
    const back_button = document.getElementById("back");
    const chat = document.getElementById("chat");
    const settings = document.getElementById("settings");

    settings_button.addEventListener("click", () => {
        chat.style.display = "none";
        settings.style.display = "flex";
    });
    back_button.addEventListener("click", () => {
        chat.style.display = "block";
        settings.style.display = "none";
    });

    // chatting
    const form = document.getElementById("chatbox");
    const input = document.getElementById("input");
    const messages = document.getElementById("messages");
    const my_username = document.getElementById("my_username").value;
    // scroll to the bottom of chat on page reload
    messages.scrollIntoView({ block: 'end' })

    // settings tab
    const leave_form = document.getElementById("leave");
    const add_user_form = document.getElementById("add_user");
    const change_chat_name = document.getElementById("change_chat_name");
    const username = document.getElementById("username");
    const chat_name = document.getElementById("chat_name");
    const chat_id = document.getElementById("config").dataset.chatId;
    const root_path = document.getElementById("config").dataset.rootPath;

    // Send message
    form.addEventListener("submit", e => {
        const message = input.value;

        if (message) {
            socket.emit('custom_message', 
                { message: message, chat: chat_id })
            input.value = '';
        }
        e.preventDefault()
    });

    // Receive messages
    socket.addEventListener("custom_response", data => {
        let divClass, serverVar;
        switch (data.username) {
            case my_username:
                divClass = 'right';
                break;
            case 'Server':
                divClass = 'middle';
                serverVar = 'server';
                break;
            default:
                divClass = 'left';
        }

        messages.innerHTML += `<div class='message'>
                                    <div class="messageWrapper">
                                        <div class="messageTime">
                                            <div>${data.datetime.slice(5, 10)}</div>
                                            <div>${data.datetime.slice(11, 16)}</div>
                                        </div>
                                        <div class="messageBoxWrapper ${divClass}">
                                            <div class="messageBox ${serverVar}">
                                                <b>${data.username}:</b>
                                                <br>
                                                <p>${data.message}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>`;
        // scroll to the bottom of chat
        messages.scrollIntoView({ block: 'end' })
    });

    // Error events for add_user and change_chat_name forms respectively
    socket.addEventListener("custom_error_add", data => {
        err = data.error;
        error = document.getElementById("error_add");
        error.innerHTML = err;
        error.style.display = "block";
    });
    socket.addEventListener("custom_error_change", data => {
        err = data.error;
        error = document.getElementById("error_change");
        error.innerHTML = err;
        error.style.display = "block";
    });
    // Page reload event after a new user has been added
    socket.addEventListener("reload", () => {
        location.reload();
    });

    // Leave chat
    leave_form.addEventListener("submit", e => {
        socket.emit('leave_chat', { chat: chat_id })
        window.location.href = root_path;
        e.preventDefault();
    });

    // Add new user to chat
    add_user_form.addEventListener("submit", e => {
        socket.emit('add_user', { username: username.value, chat: chat_id })
        e.preventDefault();
    });

    // Change chat name
    change_chat_name.addEventListener("submit", e => {
        socket.emit('change_chat_name', { new_name: chat_name.value, chat: chat_id });
        e.preventDefault();
    });
});
