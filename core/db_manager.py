import sqlite3
import os

# Path to the database file
DB_NAME = os.path.join("database", "party_bot.db")

# --- Existing Functions ---

def create_tables():
    """Creates the necessary tables if they don't exist."""
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Events table
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
    
    # Create Tickets table
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

def add_ticket(event_id, user_id, user_name, phone_number):
    """Adds a new ticket to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tickets (event_id, user_id, user_name, phone_number) 
            VALUES (?, ?, ?, ?)
        ''', (event_id, user_id, user_name, phone_number))
        
        conn.commit()
        last_row_id = cursor.lastrowid # Returns the ID of the created ticket
        conn.close()
        return last_row_id
    except Exception as e:
        print(f"Database Error: {e}")
        return False

def get_events():
    """Fetches all events."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_event(name, date, location, price, total_tickets):
    """Adds a new event."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (name, date, location, price, total_tickets) 
        VALUES (?, ?, ?, ?, ?)
    ''', (name, date, location, price, total_tickets))
    conn.commit()
    conn.close()

def get_event_by_id(event_id):
    """Fetches a single event by ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return dict(event) if event else None

def get_tickets_sold(event_id):
    """Counts how many tickets were sold for a specific event."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE event_id = ?", (event_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_revenue():
    """Calculates total revenue from all ticket sales."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(events.price) 
        FROM tickets 
        JOIN events ON tickets.event_id = events.id
    ''')
    result = cursor.fetchone()[0]
    conn.close()
    return round(result, 2) if result else 0

def get_total_tickets_sold():
    """Counts total tickets sold across all events."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_top_event():
    """Finds the event with the highest sales."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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

# --- New Function ---

def get_user_tickets(user_id):
    """Fetches all tickets for a specific user ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query to join ticket data with event details
    cursor.execute("""
        SELECT t.id, e.name, e.date, e.location 
        FROM tickets t
        JOIN events e ON t.event_id = e.id
        WHERE t.user_id = ?
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_events_by_date(target_date):
    # Returns all events happening on a specific date (format: YYYY-MM-DD).
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE date = ?", (target_date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_users_with_tickets_for_event(event_id):
    #Returns a list of user_ids that have a ticket for a specific event.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM tickets WHERE event_id = ?", (event_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]