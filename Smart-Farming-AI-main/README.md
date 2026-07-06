# 🌱 Smart Farming: AI-Powered Irrigation System

An intelligent irrigation optimization system that uses **real-time sensor data and AI reasoning** to determine whether crops need watering and for how long.

This project demonstrates how **Artificial Intelligence and IoT data** can be used to reduce water wastage and improve agricultural efficiency.

---

# 🚀 Project Overview

Traditional irrigation systems often rely on **fixed schedules**, which can lead to:

- Overwatering
- Water wastage
- Poor crop health

This project replaces fixed irrigation schedules with **AI-based decision making**.

The system analyzes:

- Soil moisture
- Temperature
- Environmental conditions

and determines:

- Whether irrigation is required
- How long the pump should run

---

# 🧠 AI Decision Engine

The irrigation logic uses **Google Gemini AI** to analyze environmental data and generate decisions with explanations.

Example output:


Moisture: 516
Temperature: 40°C

Pump: ON
Duration: 8 minutes

Justification:
The soil moisture indicates slightly dry soil. Due to high temperature,
watering duration is increased to compensate for evaporation.


---
```
# 🏗 System Architecture


IoT(simulated) Sensors (Moisture + Temperature)
↓
Google Sheets (Sensor Data Storage)
↓
Python AI Engine (optimize.py)
↓
Flask API Server (server.py)
↓
Frontend Dashboard (HTML + JS + CSS)

```
---

# 📊 Dashboard Features

The web dashboard displays:

- 🌡 Real-time temperature
- 💧 Soil moisture levels
- 🚰 Pump ON/OFF decision
- ⏱ Recommended irrigation duration
- 🧠 AI-generated explanation

---

# 🛠 Tech Stack

## Backend
- Python
- Flask
- Google Gemini AI
- Google Sheets API

## Frontend
- HTML
- CSS
- JavaScript

## AI & Data Processing
- Gemini AI
- Real-time sensor data analysis

---

# 🌍 Impact

This system helps:

- Reduce water wastage
- Improve irrigation efficiency
- Provide explainable AI decisions
- Support sustainable agriculture

AI-driven irrigation ensures **water is used only when crops actually need it**.

---

# 👨‍💻 Team

**Team Name:** Code n Conquer

Project developed as part of an innovation challenge focused on **Smart Agriculture and Sustainable Farming Technologies**.

---
