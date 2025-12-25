# 🎉 PartyFlow - Event Management & Ticketing System

**PartyFlow** is a comprehensive Full Stack solution for managing party lines and ticket sales.
It combines a user-friendly **Telegram Bot** for customers, a professional **Web Dashboard** for admins, and secure payment processing via **Stripe**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Stripe](https://img.shields.io/badge/Stripe-Payments-violet)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)

---

## 🚀 Key Features

### 🤖 For Users (Telegram Bot)
* **Browse Events:** View upcoming parties with real-time details (Location, Date, Price).
* **Smart Registration:** Interactive conversation flow to collect Name and Phone Number.
* **💳 Secure Payments:** Integrated **Stripe Checkout** for secure credit card processing (Test Mode).
* **Inventory Check:** Prevents overbooking automatically (Sold Out logic).

### 🖥️ For Admins (Web Dashboard)
* **Event Management:** Add new parties via a clean web interface.
* **📊 Live Analytics:** Real-time stats on **Total Revenue**, **Tickets Sold**, and **Top Events**.
* **Database:** Persistent storage using SQLite.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **Database:** SQLite (Managed via custom `db_manager`)
* **Payments:** Stripe API
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
│   ├── dashboard.html      # HTML Admin Interface
│   └── success.html        # Payment Success Page
├── bot.py                  # Telegram Bot Logic (Frontend 1)
├── main.py                 # FastAPI Server (Backend)
├── manage.py               # CLI tool for DB initialization
├── .env                    # Environment variables (Tokens & Keys)
└── requirements.txt        # Python dependencies