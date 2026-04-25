# Indian Stock Analyzer (Free)

Full-stack Nifty50 + BankNifty analyzer using only free APIs/tools.

## Stack

- Backend: FastAPI, yfinance, NSE unofficial API, pandas-ta, VADER, APScheduler
- Frontend: React + Vite + Tailwind CSS + lightweight-charts + axios + Firebase Web Push
- Alerts: Firebase Cloud Messaging (FCM) + CallMeBot + optional Zapier webhook
- MCP: custom `indian-stock-analyzer` server + Zapier MCP

## Project Structure

See `backend/` for API/data engine, `frontend/` for dashboard UI, `zapier_webhook.py` for outgoing alerts.

## Setup

1. Copy env template:
   - `cp .env.example .env` (or create `.env` manually on Windows)
2. Install dependencies:
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
3. Run backend:
   - `cd backend && uvicorn main:app --reload --port 8000`
4. Run frontend:
   - `cd frontend && npm run dev`
5. Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

- `GET /api/indices`
- `GET /api/stocks`
- `GET /api/stock/{symbol}`
- `GET /api/news`
- `GET /api/signals/top`
- `GET /api/banknifty`
- `POST /api/fcm/register`
- `POST /api/fcm/test`
- `WS /ws/live`

## Notes

- Data fetch is cached in memory for 5 minutes.
- NSE calls use browser-like headers + session cookies.
- Uses IST market hours (Mon-Fri, 9:15 AM to 3:30 PM).
- Sentiment defaults to VADER and is fully free.

## MCP Config

MCP server definitions are in `.cursor/mcp.json`.

## Notifications Setup (FCM + CallMeBot)

### Step 1: Firebase setup (free)
1. Create Firebase project: `indian-stock-analyzer`
2. Add a Web app and copy the config values
3. Cloud Messaging -> generate Web Push VAPID key
4. Service Accounts -> generate private key JSON
5. Save JSON as `backend/firebase-service-account.json`

### Step 2: Backend env
Add to `.env`:
- `FIREBASE_PROJECT_ID=indian-stock-analyzer`
- `FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json`
- `CALLMEBOT_PHONE=91XXXXXXXXXX`
- `CALLMEBOT_APIKEY=XXXXXXX`

### Step 3: Frontend env
Create `frontend/.env` with:
- `VITE_FIREBASE_API_KEY=...`
- `VITE_FIREBASE_AUTH_DOMAIN=indian-stock-analyzer.firebaseapp.com`
- `VITE_FIREBASE_PROJECT_ID=indian-stock-analyzer`
- `VITE_FIREBASE_STORAGE_BUCKET=indian-stock-analyzer.appspot.com`
- `VITE_FIREBASE_MESSAGING_SENDER_ID=...`
- `VITE_FIREBASE_APP_ID=...`
- `VITE_FIREBASE_VAPID_KEY=...`

### Step 4: Run and verify
- `make setup`
- `make dev`
- Open frontend, allow notifications, then call `POST /api/fcm/test`.

## Bot Commands

- `HELP` -> show all commands
- `NIFTY` -> Nifty 50 price + summary
- `BANKNIFTY` / `BNF` -> BankNifty + component signals
- `SIGNAL <STOCK>` -> full analysis
- `BUY <STOCK>` / `SELL <STOCK>` -> directional check
- `<STOCK>` -> quick quote + signal
- `TOP5` -> top 5 BUY signals
- `WORST5` -> top 5 SELL signals
- `NEWS <STOCK>` / `NEWS NIFTY` -> news + sentiment
- `MARKET` / `STATUS` -> market open/close status
- `ALERT ON` / `ALERT OFF` -> toggle push alerts

## Local Bot Test

Run:
- `cd backend && python test_bot.py`

