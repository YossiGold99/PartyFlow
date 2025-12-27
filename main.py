import os
import stripe
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from core import db_manager
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to the specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Configure Stripe API Key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = "http://127.0.0.1:8000"

# Mount static files (CSS) and templates (HTML)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Data model for ticket requests
class TicketRequest(BaseModel):
    event_id: int
    user_name: str
    user_id: int
    phone_number: str

# Data model for creating a new event via React
class EventRequest(BaseModel):
    name: str
    date: str
    location: str
    price: float
    total_tickets: int
# --- General Routes ---

# API Endpoint for React Dashboard
@app.get("/api/stats")
def get_dashboard_stats():
    return {
        "stats": {
            "total_revenue": db_manager.get_total_revenue(),
            "tickets_sold": db_manager.get_total_tickets_sold(),
            "top_event": db_manager.get_top_event()
        },
        "events": db_manager.get_events()
    }

@app.post("/api/events")
def add_event_api(event: EventRequest):
    """API endpoint to add a new event via React form."""
    db_manager.add_event(
        event.name,
        event.date,
        event.location,
        event.price,
        event.total_tickets
    )
    return {"message": "Event added successfully"}

@app.get("/")
def read_root():
    return {"message": "PartyBot API is running with Stripe integration!"}

@app.get("/events")
def get_events_api():
    """Returns a list of all events (used by the Bot)."""
    return {"events": db_manager.get_events()}

# --- Stripe Payment Logic ---

@app.post("/create_checkout_session")
def create_checkout_session(ticket: TicketRequest):
    """
    Creates a Stripe Checkout Session.
    Instead of buying immediately, we generate a payment link.
    """
    # 1. Check inventory before allowing payment
    event = db_manager.get_event_by_id(ticket.event_id)
    sold_count = db_manager.get_tickets_sold(ticket.event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if sold_count >= event['total_tickets']:
        raise HTTPException(status_code=400, detail="SOLD OUT")

    try:
        # 2. Create the Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'ils',  # Israeli Shekel (or usd)
                    'product_data': {
                        'name': f"Ticket: {event['name']}",
                    },
                    'unit_amount': int(event['price'] * 100), # Stripe uses cents/agoras
                },
                'quantity': 1,
            }],
            mode='payment',
            # 3. Store user data in metadata to retrieve it after payment
            metadata={
                "event_id": ticket.event_id,
                "user_id": ticket.user_id,
                "user_name": ticket.user_name,
                "phone_number": ticket.phone_number
            },
            # Redirect URLs
            success_url=YOUR_DOMAIN + "/payment_success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_DOMAIN + "/payment_cancel",
        )
        return {"checkout_url": checkout_session.url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment_success", response_class=HTMLResponse)
def payment_success(session_id: str, request: Request):
    """
    Handles the redirect from Stripe after a successful payment.
    Verifies the session and saves the ticket to the database.
    """
    try:
        # Verify payment status with Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Retrieve user data from metadata
            data = session.metadata
            
            # Save ticket to database (Final Step)
            db_manager.add_ticket(
                event_id=int(data['event_id']),
                user_id=int(data['user_id']),
                user_name=data['user_name'],
                phone_number=data['phone_number']
            )
            # Render the success page
            return templates.TemplateResponse("success.html", {"request": request})
        else:
            return "Payment Failed or Pending."
            
    except Exception as e:
        return f"Error processing payment: {e}"

@app.get("/payment_cancel")
def payment_cancel():
    return {"message": "Order canceled. You can close this window."}

# --- Admin Dashboard Routes ---

@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    """Renders the Admin Dashboard with real-time analytics."""
    events = db_manager.get_events()
    
    # Fetch analytics data
    stats = {
        "total_revenue": db_manager.get_total_revenue(),
        "tickets_sold": db_manager.get_total_tickets_sold(),
        "top_event": db_manager.get_top_event()
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "events": events, 
        "stats": stats
    })

@app.post("/dashboard/add")
def add_event_web(
    name: str = Form(...), 
    date: str = Form(...), 
    location: str = Form(...), 
    price: float = Form(...), 
    total_tickets: int = Form(...)
):
    """Adds a new event via the web form."""
    db_manager.add_event(name, date, location, price, total_tickets)
    return RedirectResponse(url="/dashboard", status_code=303)