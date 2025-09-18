// Enhanced Global variables
const API_BASE_URL = "http://localhost:5001/api"

// Function to make API requests with proper CORS handling
async function apiRequest(endpoint, method = "GET", data = null) {
  const config = {
    method: method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "include",
    mode: "cors",
  }

  if (data) {
    config.body = JSON.stringify(data)
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || "API request failed")
    }
    return await response.json()
  } catch (error) {
    console.error("API Error:", error)
    throw error
  }
}

let currentSection = "chat"
let doctors = []
let medications = []
const reminders = []
let isTyping = false

// API Helper Functions
async function fetchWithErrorHandling(endpoint, options = {}) {
  try {
    const method = options.method || "GET"
    const data = options.body ? JSON.parse(options.body) : null
    return await apiRequest(endpoint, method, data)
  } catch (error) {
    console.error(`API Error: ${error.message}`)
    throw error
  }
}

// Toggle loading state
function setLoading(loading) {
  const loadingIndicator = document.getElementById("loading-indicator")
  if (loadingIndicator && loading) {
    loadingIndicator.classList.remove("hidden")
  } else if (loadingIndicator) {
    loadingIndicator.classList.add("hidden")
  }
}

// Initialize the application
function init() {
  loadDoctors()
  loadMedications()
  loadReminders()
  setupEventListeners()
  showSection("chat")

  // Set minimum date for appointment to today
  const today = new Date().toISOString().split("T")[0]
  document.getElementById("appointment-date").min = today
}

// Section navigation
function showSection(section) {
  // Hide all sections
  document.querySelectorAll(".section").forEach((el) => {
    el.classList.add("hidden")
  })

  // Remove active class from all buttons
  document.querySelectorAll(".nav-button").forEach((btn) => {
    btn.classList.remove("active")
  })

  // Show selected section and update active button
  document.getElementById(`${section}-section`).classList.remove("hidden")
  document.getElementById(`${section}-btn`).classList.add("active")
  currentSection = section

  // Scroll to top when changing sections
  window.scrollTo(0, 0)
}

// Show notification
function showNotification(message, isSuccess = true) {
  const notification = document.getElementById("notification")
  const notificationText = document.getElementById("notification-text")

  notificationText.textContent = message
  notification.style.background = isSuccess ? "var(--success)" : "var(--destructive)"
  notification.classList.add("show")

  setTimeout(() => {
    notification.classList.remove("show")
  }, 3000)
}

// Chat functionality
async function sendMessage() {
  const input = document.getElementById("chat-input")
  const message = input.value.trim()

  if (!message) return

  // Add user message to chat
  addMessage(message, "user")

  // Clear input and disable it while waiting for response
  input.value = ""
  input.disabled = true

  try {
    // Show typing indicator
    showTypingIndicator()

    // Send message to backend
    const data = await fetchWithErrorHandling(`/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    })

    // Add bot response to chat
    if (data.text) {
      addMessage(data.text, "bot", data.suggestions || [])
    }
  } catch (error) {
    console.error("Chat error:", error)
    addMessage("I'm having trouble connecting right now. Please try again later.", "bot")
  } finally {
    // Always clean up
    hideTypingIndicator()
    input.disabled = false
    input.focus()
  }
}

function showTypingIndicator() {
  isTyping = true
  document.getElementById("typing-indicator").classList.remove("hidden")
  const messagesContainer = document.getElementById("chat-messages")
  messagesContainer.scrollTop = messagesContainer.scrollHeight
}

function hideTypingIndicator() {
  isTyping = false
  document.getElementById("typing-indicator").classList.add("hidden")
}

function addMessage(text, type, suggestions = []) {
  const messagesContainer = document.getElementById("chat-messages")
  const messageDiv = document.createElement("div")
  messageDiv.className = `message ${type}`

  // Sanitize text to prevent HTML injection and format newlines
  const formattedText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>")

  let messageContent = `<div class="message-content">${formattedText}`

  if (suggestions && suggestions.length > 0) {
    messageContent += '<div class="suggestions">'
    suggestions.forEach((suggestion) => {
      messageContent += `<button class="suggestion-btn" onclick="setSuggestion('${suggestion.replace(/'/g, "\\'")}')">${suggestion}</button>`
    })
    messageContent += "</div>"
  }

  messageContent += "</div>"
  messageDiv.innerHTML = messageContent
  messagesContainer.appendChild(messageDiv)

  // Scroll to bottom
  messagesContainer.scrollTop = messagesContainer.scrollHeight
}

function setSuggestion(suggestion) {
  document.getElementById("chat-input").value = suggestion
  document.getElementById("chat-input").focus()
}

function handleKeyPress(event) {
  if (event.key === "Enter") {
    sendMessage()
  }
}

// Load doctors data
async function loadDoctors() {
  try {
    setLoading(true)
    const data = await fetchWithErrorHandling(`/doctors`)
    doctors = data
    populateDoctorSelect()
    displayDoctors()
  } catch (error) {
    console.error("Error loading doctors:", error)
    showNotification("Failed to load doctors. Please try again.", false)
  } finally {
    setLoading(false)
  }
}

function populateDoctorSelect() {
  const select = document.getElementById("doctor-select")
  if (!select) return

  select.innerHTML = '<option value="">Select a doctor</option>'

  doctors.forEach((doctor) => {
    const option = document.createElement("option")
    option.value = doctor.id
    option.textContent = `Dr. ${doctor.first_name} ${doctor.last_name} - ${doctor.specialization}`
    select.appendChild(option)
  })
}

function displayDoctors() {
  const container = document.getElementById("doctors-container")
  if (!container) return

  container.innerHTML = ""

  doctors.forEach((doctor) => {
    const availableDays = JSON.parse(doctor.available_days || "[]").join(", ")
    const availableHours = JSON.parse(doctor.available_hours || "{}")

    const doctorCard = document.createElement("div")
    doctorCard.className = "card doctor-card"
    doctorCard.innerHTML = `
            <div class="card-header">
                <div class="card-title">Dr. ${doctor.first_name} ${doctor.last_name}</div>
                <div class="card-description">${doctor.specialization}</div>
            </div>
            <div class="card-content text-center">
                <img src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=200&q=80" 
                     alt="Dr. ${doctor.first_name} ${doctor.last_name}" class="doctor-image">
                <p class="mb-4">Specialist in ${doctor.specialization.toLowerCase()} with extensive experience.</p>
                <p><strong>Availability:</strong> ${availableDays}, ${availableHours.start || "9:00"} - ${availableHours.end || "17:00"}</p>
                <p><strong>Contact:</strong> ${doctor.phone}</p>
                <button class="btn btn-primary mt-4" onclick="selectDoctor(${doctor.id})">
                    <i class="fas fa-calendar-plus"></i> Book Appointment
                </button>
            </div>
        `

    container.appendChild(doctorCard)
  })
}

function selectDoctor(doctorId) {
  document.getElementById("doctor-select").value = doctorId
  showSection("appointment")
  document.getElementById("appointment-form").scrollIntoView({ behavior: "smooth" })
}

// Appointment form handling
async function handleAppointmentSubmit() {
  const form = document.getElementById("appointment-form")
  const submitBtn = form.querySelector('button[type="submit"]')
  const originalBtnText = submitBtn.textContent

  try {
    // Disable form and show loading state
    submitBtn.disabled = true
    submitBtn.textContent = "Booking..."

    const formData = new FormData(form)
    const appointmentData = {
      doctor_id: formData.get("doctor"),
      date: formData.get("date"),
      time: formData.get("time"),
      reason: formData.get("reason"),
    }

    // Basic validation
    if (!appointmentData.doctor_id || !appointmentData.date || !appointmentData.time) {
      throw new Error("Please fill in all required fields")
    }

    await fetchWithErrorHandling(`/appointments`, {
      method: "POST",
      body: JSON.stringify(appointmentData),
    })

    showNotification("Appointment booked successfully!")
    form.reset()
  } catch (error) {
    console.error("Appointment error:", error)
    showNotification(`Failed to book appointment: ${error.message}`, false)
  } finally {
    // Re-enable form
    submitBtn.disabled = false
    submitBtn.textContent = originalBtnText
  }

  return false // Prevent form submission
}

// Medication functionality
async function loadMedications() {
  try {
    setLoading(true)
    const data = await fetchWithErrorHandling(`/medications`)
    medications = data || []
    displayMedications()
  } catch (error) {
    console.error("Error loading medications:", error)
    showNotification("Failed to load medications. Please try again.", false)
    // Fallback data
    medications = [
      {
        id: 1,
        medication_name: "Amoxicillin",
        dosage: "500mg",
        frequency: "twice daily",
        reminder_times: ["08:00", "20:00"],
      },
      { id: 2, medication_name: "Vitamin D", dosage: "1000 IU", frequency: "once daily", reminder_times: ["12:00"] },
    ]
    displayMedications()
  }
}

function displayMedications() {
  const container = document.getElementById("medications-container")
  if (!container) return

  if (medications.length === 0) {
    container.innerHTML =
      '<p class="text-center">No medications added yet. Use the form to add a new medication reminder.</p>'
    return
  }

  container.innerHTML = ""

  medications.forEach((med) => {
    const medElement = document.createElement("div")
    medElement.className = "card mb-4"
    const reminderTimes = Array.isArray(med.reminder_times)
      ? med.reminder_times.filter((t) => t !== null).join(", ")
      : "Not set"

    medElement.innerHTML = `
            <div class="card-content">
                <div class="flex justify-between items-center">
                    <div>
                        <h4 class="font-semibold">${med.medication_name}</h4>
                        <p><strong>Dosage:</strong> ${med.dosage}</p>
                        <p><strong>Frequency:</strong> ${med.frequency}</p>
                        <p><strong>Reminders:</strong> ${reminderTimes}</p>
                    </div>
                    <button class="btn btn-destructive" onclick="removeMedication(${med.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `
    container.appendChild(medElement)
  })
}

async function handleMedicationSubmit() {
  const name = document.getElementById("medication-name").value
  const dosage = document.getElementById("medication-dosage").value
  const time = document.getElementById("medication-time").value
  const daily = document.getElementById("medication-daily").checked

  if (!name || !dosage || !time) {
    showNotification("Please fill all required fields", false)
    return
  }

  const frequency = daily ? "Once daily" : "As needed"
  const reminderTimes = daily ? [time] : []

  // API call to add medication
  try {
    const response = await fetch(`${API_BASE_URL}/api/medications`, {
      mode: "cors",
      credentials: "include",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        patient_id: 1, // Using patient ID 1 for demo
        medication_name: name,
        dosage: dosage,
        frequency: frequency,
        reminder_times: reminderTimes,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    if (data.error) {
      showNotification(data.error, false)
    } else {
      // Add to local state and update UI
      const newMedication = {
        id: data.medication_id || data.id, // Handle both response formats
        medication_name: name,
        dosage: dosage,
        frequency: frequency,
        reminder_times: reminderTimes,
      }
      medications.push(newMedication)
      displayMedications()
      showNotification("Medication reminder added successfully!")
      document.getElementById("medication-form").reset()
    }
  } catch (error) {
    console.error("Error:", error)
    showNotification("Failed to add medication: " + error.message, false)
  }
}

function removeMedication(medicationId) {
  // In a real app, you would make a DELETE API call here.
  // For this demo, we'll just remove it from the local state.
  medications = medications.filter((med) => med.id !== medicationId)
  displayMedications()
  showNotification("Medication removed.")
}

// Placeholder for reminder history functionality
function loadReminders() {
  // In a real app, this would fetch reminder history from an API.
  const container = document.getElementById("reminder-history")
  if (container) {
    // Initially, the HTML content serves as the default state.
    // container.innerHTML = '<p class="text-center">No reminders set yet</p>';
  }
}

// Setup event listeners
function setupEventListeners() {
  // Chat input
  const chatInput = document.getElementById("chat-input")
  if (chatInput) {
    chatInput.addEventListener("keypress", handleKeyPress)
  }

  // Appointment form
  const appointmentForm = document.getElementById("appointment-form")
  if (appointmentForm) {
    appointmentForm.addEventListener("submit", (e) => {
      e.preventDefault()
      handleAppointmentSubmit()
    })
  }

  // Medication form
  const medicationForm = document.getElementById("medication-form")
  if (medicationForm) {
    medicationForm.addEventListener("submit", (e) => {
      e.preventDefault()
      handleMedicationSubmit()
    })
  }
}

// Initialize the app when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", init)

// ---------------- Appointment Modal ----------------
function openModal() {
  document.getElementById("appointment-modal").classList.remove("hidden")
}

function closeModal() {
  document.getElementById("appointment-modal").classList.add("hidden")
}

const appointmentForm = document.getElementById("appointment-popup-form")
if (appointmentForm) {
  appointmentForm.addEventListener("submit", function (e) {
    e.preventDefault()

    const date = document.getElementById("appointment-date").value
    const time = document.getElementById("appointment-time").value
    const reason = document.getElementById("reason").value

    if (!date || !time) {
      showAppointmentNotification("⚠️ Please select both date and time")
      return
    }

    // Simulated confirmation response
    showAppointmentNotification(`✅ Appointment set for ${date} at ${time}`)

    // Reset form and close modal
    this.reset()
    closeModal()
  })
}

function showAppointmentNotification(message) {
  const notif = document.getElementById("appointment-notification")
  const notifText = document.getElementById("appointment-notification-text")
  notifText.textContent = message

  notif.classList.add("show")
  setTimeout(() => {
    notif.classList.remove("show")
  }, 3000) // disappears after 3s
}
