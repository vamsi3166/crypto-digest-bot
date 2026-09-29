import os
import requests
import feedparser
from datetime import datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]  # e.g. "@yourchannelname" or a numeric channel ID
COINGECKO_API_KEY = os.environ["COINGECKO_API_KEY"]  # free "Demo" key from coingecko.com

NEWS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]


def get_market_movers():
    """Fetch top crypto gainers/losers from CoinGecko (free, no API key needed)."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "price_change_percentage": "24h",
    }
    headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    coins = resp.json()

    coins = [c for c in coins if c.get("price_change_percentage_24h") is not None]
    sorted_coins = sorted(coins, key=lambda c: c["price_change_percentage_24h"], reverse=True)

    gainers = sorted_coins[:3]
    losers = sorted_coins[-3:]

    def fmt(c):
        return f"• {c['symbol'].upper()}: ${c['current_price']:,} ({c['price_change_percentage_24h']:+.2f}%)"

    return {
        "gainers": [fmt(c) for c in gainers],
        "losers": [fmt(c) for c in losers],
    }


def get_top_headlines(limit=6):
    """Pull recent headlines from a couple of crypto news RSS feeds."""
    headlines = []
    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                headlines.append(f"• {entry.title}")
        except Exception as e:
            print(f"Failed to parse feed {feed_url}: {e}")
    return headlines[:limit]


def build_digest(market_data, headlines):
    """Format raw data directly into a readable message - no AI involved."""
    today = datetime.utcnow().strftime("%B %d, %Y")

    message = f"📊 <b>Daily Crypto Digest</b> — {today}\n\n"
    message += "<b>📈 Top Gainers (24h)</b>\n"
    message += "\n".join(market_data["gainers"]) + "\n\n"
    message += "<b>📉 Top Losers (24h)</b>\n"
    message += "\n".join(market_data["losers"]) + "\n\n"
    message += "<b>📰 Latest Headlines</b>\n"
    message += "\n".join(headlines) + "\n\n"
    message += "<i>Not financial advice.</i>"

    return message


def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    resp = requests.post(url, data=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    market_data = get_market_movers()
    headlines = get_top_headlines()
    digest = build_digest(market_data, headlines)
    result = send_to_telegram(digest)
    print("Message sent successfully:", result.get("ok"))


if __name__ == "__main__":
    main()
