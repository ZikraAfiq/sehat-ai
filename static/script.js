const startScreen = document.getElementById("startScreen");
const startInput = document.getElementById("startInput");
const startBtn = document.getElementById("startBtn");

const chatBox = document.getElementById("chatBox");
const messages = document.getElementById("messages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

function insertPrompt(text) {
  if (!chatBox.classList.contains("hidden")) {
    userInput.value = text;
    userInput.focus();
  } else {
    startInput.value = text;
    startInput.focus();
  }
}

// Start chat
startBtn.onclick = () => startChat(startInput.value.trim());
startInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") startChat(startInput.value.trim());
});

function startChat(initialMessage) {
  if (!initialMessage) return;

  startScreen.classList.add("hidden");
  chatBox.classList.remove("hidden");

  addMessage(initialMessage, "user");
  setTimeout(() => {
    addMessage("Welcome! I'm Sehat.AI. How can I help you today?", "bot");
  }, 600);
}

// Chat send
sendBtn.onclick = () => sendMessage();
userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  addMessage(text, "user");

  setTimeout(() => {
    addMessage("This is a sample response from Sehat.AI.", "bot");
  }, 600);

  userInput.value = "";
}

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.textContent = text;
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}
