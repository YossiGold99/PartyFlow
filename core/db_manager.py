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

if __name__ == "__main__":
    print("--testing Database manager--")

    #1. Add a test event
    add_event("christmas Party", "2024-12-31", "hamon 17,TLV", 250, 800)
    # 2.Fecth and display all events to see if it workded
    print("/mCurrent Ecencts in Database:")
    events = get_all_events()
    for event in events:
        print(f"{event['name']} - {event['price']} NIS")