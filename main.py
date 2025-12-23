from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core import db_manager

app = FastAPI()

# Request model - includes phone_number
class TicketRequest(BaseModel):
    event_id: int
    user_name: str
    user_id: int
    phone_number: str

@app.get("/")
def read_root():
    return {"message": "PartyBot API is running!"}

@app.get("/events")
def get_events():
    events = db_manager.get_events()
    return {"events": events}

@app.post("/buy_ticket")
def buy_ticket(ticket: TicketRequest):
    # Pass all data, including phone number, to the database manager
    success = db_manager.add_ticket(
        event_id=ticket.event_id,
        user_id=ticket.user_id,
        user_name=ticket.user_name,
        phone_number=ticket.phone_number
    )
    
    if success:
        return {"status": "success", "message": f"Ticket bought for {ticket.user_name}"}
    else:
        # Raise HTTP 500 error if database operation fails
        raise HTTPException(status_code=500, detail="Failed to save ticket in database")