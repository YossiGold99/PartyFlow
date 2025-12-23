import sqlite3
import os

# 1. Get the current directory (core)
current_dir = os.path.dirname(__file__)
# 2. Go up one level to the main project folder
base_dir = os.path.dirname(current_dir)
# 3. Bulid the path to the database file
DB_PATH = os.path.join(base_dir,'database','party_bot.db')
print (f"Database path: {DB_PATH}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name 
    return conn

def add_event(name, date, location, price, total_tickets):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                INSERT INTO events (name, date, location, price, total_tickets)
                VALUES (?, ?, ?, ?, ?)
                ''', (name, date, location, price, total_tickets))
    conn.commit()
    conn.close()
    print (f"Event '{name}' added successfully.")

def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Select all columns from the events table
    cursor.execute('SELECT * FROM events') 
    events = cursor.fetchall() # Returns a list of Row objects
    conn.close()
    return events

def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    print(f"Event {event_id} deleted successfully.")

def get_remaining_tickets(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. count sold tickets
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE event_id = ?', (event_id,))
    sold_count = cursor.fetchone()[0]
    # 2. get total_tickets from events table
    cursor.execute("SELECT total_tickets FROM events WHERE id = ?", (event_id,))

    event = cursor.fetchone()
    total_tickets = event['total_tickets']
    conn.close()
    return total_tickets - sold_count

def sell_ticket(event_id, user_id,user_name):
    conn = get_db_connection()
    cursor = conn.cursor()
# Insert ticket into the tickets table
# We use the 'phone_number' column to store the Telegram user_id
    cursor.execute('''
                INSERT INTO tickets (event_id, phone_number, user_name)
                VALUES (?,?,?)
                ''', (event_id, user_name, str(user_id)))
    conn.commit()
    conn.close()
    print(f"Ticket sold to {user_name} (ID: {user_id}) for event {event_id}")

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create a party table (if it doesn't exist)
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
    
    # Create a card table (the new one!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Tables created successfully.")
    


# This block runs only if we execute this file directly
if __name__ == "__main__":
    print("--testing Database manager--")
    # 1. Test Adding 
    print("\n--- Adding a dummy event ---")
    add_event("Mistake Party", "2099-01-01", "TLV", 0, 500)
    events = get_all_events()
    last_event = events[-1] 
    last_id = last_event['id']
    print(f"Added event: {last_event['name']} (ID: {last_id})")
    # 2. Test Ticket Calculation
    print("\n--- Testing Ticket Count ---")
    remaining = get_remaining_tickets(last_id)
    print(f"Tickets remaining for event {last_id}: {remaining}")
    # 3. Test Deletion
    print(f"\n--- Deleting event {last_id} ---")
    delete_event(last_id)
    # 4. Final Verification
    print("\n--- Final Event List ---")
    current_events = get_all_events()
    for event in current_events:
        print(f"{event['id']}: {event['name']}")