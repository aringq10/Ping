window.addEventListener("DOMContentLoaded", () => {
    var socket = io();

    // toggle between chat and settings
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
    const username = document.getElementById("username").value;
    // scroll chat to bottoms
    messages.scrollIntoView({ block: 'end' })

    // settings tab
    const leave_form = document.getElementById("leave");
    const add_user_form = document.getElementById("add_user");
    const change_chat_name = document.getElementById("change_chat_name");
    const user_id = document.getElementById("user_id");
    const chat_name = document.getElementById("chat_name");

    // Send message
    form.addEventListener("submit", e => {
        const message = input.value;

        if (message) {
            socket.emit('custom_message', { message: message, chat: window.location.pathname })
            input.value = '';
        }
        e.preventDefault()
    });

    // Receive messages
    socket.addEventListener("custom_response", data => {
        let divClass, serverVar;
        switch (data.username) {
            case username:
                divClass = 'message right';
                break;
            case 'Server':
                divClass = 'message middle';
                serverVar = 'server';
                break;
            default:
                divClass = 'message left';
        }

        messages.innerHTML += `<div class='${divClass}'>
                                    <div class="messageBox ${serverVar}">
                                        <b>${data.username}</b>: ${data.message}
                                    </div>
                                </div>`;
        // scroll chat to bottom
        messages.scrollIntoView({ block: 'end' })
    });

    // Error events
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
    socket.addEventListener("reload", () => {
        location.reload();
    });

    // Leave chat
    leave_form.addEventListener("submit", e => {
        socket.emit('leave_chat', { chat: window.location.pathname })
        window.location.href = '/';
        e.preventDefault();
    });

    // Add new user to chat
    add_user_form.addEventListener("submit", e => {
        socket.emit('add_user', { user_id: user_id.value, chat: window.location.pathname })
        e.preventDefault();
    });

    // Change chat name
    change_chat_name.addEventListener("submit", e => {
        socket.emit('change_chat_name', { new_name: chat_name.value, chat: window.location.pathname });
        e.preventDefault();
    });
});