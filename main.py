import os
import stripe
import qrcode 
import requests
import secrets
import asyncio
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from core import db_manager
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Validates the username and password using secure constant-time comparison.
    Change 'admin' and '1234' to your desired credentials.
    """
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "1234")

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Enable CORS for React frontend
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

@app.get("/api/tickets/{user_id}")
def get_tickets_api(user_id: int):
    # This calls the function inside core/db_manager.py
    tickets = db_manager.get_user_tickets(user_id)
    return {"tickets": tickets}

# --- Automatic Reminder Logic ---

scheduler = AsyncIOScheduler()

def check_and_send_reminders():
    # Get today's date in YYYY-MM-DD format (matches our DB format)
    today = date.today().isoformat()
    print(" Scheduler running: chechking for events on {today}")

    # 1.find events happening today
    events = db_manager.get_events_by_date(today)

    if not events:
        print("   💤 No events today.")
        return
    
    token = os.getenv("TELEGRAM_TOKEN")

    # 2. For each event, notify ticket holders
    for event in events:
        print(f"   🎉 FOUND EVENT: {event['name']}! Sending reminders...")
        user_ids = db_manager.get_users_with_tickets_for_event(event["id"])

        for user_id in user_ids:
            try:
                msg = (
                    f"Today is the day!\n\n"
                    f"Get ready! **{event['name']}** is happening today.\n"
                    f"Location: {event['location']}\n\n"
                    f"See you there!"
                )

                # send direct message via Telegram API
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                    "chat_id": user_id, 
                    "text": msg, 
                    "parse_mode": "Markdown"
                })
                print(f"   ✅ Sent to {user_id}")

                
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")

#  --- Start the scheduler ---

@app.on_event("startup")
def start_scheduler():
    # Option A: Run once immediately when server starts (For Testing)
    # asyncio.create_task(check_and_send_reminders()) 
    
    # Option B: Run every day at 10:00 AM (Production)
    scheduler.add_job(check_and_send_reminders, 'cron', hour=10, minute=0)
    
    # Option C: Run every 60 seconds (For Demo/Testing now)
    # scheduler.add_job(check_and_send_reminders, 'interval', seconds=20)
    
    scheduler.start()
    print("✅ Scheduler started (Checking every 10h)")

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
    Handles successful payment:
    1. Verifies Stripe session.
    2. Saves ticket to DB.
    3. Generates QR Code.
    4. Sends QR Code to user's Telegram.
    """
    try:
        # Verify payment status with Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            data = session.metadata
            
            # 1. Save ticket to database
            ticket_id = db_manager.add_ticket(
                event_id=int(data['event_id']),
                user_id=int(data['user_id']),
                user_name=data['user_name'],
                phone_number=data['phone_number']
            )
            
            # 2. Get event details for the ticket
            event = db_manager.get_event_by_id(int(data['event_id']))
            
            # 3. Generate QR Code
            qr_path = generate_qr_code(ticket_id, event['name'], data['user_name'])
            
            # 4. Send QR Code to Telegram
            caption = (
                f"🎉 Payment Confirmed!\n"
                f"Event: {event['name']}\n"
                f"Ticket ID: #{ticket_id}\n\n"
                f"Show this QR code at the entrance."
            )
            send_ticket_to_telegram(data['user_id'], qr_path, caption)

            return templates.TemplateResponse("success.html", {"request": request})
        else:
            return "Payment Failed or Pending."
            
    except Exception as e:
        return f"Error processing payment: {e}"

@app.get("/payment_cancel")
def payment_cancel():
    return {"message": "Order canceled. You can close this window."}

# --- Admin Dashboard Routes ---

@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(get_current_username)])
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

@app.post("/dashboard/add", dependencies=[Depends(get_current_username)])
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

# --- Authentication Model ---

class LoginRequest(BaseModel):
    password: str

# --- Authentication Route ---

@app.post("/api/login")
def login(request: LoginRequest):
    """
    Validates the admin password.
    Compares the input against the environment variable ADMIN_PASSWORD.
    """
    # Get password from .env or use default "admin"
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    if request.password == admin_password:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # --- Helper Functions ---

def generate_qr_code(ticket_id: int, event_name: str, user_name: str):
    """
    Generates a QR code image for the ticket.
    Saves it in the 'static' folder.
    """
    # Ensure static folder exists
    if not os.path.exists("static"):
        os.makedirs("static")
        
    # Data to encode in the QR (e.g., a verify URL or JSON data)
    data = f"TICKET-ID:{ticket_id} | EVENT:{event_name} | OWNER:{user_name}"
    
    # Create QR image
    qr = qrcode.make(data)
    file_path = f"static/ticket_{ticket_id}.png"
    qr.save(file_path)
    return file_path

def send_ticket_to_telegram(chat_id, file_path, caption):
    """
    Sends the generated QR code image to the user via Telegram API.
    """
    bot_token = os.getenv("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    with open(file_path, "rb") as image_file:
        files = {"photo": image_file}
        data = {"chat_id": chat_id, "caption": caption}
        requests.post(url, data=data, files=files)