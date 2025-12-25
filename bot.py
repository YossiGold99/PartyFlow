import os
import telebot
import requests
from telebot import types 
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. Load secrets from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

# 2.Check if token exists
if not TELEGRAM_TOKEN:
    print("Error: No TELEGRAM_TOKEN found in .env file")
    exit()

# 3. Initialize the bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print("Bot is running...")

# Temporary dictionary to store data during the registration flow
# Structure: {chat_id: {'event_id': 1, 'name': 'Yossi'}}
user_data = {}

# --- Standard commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to PartyFlow! 🥳\nUse /events to see upcoming parties.")

@bot.message_handler(commands=['events'])
def list_events(message):
    try:
        # Check if API_URL is defined
        if not API_URL:
            bot.reply_to(message, "Error: API_URL is missing.")
            return
        
        # Send request to the server 
        response = requests.get(f"{API_URL}/events")

        if response.status_code == 200:
            data = response.json()
            events=data.get('events', [])

            if not events:
                bot.reply_to(message, "No upcoming parties found")
                return

            bot.send_message(message.chat.id, "🎉 **Upcoming Parties:** 👇")

            for event in events:
                # Create the event text
                event_text = (
                    f"🎈 **{event['name']}**\n"
                    f"📍 {event['location']} | 📅 {event['date']}\n"
                    f"💰 Price: {event['price']} NIS"
                )

                # Create the button
                markup = types.InlineKeyboardMarkup()
                # the button stores the party ID inthe callback_data
                buy_button = types.InlineKeyboardButton("🛒 Buy Ticket", callback_data=f"buy_{event['id']}")
                markup.add(buy_button)

                # Send message with the button
                bot.send_message(message.chat.id, event_text, reply_markup=markup, parse_mode="markdown")

        else:
            bot.reply_to(message, f"Server Error: {response.status_code}")

    except Exception as e:
        bot.reply_to(message, f"Connection failed: {e}")

# --- Smart Registration FLow ---

# 1. User clicks the "buy" button
@bot.callback_query_handler(func=lambda call:call.data.startswith("buy_"))
def ask_name(call):
    chat_id = call.message.chat.id
    # Extract event ID from callback data (e.g., "buy_3" -> 3)
    event_id = int(call.data.split('_')[1])

    # Initialize dictionary for this specific user
    user_data[chat_id] = {'event_id': event_id}

    # Ask for the user's name
    msg = bot.send_message(chat_id, "Great choice! 🎫\nWhat is your **Full Name**?")

    # Register the next step: tell the bot to pass the NEXT user message to 'step2_ask_phone'
    bot.register_next_step_handler(msg,ask_phone)

# 2. save name and ask for phone number
def ask_phone(message):
    chat_id = message.chat.id
    name = message.text

    # Save name in the temporary dictionary
    user_data[chat_id]['name'] = name

    msg = bot.send_message(chat_id, f"Nice to meet you, {name}! 👋\nNow, please enter your **Phone Number**:")

    # Register the next step
    bot.register_next_step_handler(msg, finalize_order)

# Step 3: Save phone and finalize purchase with the server
def finalize_order(message):
    chat_id = message.chat.id
    phone = message.text
    
    current_user = user_data.get(chat_id)
    if not current_user:
        bot.send_message(chat_id, "Session expired. Please use /start again.")
        return

    # Prepare payload for the checkout session
    payload = {
        "event_id": current_user['event_id'],
        "user_name": current_user['name'],
        "user_id": chat_id,
        "phone_number": phone
    }
    
    bot.send_message(chat_id, "Generating payment link... 💳")
    
    try:
        # Request payment URL from the server
        response = requests.post(f"{API_URL}/create_checkout_session", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            payment_url = data.get('checkout_url')
            
            # Create an inline button with the payment link
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("👉 Click to Pay Now 👈", url=payment_url))
            
            bot.send_message(chat_id, "Ticket reserved! Please complete payment:", reply_markup=markup)
            
        elif response.status_code == 400: # Handle Sold Out
            bot.send_message(chat_id, "⚠️ Sorry, this event is SOLD OUT!")
        else:
            bot.send_message(chat_id, "❌ Error generating payment link.")
            
    except Exception as e:
        bot.send_message(chat_id, f"Connection Error: {e}")
    
    # Clear user session
    user_data.pop(chat_id, None)

# 4. Start the bot
bot.infinity_polling()