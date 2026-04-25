from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

from fetcher import BANKNIFTY_SYMBOLS as BANKNIFTY_LIST, NIFTY_50_SYMBOLS
from indicators import calculate_indicators
from news import fetch_market_news, fetch_news_for_topic
from sentiment import score_articles
from signals import generate_signal

IST = ZoneInfo("Asia/Kolkata")
ALERT_STATUS_FILE = Path(__file__).resolve().parent / "alert_status.txt"
NIFTY50_SYMBOLS = NIFTY_50_SYMBOLS
BANKNIFTY_SYMBOLS = BANKNIFTY_LIST


def _hist_to_ohlcv(hist):
    out = []
    for idx, row in hist.iterrows():
        out.append(
            {
                "time": idx.to_pydatetime().astimezone(IST).isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        )
    return out


def _safe_history(ticker_symbol: str, period: str = "3mo"):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        return ticker, hist
    except Exception:
        return None, None


def _ema_trend(ind: dict) -> str:
    e20, e50, e200 = ind.get("ema20"), ind.get("ema50"), ind.get("ema200")
    if None in (e20, e50, e200):
        return "Neutral"
    if e20 > e50 > e200:
        return "Bullish"
    if e20 < e50 < e200:
        return "Bearish"
    return "Neutral"


def _macd_bullish(ind: dict) -> bool:
    m, s = ind.get("macd"), ind.get("macd_signal")
    return m is not None and s is not None and m > s


def _volume_signal(ind: dict) -> str:
    v, avg = ind.get("volume"), ind.get("avg_volume")
    if v is None or avg in (None, 0):
        return "Normal"
    return "High" if v > avg * 1.5 else "Normal"


def _market_news_for_symbol(sym: str):
    if sym in ("NIFTY", "NIFTY50"):
        return fetch_market_news()["NIFTY50"]
    if sym in ("BANKNIFTY", "BNF"):
        return fetch_market_news()["BANKNIFTY"]
    return fetch_news_for_topic(f"{sym} NSE India stock", limit=5)


def handle_command(cmd: str) -> str:
    parts = cmd.strip().split()
    base = parts[0] if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    routes = {
        "HELP": cmd_help,
        "BUY": lambda: cmd_stock_signal(arg, expected="BUY"),
        "SELL": lambda: cmd_stock_signal(arg, expected="SELL"),
        "SIGNAL": lambda: cmd_stock_signal(arg, expected="ALL"),
        "NIFTY": cmd_nifty,
        "BANKNIFTY": cmd_banknifty,
        "BNF": cmd_banknifty,
        "TOP5": cmd_top5_buy,
        "TOP": cmd_top5_buy,
        "WORST5": cmd_top5_sell,
        "NEWS": lambda: cmd_news(arg),
        "ALERT": lambda: cmd_alert(arg),
        "MARKET": cmd_market_status,
        "STATUS": cmd_market_status,
        "WATCHLIST": cmd_watchlist,
        "PORTFOLIO": cmd_portfolio_summary,
    }
    handler = routes.get(base)
    if handler:
        try:
            return handler()
        except Exception as e:
            return f"❌ Error processing {base}: {str(e)[:100]}\n\nTry: HELP"
    if base in NIFTY50_SYMBOLS or base in BANKNIFTY_SYMBOLS:
        return cmd_stock_signal(base, expected="ALL")
    return cmd_help()


def cmd_help() -> str:
    return """🤖 *NSE Stock Bot* — Commands:

📈 *Stock Analysis:*
- `SIGNAL RELIANCE` — full analysis
- `BUY TCS` — buy signal check
- `SELL HDFCBANK` — sell signal check
- `RELIANCE` — quick quote + signal

📊 *Indices:*
- `NIFTY` — Nifty 50 analysis
- `BANKNIFTY` or `BNF` — BankNifty analysis
- `MARKET` — market open/close status

🏆 *Top Picks:*
- `TOP5` — top 5 buy signals now
- `WORST5` — top 5 sell signals now

📰 *News:*
- `NEWS INFY` — latest news + sentiment
- `NEWS NIFTY` — market news

🔔 *Alerts:*
- `ALERT ON` — auto push alerts
- `ALERT OFF` — stop auto alerts

_Data: NSE India · Yahoo Finance · Google News_
_Signals: RSI · MACD · EMA · Bollinger · Sentiment_"""


def cmd_stock_signal(symbol: str, expected: str = "ALL") -> str:
    if not symbol:
        return "❌ Please provide a stock symbol.\nExample: SIGNAL RELIANCE"
    sym = symbol.upper().replace(".NS", "")
    ticker, hist = _safe_history(f"{sym}.NS", period="3mo")
    if ticker is None or hist is None or hist.empty:
        return f"❌ Could not fetch data for {sym}. Check the symbol."

    ohlcv = _hist_to_ohlcv(hist)
    ind = calculate_indicators(ohlcv)
    sentiment = score_articles(_market_news_for_symbol(sym))
    sig = generate_signal(ind, sentiment)
    if expected == "BUY" and "BUY" not in sig["signal"]:
        return f"⚠️ *{sym}* is not a BUY right now.\nCurrent signal: *{sig['signal']}* ({sig['confidence']}%)"
    if expected == "SELL" and "SELL" not in sig["signal"]:
        return f"⚠️ *{sym}* is not a SELL right now.\nCurrent signal: *{sig['signal']}* ({sig['confidence']}%)"

    current = round(float(hist["Close"].iloc[-1]), 2)
    prev = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else current
    chg = round(current - prev, 2)
    pct = round((chg / prev) * 100, 2) if prev else 0.0
    sig_emoji = "🟢" if "BUY" in sig["signal"] else ("🔴" if "SELL" in sig["signal"] else "⏸️")
    change_emoji = "📈" if chg >= 0 else "📉"
    sent_score = sentiment.get("score", 0.0)
    sent_emoji = "🟢" if sent_score > 0.05 else ("🔴" if sent_score < -0.05 else "⚪")
    rsi = round(ind.get("rsi", 0) or 0, 1)
    rsi_note = "Oversold" if rsi < 30 else ("Overbought" if rsi > 70 else "Neutral")

    return f"""{sig_emoji} *{sym}* — {sig['signal']} ({sig['confidence']}%)

💰 Price: ₹{current} {change_emoji} {'+' if chg >= 0 else ''}{chg} ({'+' if pct >= 0 else ''}{pct}%)

📊 *Indicators:*
- RSI: {rsi} ({rsi_note})
- MACD: {'Bullish ▲' if _macd_bullish(ind) else 'Bearish ▼'}
- EMA Trend: {_ema_trend(ind)}
- Volume: {_volume_signal(ind)}

{sent_emoji} *News Sentiment:* {sentiment.get('sentiment', 'Neutral')} ({round(sent_score * 100)}%)

💡 *Reasons:*
{chr(10).join(['• ' + r for r in sig['reasons'][:4]]) if sig['reasons'] else '• No strong confluence yet'}

⏰ {datetime.now(IST).strftime('%d %b %Y %H:%M IST')}"""


def cmd_nifty() -> str:
    ticker, hist = _safe_history("^NSEI", period="5d")
    if ticker is None or hist is None or hist.empty:
        return "❌ Could not fetch Nifty data right now."
    current = round(float(hist["Close"].iloc[-1]), 2)
    prev = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else current
    change = round(current - prev, 2)
    pct = round((change / prev) * 100, 2) if prev else 0.0
    week_high = round(float(hist["High"].max()), 2)
    week_low = round(float(hist["Low"].min()), 2)
    return f"""📊 *NIFTY 50*

💰 {current:,.2f} {'📈' if change >= 0 else '📉'} {'+' if change >= 0 else ''}{change} ({'+' if pct >= 0 else ''}{pct}%)
📅 5D High: {week_high:,.2f}  Low: {week_low:,.2f}

🔔 Send *TOP5* for top Nifty buy signals
🔔 Send *NEWS NIFTY* for market news
⏰ {datetime.now(IST).strftime('%d %b %H:%M IST')}"""


def cmd_banknifty() -> str:
    _, hist = _safe_history("^NSEBANK", period="5d")
    if hist is None or hist.empty:
        return "❌ Could not fetch BankNifty data right now."
    current = round(float(hist["Close"].iloc[-1]), 2)
    prev = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else current
    change = round(current - prev, 2)
    pct = round((change / prev) * 100, 2) if prev else 0.0
    bank_signals = []
    for sym in BANKNIFTY_SYMBOLS[:10]:
        _, sh = _safe_history(f"{sym}.NS", period="1mo")
        if sh is None or sh.empty:
            continue
        sig = generate_signal(calculate_indicators(_hist_to_ohlcv(sh)), {"score": 0, "sentiment": "Neutral"})
        emoji = "🟢" if "BUY" in sig["signal"] else ("🔴" if "SELL" in sig["signal"] else "⚪")
        bank_signals.append(f"{emoji} {sym}: {sig['signal']}")
    bank_str = "\n".join(bank_signals) if bank_signals else "Loading..."
    return f"""🏦 *BANKNIFTY*

💰 {current:,.2f} {'📈' if change >= 0 else '📉'} {'+' if change >= 0 else ''}{change} ({'+' if pct >= 0 else ''}{pct}%)

📊 *Component Signals:*
{bank_str}

⏰ {datetime.now(IST).strftime('%d %b %H:%M IST')}"""


def _top_for(kind: str) -> list[tuple[str, str, int, float]]:
    results = []
    for sym in NIFTY50_SYMBOLS:
        _, hist = _safe_history(f"{sym}.NS", period="1mo")
        if hist is None or hist.empty:
            continue
        ind = calculate_indicators(_hist_to_ohlcv(hist))
        sig = generate_signal(ind, {"score": 0, "sentiment": "Neutral"})
        if kind in sig["signal"]:
            price = round(float(hist["Close"].iloc[-1]), 2)
            results.append((sym, sig["signal"], int(sig["confidence"]), price))
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:5]


def cmd_top5_buy() -> str:
    top5 = _top_for("BUY")
    if not top5:
        return "📊 No strong BUY signals right now. Market may be bearish."
    lines = [f"{i}. {'🟢' if 'STRONG' in s else '✅'} *{sym}* ₹{p} — {s} ({c}%)" for i, (sym, s, c, p) in enumerate(top5, 1)]
    return f"""🏆 *Top 5 BUY Signals — Nifty 50*

{chr(10).join(lines)}

💡 Send `SIGNAL <stock>` for full analysis
⏰ {datetime.now(IST).strftime('%d %b %H:%M IST')}"""


def cmd_top5_sell() -> str:
    top5 = _top_for("SELL")
    if not top5:
        return "📊 No strong SELL signals right now. Market may be bullish."
    lines = [f"{i}. {'🔴' if 'STRONG' in s else '⚠️'} *{sym}* ₹{p} — {s} ({c}%)" for i, (sym, s, c, p) in enumerate(top5, 1)]
    return f"""⚠️ *Top 5 SELL Signals — Nifty 50*

{chr(10).join(lines)}

💡 Send `SIGNAL <stock>` for full analysis
⏰ {datetime.now(IST).strftime('%d %b %H:%M IST')}"""


def cmd_news(symbol: str = "") -> str:
    sym = symbol.upper() if symbol else "NIFTY"
    try:
        scored = score_articles(_market_news_for_symbol(sym)).get("articles", [])[:4]
    except Exception:
        scored = []
    if not scored:
        return f"📰 No recent news found for {sym}"
    lines = []
    for a in scored:
        score = a.get("score", 0.0)
        sent = "🟢" if score > 0.05 else ("🔴" if score < -0.05 else "⚪")
        lines.append(f"{sent} {a.get('title', '')[:80]}")
    return f"""📰 *News: {sym}*

{chr(10).join(lines)}

⏰ {datetime.now(IST).strftime('%d %b %H:%M IST')}"""


def cmd_market_status() -> str:
    now = datetime.now(IST)
    wd, h, m = now.weekday(), now.hour, now.minute
    is_open = wd < 5 and ((h > 9 or (h == 9 and m >= 15)) and (h < 15 or (h == 15 and m <= 30)))
    if is_open:
        status, msg = "🟢 OPEN", "NSE market is currently trading."
    elif wd >= 5:
        status, msg = "🔴 CLOSED", "Weekend — market opens Monday 9:15 AM IST"
    elif h < 9 or (h == 9 and m < 15):
        status, msg = "🟡 PRE-MARKET", "Market opens at 9:15 AM IST"
    else:
        status, msg = "🔴 CLOSED", "Market closed at 3:30 PM. Opens tomorrow 9:15 AM IST"
    return f"""📊 *Market Status*

{status}
{msg}

🕐 Current IST: {now.strftime('%d %b %Y %H:%M')}

Send *NIFTY* or *BANKNIFTY* for latest data."""


def cmd_alert(arg: str) -> str:
    value = (arg or "").strip().upper()
    if value in ("ON", "OFF"):
        ALERT_STATUS_FILE.write_text(value, encoding="utf-8")
        return (
            "🔔 *Alerts ENABLED*\n\nYou'll now receive automatic WhatsApp pushes."
            if value == "ON"
            else "🔕 Alerts DISABLED. Send *ALERT ON* to re-enable."
        )
    status = ALERT_STATUS_FILE.read_text(encoding="utf-8").strip() if ALERT_STATUS_FILE.exists() else "OFF"
    return f"🔔 Alerts are currently *{status}*\nSend *ALERT ON* or *ALERT OFF*"


def cmd_watchlist() -> str:
    return """📋 *Your Watchlist*

To add to watchlist, send:
`WATCH ADD RELIANCE`
`WATCH REMOVE TCS`
`WATCH LIST`

_(Watchlist feature — coming in next update)_"""


def cmd_portfolio_summary() -> str:
    return """💼 *Portfolio Tracker*

Send your holdings like:
`PORT ADD RELIANCE 100 2450`
(stock, qty, buy price)

Then `PORTFOLIO` shows P&L.

_(Portfolio feature — coming in next update)_"""
