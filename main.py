from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from core import db_manager


app = FastAPI()
@app.get("/")

def home():
    return {"message": "Server is running"}

@app.get("/events")
def get_events():
    events = db_manager.get_all_events()
    return {"events": events}

# Define the data structure for buying a ticket
class TicketRequest(BaseModel):
    event_id: int
    user_name: str
    user_id: int

@app.post("/buy_ticket")
def buy_ticket(ticket: TicketRequest):
    # Call the database manger to perform the sale
    db_manager.sell_ticket(ticket.event_id, ticket.user_name, ticket.user_id)
    # Check remaining tickets
    return {"status": "success", "message": f"Ticket bought for {ticket.user_name} for event {ticket.event_id}"}