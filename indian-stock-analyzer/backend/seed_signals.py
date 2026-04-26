from __future__ import annotations

import os
import asyncio
from dotenv import load_dotenv
from main import build_stock_payload, fetcher
from zapier_webhook import send_alert

load_dotenv()

def seed_now():
    print("🚀 Seeding automated signals to Telegram...")
    
    # Get Nifty 50 and Bank Nifty symbols
    symbols = fetcher.get_nifty50_symbols() + fetcher.get_banknifty_symbols()
    symbols = list(set(symbols)) # Unique symbols
    
    found_signals = 0
    for symbol in symbols:
        try:
            print(f"Analyzing {symbol}...")
            stock = build_stock_payload(symbol)
            signal = stock["signal"]
            
            # If it's a BUY or SELL signal, send it immediately
            if any(s in signal for s in ["BUY", "SELL"]) and "HOLD" not in signal:
                print(f"✅ Found signal for {symbol}: {signal}. Sending to Telegram...")
                send_alert(
                    symbol, 
                    signal, 
                    stock.get("price") or 0.0, 
                    stock["confidence"], 
                    stock["reasons"]
                )
                found_signals += 1
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")

    if found_signals == 0:
        print("⚠️ No strong BUY/SELL signals found at this moment. Sending a status update instead.")
        # Send a heartbeat message to verify bot is working
        from zapier_webhook import _send_telegram
        _send_telegram({
            "stock": "SYSTEM",
            "signal": "ONLINE 📡",
            "price": "N/A",
            "confidence": 100,
            "time": "Just Now",
            "reasons": ["Automated scanner is active.", "Monitoring Nifty 50 & Bank Nifty.", "No strong signals detected in the last scan."]
        })
    else:
        print(f"✨ Successfully seeded {found_signals} signals to Telegram.")

if __name__ == "__main__":
    seed_now()
