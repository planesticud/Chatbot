// Obtener el token CSRF
function getCSRFToken() {
    const csrfToken = document.cookie.match(/csrftoken=([^;]*)/);
    return csrfToken ? csrfToken[1] : null;
}

// Función para crear y añadir un mensaje al chat
function appendMessage(content, sender) {
    const chatHistory = document.getElementById("chatHistory");

    const messageElement = document.createElement("div");
    messageElement.classList.add("chat-message", sender);
    messageElement.textContent = content;

    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight; // Desplazarse hacia abajo automáticamente
}

// Función para enviar el mensaje
function sendMessage() {
    const userInput = document.getElementById("userMessage");
    const message = userInput.value.trim();

    if (message === "") return; // No enviar mensajes vacíos

    // Añadir el mensaje del usuario al chat
    appendMessage(message, "user");

    // Preparar datos para enviar
    const data = { message: message };

    fetch("/api/send_message/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(data),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.response) {
                // Añadir la respuesta del bot al chat
                appendMessage(data.response, "bot");
            } else if (data.error) {
                // Manejar errores devueltos por el servidor
                appendMessage("Error: " + data.error, "bot");
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            appendMessage("Error al comunicarse con el servidor.", "bot");
        });

    userInput.value = ""; 
}

// Enviar mensaje al presionar Enter
document.getElementById("userMessage").addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});
