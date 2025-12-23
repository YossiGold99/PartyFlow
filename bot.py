import os
import telebot
from telebot import types 
import requests
from dotenv import load_dotenv

# 1. Load secrets from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

# 2. Check if token exists
if not TELEGRAM_TOKEN:
    print("Error: No TELEGRAM_TOKEN found in .env file")
    exit()

# 3. Initialize the bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print("Bot is running...")

# --- Bot Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to PartyFlow bot! 🥳\nUse /events to see upcoming parties.")

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
            events = data.get('events', [])
            
            if not events:
                bot.reply_to(message, "No upcoming parties found.")
                return
            
            bot.send_message(message.chat.id, "🎉 **Upcoming Parties:** 👇")

            for event in events:
                # 1. Creating the text
                event_text = (
                    f"🎈 **{event['name']}**\n"
                    f"📍 {event['location']} | 📅 {event['date']}\n"
                    f"💰 Price: {event['price']} NIS"
                )
                
                #2. Creating the button
                markup = types.InlineKeyboardMarkup()
                buy_button = types.InlineKeyboardButton(
                    text="🛒 Buy Ticket", 
                    callback_data=f"buy_{event['id']}"
                )
                markup.add(buy_button)
                
                # 3. Sending the message with the button
                bot.send_message(message.chat.id, event_text, reply_markup=markup, parse_mode="Markdown")
            
        else:
            bot.reply_to(message, f"Server Error: {response.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"Connection failed: {e}")


# --- Handle Button Clicks ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy_click(call):
    try:
        # Extract event_id
        event_id = int(call.data.split('_')[1])
        user_id = call.from_user.id
        user_name = call.from_user.first_name or "Unknown"

        # Prepare data for the server
        payload = {
            "event_id": event_id,
            "user_id": user_id,
            "user_name": user_name
        }

        # Send POST request to buy ticket
        response = requests.post(f"{API_URL}/buy_ticket", json=payload)

        if response.status_code == 200:
            # Show a pop-up notification
            bot.answer_callback_query(call.id, "Ticket purchased successfully! ✅")
            # Send a confirmation message 
            bot.send_message(call.message.chat.id, f" You bought a ticket for Event ID: {event_id}!")
        else:
            bot.answer_callback_query(call.id, "Error: Could not buy ticket ❌")

    except Exception as e:
        print(f"Error processing callback: {e}")
        bot.answer_callback_query(call.id, "System Error occurred")

# 4. Start the bot
bot.infinity_polling()