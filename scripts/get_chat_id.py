import os
import requests
from mansur_bot.config import load_project_env

# Load token from .env
load_project_env()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_chat_id():
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        return

    print(f"🔍 Checking for messages to Bot...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Error from Telegram: {data}")
            return

        results = data.get('result', [])
        if not results:
            print("⚠️ No messages found! Please send 'Hello' to your bot on Telegram and run this again.")
            return

        # Get the chat ID from the last message
        last_message = results[-1]
        chat = last_message['message']['chat']
        chat_id = chat['id']
        first_name = chat.get('first_name', 'User')
        
        print("\n✅ SUCCESS! Found Chat ID:")
        print(f"👉 {chat_id}")
        print(f"Name: {first_name}")
        print("\nAdd this to your .env file:\nTELEGRAM_CHAT_ID=" + str(chat_id))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_chat_id()
