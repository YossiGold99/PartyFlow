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

    # Tickets table
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

# Function to add an event (used by manage.py and web dashboard)
def add_event(name, date, location, price, total_tickets):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (name, date, location, price, total_tickets)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, date, location, price, total_tickets))
    conn.commit()
    conn.close()


def get_event_by_id(event_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Retrieves the party details by ID
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return dict(event) if event else None

def get_tickets_sold(event_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Count how many tickets were sold for this party
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE event_id = ?", (event_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- Analytics Functions ---

def get_total_revenue():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Calculate total revenue: sum of (event price) for all sold tickets
    cursor.execute('''
        SELECT SUM(events.price) 
        FROM tickets 
        JOIN events ON tickets.event_id = events.id
    ''')
    result = cursor.fetchone()[0]
    conn.close()
    return round(result, 2) if result else 0

def get_total_tickets_sold():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Count total number of rows in tickets table
    cursor.execute("SELECT COUNT(*) FROM tickets")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_top_event():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Find the event with the highest number of sold tickets
    cursor.execute('''
        SELECT events.name, COUNT(tickets.id) as ticket_count
        FROM tickets
        JOIN events ON tickets.event_id = events.id
        GROUP BY events.id
        ORDER BY ticket_count DESC
        LIMIT 1
    ''')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "No Sales Yet"