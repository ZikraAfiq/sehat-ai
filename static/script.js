// Section navigation (switch between Chat / Medications)
function showSection(section) {
  document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-button').forEach(btn => btn.classList.remove('active'));

  document.getElementById(`${section}-section`).classList.remove('hidden');
  document.getElementById(`${section}-btn`).classList.add('active');
}


// ---------------- Chat Demo ----------------
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
if (startBtn) {
  startBtn.onclick = () => startChat(startInput.value.trim());
}
if (startInput) {
  startInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") startChat(startInput.value.trim());
  });
}

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
if (sendBtn) {
  sendBtn.onclick = () => sendMessage();
}
if (userInput) {
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}

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

// ---------------- Appointment Modal ----------------
function openModal() {
  document.getElementById("appointment-modal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("appointment-modal").classList.add("hidden");
}

const appointmentForm = document.getElementById("appointment-popup-form");
if (appointmentForm) {
  appointmentForm.addEventListener("submit", function(e) {
    e.preventDefault();

    const date = document.getElementById("appointment-date").value;
    const time = document.getElementById("appointment-time").value;
    const reason = document.getElementById("reason").value;

    if (!date || !time) {
      showAppointmentNotification("⚠️ Please select both date and time");
      return;
    }

    // Simulated confirmation response
    showAppointmentNotification(`✅ Appointment set for ${date} at ${time}`);

    // Reset form and close modal
    this.reset();
    closeModal();
  });
}

function showAppointmentNotification(message) {
  const notif = document.getElementById("appointment-notification");
  const notifText = document.getElementById("appointment-notification-text");
  notifText.textContent = message;

  notif.classList.add("show");
  setTimeout(() => {
    notif.classList.remove("show");
  }, 3000); // disappears after 3s
}

// ---------------- Medication Tracker ----------------
let medications = [];

const medicationForm = document.getElementById("medication-form");
if (medicationForm) {
  medicationForm.addEventListener("submit", function(e) {
    e.preventDefault();

    const name = document.getElementById("medication-name").value;
    const dosage = document.getElementById("medication-dosage").value;
    const time = document.getElementById("medication-time").value;

    const newMed = { name, dosage, time };
    medications.push(newMed);

    displayMedications();
    addReminderLog(`💊 Reminder set: ${name} (${dosage}) at ${time}`);

    this.reset();
  });
}

function displayMedications() {
  const container = document.getElementById("medications-container");
  if (!container) return;

  if (medications.length === 0) {
    container.innerHTML = '<p class="text-center">No medications added yet.</p>';
    return;
  }

  container.innerHTML = '';
  medications.forEach((med, index) => {
    const medDiv = document.createElement("div");
    medDiv.className = "card mb-4";
    medDiv.innerHTML = `
      <div class="card-content flex justify-between items-center">
        <div>
          <h4 class="font-semibold">${med.name}</h4>
          <p><strong>Dosage:</strong> ${med.dosage}</p>
          <p><strong>Time:</strong> ${med.time}</p>
        </div>
        <button class="btn btn-destructive" onclick="removeMedication(${index})">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    `;
    container.appendChild(medDiv);
  });
}

function removeMedication(index) {
  const removed = medications.splice(index, 1)[0];
  displayMedications();
  addReminderLog(`❌ Removed reminder for ${removed.name}`);
}

function addReminderLog(message) {
  const log = document.getElementById("reminder-history");
  if (!log) return;

  const entry = document.createElement("p");
  entry.textContent = message;
  log.appendChild(entry);
}
