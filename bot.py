import os
import telebot
import requests
from dotenv import load_dotenv

# 1.load secrets from .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

# 2.check if token exists
if not TELEGRAM_TOKEN:
    print ("Error: No TELEGRAM_TOKEN found in .env file")
    exit()

# 3.initialize the bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print("bot is running...")

# --- Bot Commands ---

@bot.message_handler(commands= ['start'])
def send_welcome(message):
    bot.reply_to(message, "welcome to PartyFlow bot! \nUse /events to see upcoming parties.")

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
            # Use .get() to avoid crashing if 'events' key is missing
            events = data.get('events', [])
            
            if not events:
                bot.reply_to(message, "No upcoming parties found.")
                return
            
            # Build the message - note the f-string usage
            reply_text = "🎉 **Upcoming Parties:**\n\n"
            for event in events:
                # Add event name
                reply_text += f"🎈 {event['name']}\n"
                # Add location and date
                reply_text += f"📍 {event['location']} | 📅 {event['date']}\n"
                # Add price
                reply_text += f"💰 Price: {event['price']} NIS\n"
                # Add ID for purchase
                reply_text += f"🆔 ID: {event['id']}\n\n"
            
            bot.reply_to(message, reply_text)
        else:
            bot.reply_to(message, f"Server Error: {response.status_code}")
            
    except Exception as e:
        # Send exact error to Telegram for debugging
        bot.reply_to(message, f"Connection failed: {e}")

# 4.start the bot (infinite loop)
bot.infinity_polling()