from urllib.parse import quote_plus

# Broad market feeds. These carry general Indian market news and are NOT
# ticker-specific — they are ingested for market context, but articles from
# them are only linked to a ticker when they actually mention it.
RSS_FEEDS: dict[str, list[dict[str, str]]] = {
    "_default": [
        {
            "name": "MoneyControl",
            "url": "https://www.moneycontrol.com/rss/marketreports.xml",
        },
        {
            "name": "Economic Times Markets",
            "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        },
        {
            "name": "LiveMint Markets",
            "url": "https://www.livemint.com/rss/markets",
        },
        {
            "name": "NDTV Profit",
            "url": "https://feeds.feedburner.com/ndtvprofit-latest",
        },
    ],
}

NSE_EXCHANGE_SUFFIX = ".NS"
BSE_EXCHANGE_SUFFIX = ".BO"

TICKER_ALIASES: dict[str, list[str]] = {
    "RELIANCE": ["Reliance Industries", "RIL"],
    "TCS": ["Tata Consultancy", "Tata Consultancy Services"],
    "INFY": ["Infosys"],
    "HDFCBANK": ["HDFC Bank"],
    "ICICIBANK": ["ICICI Bank"],
    "HINDUNILVR": ["Hindustan Unilever", "HUL"],
    "ITC": ["ITC Limited"],
    "SBIN": ["State Bank of India", "SBI"],
    "BAJFINANCE": ["Bajaj Finance"],
    "BHARTIARTL": ["Bharti Airtel", "Airtel"],
    "KOTAKBANK": ["Kotak Mahindra Bank", "Kotak Bank"],
    "LT": ["Larsen & Toubro", "L&T"],
    "WIPRO": ["Wipro"],
    "HCLTECH": ["HCL Technologies", "HCL Tech"],
    "MARUTI": ["Maruti Suzuki"],
    "TATAMOTORS": ["Tata Motors"],
    "TATASTEEL": ["Tata Steel"],
    "AXISBANK": ["Axis Bank"],
    "SUNPHARMA": ["Sun Pharma", "Sun Pharmaceutical"],
    "ASIANPAINT": ["Asian Paints"],
}


def ticker_news_feeds(symbol: str, company_name: str | None = None) -> list[dict[str, str]]:
    """Build ticker-specific Google News RSS feeds for an NSE symbol.

    The broad market feeds above rarely carry enough coverage of any single
    stock, which starves retrieval and pushes confidence below the
    anti-hallucination threshold. A per-ticker news search gives the corpus
    articles that are actually about the company the user followed.
    """
    terms: list[str] = []

    # Prefer the full company name — "TCS" alone matches unrelated text.
    aliases = TICKER_ALIASES.get(symbol.upper(), [])
    if aliases:
        terms.append(aliases[0])
    if company_name and company_name.upper() != symbol.upper():
        cleaned = company_name.replace("Limited", "").replace("Ltd", "").strip()
        if cleaned and cleaned not in terms:
            terms.append(cleaned)
    if not terms:
        terms.append(symbol)

    feeds: list[dict[str, str]] = []
    for term in terms[:2]:
        query = quote_plus(f'"{term}" (stock OR share OR NSE OR results OR earnings)')
        feeds.append(
            {
                "name": f"Google News — {term}",
                "url": (f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"),
            }
        )
    return feeds
