import os
import stripe
import qrcode 
import requests
import secrets
import logging
import asyncio
from datetime import date
from dotenv import load_dotenv
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# FastAPI Imports
from fastapi import FastAPI, HTTPException, Request, Form, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Core Logic
from core import db_manager

# --- Configuration & Setup ---

# 1. Load environment variables
load_dotenv()

# 2. Configure Logging (Professional console output)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 3. Initialize App
app = FastAPI()

# 4. Security Setup
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Validates the username and password using secure constant-time comparison.
    """
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "1234")

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 5. Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Third-Party Keys
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = "http://127.0.0.1:8000"  # Change this in production

# 7. Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Data Models ---

class TicketRequest(BaseModel):
    event_id: int
    user_name: str
    user_id: int
    phone_number: str

class EventRequest(BaseModel):
    name: str
    date: str
    location: str
    price: float
    total_tickets: int

class LoginRequest(BaseModel):
    password: str


# --- Routes ---

@app.get("/")
def read_root():
    """Redirects the homepage directly to the dashboard."""
    return RedirectResponse(url="/dashboard")

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

# -- API Routes --

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
    db_manager.add_event(
        event.name, event.date, event.location, event.price, event.total_tickets
    )
    return {"message": "Event added successfully"}

@app.get("/events")
def get_events_api():
    """Returns a list of all events (used by the Bot)."""
    return {"events": db_manager.get_events()}

@app.get("/api/tickets/{user_id}")
def get_tickets_api(user_id: int):
    tickets = db_manager.get_user_tickets(user_id)
    return {"tickets": tickets}

@app.post("/api/login")
def login(request: LoginRequest):
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    if request.password == admin_password:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")


# --- Dashboard Routes (Admin) ---

@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(get_current_username)])
def show_dashboard(request: Request, page: int = 1, q: str = ""):
    """Renders the Admin Dashboard with Pagination & Search."""
    
    events, total_pages = db_manager.get_events_paginated(page=page, per_page=5, search_query=q)
    
    stats = {
        "total_revenue": db_manager.get_total_revenue(),
        "tickets_sold": db_manager.get_total_tickets_sold(),
        "top_event": db_manager.get_top_event()
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "events": events, 
        "stats": stats,
        "current_page": page,
        "total_pages": total_pages,
        "search_query": q
    })

@app.post("/dashboard/add", dependencies=[Depends(get_current_username)])
def add_event_web(
    name: str = Form(...), 
    date: str = Form(...), 
    location: str = Form(...), 
    price: float = Form(...), 
    total_tickets: int = Form(...)
):
    db_manager.add_event(name, date, location, price, total_tickets)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/dashboard/broadcast", dependencies=[Depends(get_current_username)])
def broadcast_message(event_id: int = Form(...), message: str = Form(...)):
    """Sends a broadcast message to all users who purchased a ticket."""
    event = db_manager.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    user_ids = db_manager.get_users_with_tickets_for_event(event_id)
    bot_token = os.getenv("TELEGRAM_TOKEN")
    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    count = 0
    for user_id in user_ids:
        try:
            full_text = (
                f"📢 **Update regarding {event['name']}**\n\n"
                f"{message}\n\n"
                f"-- PartyFlow Management"
            )
            requests.post(send_url, json={
                "chat_id": user_id, 
                "text": full_text, 
                "parse_mode": "Markdown"
            })
            count += 1
        except Exception as e:
            logging.error(f"Failed to send broadcast to {user_id}: {e}")
            
    logging.info(f"Broadcast sent to {count} users for event {event_id}")
    return RedirectResponse(url="/dashboard", status_code=303)


# --- Stripe Payment Logic ---

@app.post("/create_checkout_session")
def create_checkout_session(ticket: TicketRequest):
    # Check inventory
    event = db_manager.get_event_by_id(ticket.event_id)
    sold_count = db_manager.get_tickets_sold(ticket.event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if sold_count >= event['total_tickets']:
        raise HTTPException(status_code=400, detail="SOLD OUT")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'ils',
                    'product_data': {'name': f"Ticket: {event['name']}"},
                    'unit_amount': int(event['price'] * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata={
                "event_id": ticket.event_id,
                "user_id": ticket.user_id,
                "user_name": ticket.user_name,
                "phone_number": ticket.phone_number
            },
            success_url=YOUR_DOMAIN + "/payment_success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_DOMAIN + "/payment_cancel",
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        logging.error(f"Stripe Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment_success", response_class=HTMLResponse)
def payment_success(session_id: str, request: Request):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            data = session.metadata
            
            # Save ticket & Generate QR
            ticket_id = db_manager.add_ticket(
                event_id=int(data['event_id']),
                user_id=int(data['user_id']),
                user_name=data['user_name'],
                phone_number=data['phone_number']
            )
            event = db_manager.get_event_by_id(int(data['event_id']))
            qr_path = generate_qr_code(ticket_id, event['name'], data['user_name'])
            
            # Send to Telegram
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
        logging.error(f"Payment processing error: {e}")
        return f"Error processing payment: {e}"

@app.get("/payment_cancel")
def payment_cancel():
    return {"message": "Order canceled. You can close this window."}


# --- Automatic Reminder Logic ---

scheduler = AsyncIOScheduler()

def check_and_send_reminders():
    today = date.today().isoformat()
    logging.info(f"Scheduler running: checking for events on {today}")

    events = db_manager.get_events_by_date(today)
    if not events:
        logging.info("No events today.")
        return
    
    token = os.getenv("TELEGRAM_TOKEN")
    for event in events:
        logging.info(f"Found event: {event['name']}! Sending reminders...")
        user_ids = db_manager.get_users_with_tickets_for_event(event["id"])

        for user_id in user_ids:
            try:
                msg = (
                    f"Today is the day!\n\n"
                    f"Get ready! **{event['name']}** is happening today.\n"
                    f"Location: {event['location']}\n\n"
                    f"See you there!"
                )
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                    "chat_id": user_id, 
                    "text": msg, 
                    "parse_mode": "Markdown"
                })
            except Exception as e:
                logging.error(f"Failed to send reminder to {user_id}: {e}")

@app.on_event("startup")
def start_scheduler():
    # Option A: Run once immediately when server starts (For Testing)
    # asyncio.create_task(check_and_send_reminders()) 
    
    # Option B: Run every day at 10:00 AM (Production)
    scheduler.add_job(check_and_send_reminders, 'cron', hour=10, minute=0)
    
    # Option C: Run every 60 seconds (For Demo/Testing now)
    # scheduler.add_job(check_and_send_reminders, 'interval', seconds=60)
    
    scheduler.start()
    logging.info("✅ Scheduler started")


# --- Helpers ---

def generate_qr_code(ticket_id: int, event_name: str, user_name: str):
    if not os.path.exists("static"):
        os.makedirs("static")
    data = f"TICKET-ID:{ticket_id} | EVENT:{event_name} | OWNER:{user_name}"
    qr = qrcode.make(data)
    file_path = f"static/ticket_{ticket_id}.png"
    qr.save(file_path)
    return file_path

def send_ticket_to_telegram(chat_id, file_path, caption):
    bot_token = os.getenv("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(file_path, "rb") as image_file:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": image_file})