# PartyFlow
party management bot
# 🎉 PartyFlow - Event Management System

**PartyFlow** is a comprehensive Full Stack solution for managing party lines and ticket sales.
It combines a user-friendly **Telegram Bot** for customers with a powerful **Web Dashboard** for admins.

---

## 🚀 Key Features

### 🤖 For Users (Telegram Bot)
* **Browse Events:** View upcoming parties with real-time details (Location, Date, Price).
* **Smart Registration:** Interactive conversation flow to collect Name and Phone Number.
* **Ticket Purchase:** Real-time communication with the server to book tickets.
* **Inventory Check:** Prevents overbooking (Sold Out logic).

### 🖥️ For Admins (Web Dashboard)
* **Event Management:** Add new parties via a clean web interface.
* **Live Overview:** View all active events and their details.
* **Database:** Persistent storage using SQLite.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **Database:** SQLite (Managed via custom `db_manager`)
* **Frontend (Web):** Jinja2 Templates + Bootstrap 5 + Custom CSS
* **Frontend (Bot):** pyTelegramBotAPI (Telebot)
* **HTTP Client:** Requests

---

## 📂 Project Structure

```text
PartyFlow/
├── core/
│   └── db_manager.py       # Database logic & SQL queries
├── database/
│   └── party_bot.db        # SQLite file (Auto-generated)
├── static/
│   └── style.css           # Custom CSS for the dashboard
├── templates/
│   └── dashboard.html      # HTML Admin Interface
├── bot.py                  # Telegram Bot Logic (Frontend 1)
├── main.py                 # FastAPI Server (Backend)
├── manage.py               # CLI tool for DB initialization
├── .env                    # Environment variables (Token)
└── requirements.txt        # Python dependencies