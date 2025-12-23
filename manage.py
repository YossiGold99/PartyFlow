from core import db_manager

action = input("Do you want to 'add' or 'delete' an event? ")

if action == 'delete':
    # display all events
    events = db_manager.get_all_events()
    for event in events:
        print(event['id'], event['name'])

    # get event id to delete
    event_id = input("Enter event ID to delete: ")
    db_manager.delete_event(event_id)

elif action == 'add':
    print("--- Add New Event ---")
    name = input("Event Name: ")
    date = input("Event Date (YYYY-MM-DD): ")
    location = input("Event Location: ")
    price = float(input("Ticket Price: "))
    total_tickets = int(input("Total Tickets Available: "))
    db_manager.add_event(name, date, location, price, total_tickets)
    # print(f"Event '{name}' added successfully.")

# if __name__ == "__main__":
#     db_manager.create_tables()
#     print("Tables created successfully!")
    
