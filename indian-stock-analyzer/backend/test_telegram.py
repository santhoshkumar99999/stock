import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print(f"🔍 Testing Telegram Connection...")
    print(f"Token: {token[:10]}... (truncated)")
    print(f"Chat ID: {chat_id}")
    
    if not token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in .env file!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ **Telegram Bot is Working!**\n\nYour Indian Stock Analyzer is now connected and ready to send automated Buy/Sell signals.",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("🚀 SUCCESS! Check your Telegram app, you should have received a message.")
        else:
            print(f"❌ Failed to send message. Telegram API returned: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    test_telegram()
