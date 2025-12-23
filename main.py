from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from core import db_manager

app = FastAPI()

# 1. Setup Templates (Connects to the 'templates' folder)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- API Models ---
class TicketRequest(BaseModel):
    event_id: int
    user_name: str
    user_id: int
    phone_number: str

# --- Routes ---

@app.get("/")
def read_root():
    return {"message": "PartyBot API is running! Go to /dashboard to manage."}

# API: Get all events (JSON) - Used by the Bot
@app.get("/events")
def get_events_api():
    events = db_manager.get_events()
    return {"events": events}

# API: Buy Ticket - Used by the Bot
@app.post("/buy_ticket")
def buy_ticket(ticket: TicketRequest):
    # 1. Get event details to check limits
    event = db_manager.get_event_by_id(ticket.event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # 2. Check how many tickets were already sold
    sold_count = db_manager.get_tickets_sold(ticket.event_id)
    total_tickets = event['total_tickets']
    
    # 3. Logic Check: Is it Sold Out?
    if sold_count >= total_tickets:
        raise HTTPException(status_code=400, detail="Sorry, this event is SOLD OUT!")

    # 4. If space is available, proceed to buy
    success = db_manager.add_ticket(
        event_id=ticket.event_id,
        user_id=ticket.user_id,
        user_name=ticket.user_name,
        phone_number=ticket.phone_number
    )
    
    if success:
        return {
            "status": "success", 
            "message": f"Ticket bought! ({sold_count + 1}/{total_tickets} sold)"
        }
    else:
        raise HTTPException(status_code=500, detail="Database Error")

# --- WEB DASHBOARD ROUTES (Full Stack Part) ---

# WEB: Show the Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    # 1. Get list of events
    events = db_manager.get_events()
    
    # 2. Get Analytics Data using the new functions
    stats = {
        "total_revenue": db_manager.get_total_revenue(),
        "tickets_sold": db_manager.get_total_tickets_sold(),
        "top_event": db_manager.get_top_event()
    }

    # 3. Render HTML with both 'events' and 'stats'
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "events": events,
        "stats": stats
    })

# WEB: Add a new event via the form
@app.post("/dashboard/add")
def add_event_web(
    name: str = Form(...),
    date: str = Form(...),
    location: str = Form(...),
    price: float = Form(...),
    total_tickets: int = Form(...)
):
    # Add to database
    db_manager.add_event(name, date, location, price, total_tickets)
    # Reload the page to show the new event
    return RedirectResponse(url="/dashboard", status_code=303)