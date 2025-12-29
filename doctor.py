import sqlite3
import requests
import os

# 1. הגדרות
DB_PATH = os.path.join("database", "party_bot.db")
USER_ID = 846858195  # ה-ID שלך מהלוג הקודם
API_URL = "http://127.0.0.1:8000/api/tickets"

print("--- 🩺 STARTING DIAGNOSIS ---")

# 2. בדיקת דאטאבייס ישירה (האם ה-JOIN עובד?)
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"\n1. Checking DB for User ID: {USER_ID}...")
    
    # בדיקה אם יש כרטיסים בכלל
    cursor.execute("SELECT count(*) FROM tickets WHERE user_id = ?", (USER_ID,))
    raw_count = cursor.fetchone()[0]
    print(f"   ✅ Raw tickets found in DB: {raw_count}")

    # בדיקה קריטית: האם הכרטיס מקושר לאירוע קיים? (JOIN Check)
    # אם האירוע נמחק, השאילתה הזו תחזיר כלום - וזו הבעיה!
    cursor.execute("""
        SELECT t.id, e.name 
        FROM tickets t
        JOIN events e ON t.event_id = e.id
        WHERE t.user_id = ?
    """, (USER_ID,))
    
    joined_rows = cursor.fetchall()
    print(f"   🧐 Tickets matched with valid Events: {len(joined_rows)}")
    
    if raw_count > 0 and len(joined_rows) == 0:
        print("   ❌ PROBLEM FOUND: You have tickets, but the Events (parties) were deleted!")
        print("      (The tickets point to event_IDs that no longer exist)")
    
    conn.close()

except Exception as e:
    print(f"   ❌ DB Error: {e}")

# 3. בדיקת השרת (API)
print(f"\n2. Testing Server API: {API_URL}/{USER_ID}...")
try:
    response = requests.get(f"{API_URL}/{USER_ID}", timeout=5)
    print(f"   📡 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        tickets = data.get('tickets', [])
        print(f"   📦 JSON Response: {data}")
        print(f"   🎉 Server returned {len(tickets)} tickets.")
    elif response.status_code == 404:
        print("   ❌ Error 404: The route was not found in main.py!")
    else:
        print(f"   ❌ Server Error: {response.text}")

except Exception as e:
    print(f"   ❌ Connection Failed:Is uvicorn running? {e}")

print("\n--- 🏁 DIAGNOSIS COMPLETE ---")