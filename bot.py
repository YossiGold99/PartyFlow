import os
import telebot 
import requests
import phonenumbers 
import qrcode 
import logging
from io import BytesIO 
from telebot import types  
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Configuration & Setup ---

# 1. Configure Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 2. Load secrets from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

# 3. Check if token exists
if not TELEGRAM_TOKEN:
    logging.error("No TELEGRAM_TOKEN found in .env file")
    exit()

# 4. Initialize the bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
logging.info("Bot is running...")

# Temporary dictionary to store data (In production, use Redis or DB)
user_data = {}


# --- Standard commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to PartyFlow! 🥳\nUse /events to see upcoming parties.\nUse /my_tickets to view your tickets.")

@bot.message_handler(commands=['events'])
def list_events(message):
    try:
        if not API_URL:
            bot.reply_to(message, "Error: API_URL is missing.")
            return
        
        response = requests.get(f"{API_URL}/events")

        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])

            if not events:
                bot.reply_to(message, "No upcoming parties found")
                return

            bot.send_message(message.chat.id, "🎉 **Upcoming Parties:** 👇")

            for event in events:
                event_text = (
                    f"🎈 **{event['name']}**\n"
                    f"📍 {event['location']} | 📅 {event['date']}\n"
                    f"💰 Price: {event['price']} NIS"
                )

                markup = types.InlineKeyboardMarkup()
                buy_button = types.InlineKeyboardButton("🛒 Buy Ticket", callback_data=f"buy_{event['id']}")
                markup.add(buy_button)

                bot.send_message(message.chat.id, event_text, reply_markup=markup, parse_mode="markdown")

        else:
            bot.reply_to(message, f"Server Error: {response.status_code}")

    except Exception as e:
        bot.reply_to(message, f"Connection failed: {e}")


# --- Command: View My Tickets ---

@bot.message_handler(commands=['my_tickets'])
def my_tickets(message):
    chat_id = message.chat.id
    
    try:
        if not API_URL:
            bot.reply_to(message, "Configuration Error: API_URL missing.")
            return

        # Request tickets from server
        response = requests.get(f"{API_URL}/api/tickets/{chat_id}")
        
        if response.status_code == 200:
            data = response.json()
            tickets = data.get('tickets', [])
            
            if not tickets:
                bot.reply_to(message, "You don't have any tickets yet. Type /events to buy one! 🎟️")
                return
            
            bot.send_message(chat_id, f"🎫 Found {len(tickets)} ticket(s):")
            
            for ticket in tickets:
                caption = (
                    f"🎟️ **Ticket #{ticket['id']}**\n"
                    f"🎉 Event: {ticket['name']}\n" 
                    f"📅 Date: {ticket['date']}\n"
                    f"📍 Location: {ticket['location']}"
                )
                
                # Generate QR Code
                qr_data = f"TICKET-ID:{ticket['id']} | OWNER:{chat_id}"
                qr_img = qrcode.make(qr_data)
                
                # Save to memory buffer
                bio = BytesIO()
                qr_img.save(bio, 'PNG')
                bio.seek(0)
                
                # Send photo
                bot.send_photo(chat_id, bio, caption=caption, parse_mode="markdown")
                
        else:
            bot.reply_to(message, "Error fetching tickets from server.")
            
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


# --- Smart Registration Flow ---

# Step 1: User clicks "buy"
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def ask_name(call):
    chat_id = call.message.chat.id
    event_id = int(call.data.split('_')[1])

    user_data[chat_id] = {'event_id': event_id}

    msg = bot.send_message(chat_id, "Great choice! 🎫\nWhat is your **Full Name**?")
    bot.register_next_step_handler(msg, ask_phone)

# Step 2: Save name and ask for phone
def ask_phone(message):
    chat_id = message.chat.id
    name = message.text

    user_data[chat_id]['name'] = name

    msg = bot.send_message(chat_id, f"Nice to meet you, {name}! 👋\nNow, please enter your **Phone Number**:")
    
    bot.register_next_step_handler(msg, validate_phone) 

# Step 3: Validate the phone number
def validate_phone(message):
    chat_id = message.chat.id
    phone_input = message.text
    
    try:
        # 1. Parse number (Assuming Israel)
        parsed_number = phonenumbers.parse(phone_input, "IL")
        
        # 2. Check if valid
        if not phonenumbers.is_valid_number(parsed_number):
            msg = bot.send_message(chat_id, "❌ Invalid number. Please try again (e.g., 0501234567):")
            bot.register_next_step_handler(msg, validate_phone) 
            return

        # 3. Format nicely
        formatted_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        
        # Save valid phone and proceed
        finalize_order(message, formatted_phone)

    except phonenumbers.NumberParseException:
        msg = bot.send_message(chat_id, "❌ That doesn't look like a phone number. Try again:")
        bot.register_next_step_handler(msg, validate_phone)

# Step 4: Finalize purchase with server
def finalize_order(message, valid_phone):
    chat_id = message.chat.id
    
    current_user = user_data.get(chat_id)
    if not current_user:
        bot.send_message(chat_id, "Session expired. Please use /start again.")
        return

    payload = {
        "event_id": current_user['event_id'],
        "user_name": current_user['name'],
        "user_id": chat_id,
        "phone_number": valid_phone
    }
    
    bot.send_message(chat_id, "Generating payment link... 💳")
    
    try:
        response = requests.post(f"{API_URL}/create_checkout_session", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            payment_url = data.get('checkout_url')
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("👉 Click to Pay Now 👈", url=payment_url))
            
            bot.send_message(chat_id, "Ticket reserved! Please complete payment:", reply_markup=markup)
            
        elif response.status_code == 400:
            bot.send_message(chat_id, "⚠️ Sorry, this event is SOLD OUT!")
        else:
            bot.send_message(chat_id, "❌ Error generating payment link.")
            
    except Exception as e:
        bot.send_message(chat_id, f"Connection Error: {e}")
    
    user_data.pop(chat_id, None)


# 5. Start the bot
bot.infinity_polling()