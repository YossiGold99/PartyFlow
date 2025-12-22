from core import db_manager

# 1. show all existing events
events = db_manager.get_all_events()

print("--list of events--")
for event in events:
    print(event['id'], event['name'])

# 2. ask user ifor ID to delete
event_id = input("\nEnter event id to delete: ")

# 3.perform deletion
db_manager.delete_event(event_id)