import os
import requests
import sys
from mansur_bot.config import load_project_env

load_project_env()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_file(file_path):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Error: Credentials missing in .env")
        return

    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID}
            response = requests.post(url, data=data, files=files)
            
        if response.status_code == 200:
            print(f"✅ Successfully sent: {file_path}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_file.py <path_to_file>")
    else:
        file_to_send = sys.argv[1]
        send_file(file_to_send)
