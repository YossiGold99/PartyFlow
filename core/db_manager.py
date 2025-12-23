import sqlite3
import os

DB_NAME = os.path.join("database", "party_bot.db")

def create_tables():
    # Ensure the database directory exists
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            price REAL NOT NULL,
            total_tickets INTEGER NOT NULL
        )
    ''')

    # Tickets table - includes the phone_number column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            phone_number TEXT,
            purchase_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Function to add a ticket to the database
def add_ticket(event_id, user_id, user_name, phone_number):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (event_id, user_id, user_name, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (event_id, user_id, user_name, phone_number))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False

def get_events():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Function to add an event (used by manage.py)
def add_event(name, date, location, price, total_tickets):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (name, date, location, price, total_tickets)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, date, location, price, total_tickets))
    conn.commit()
    conn.close()