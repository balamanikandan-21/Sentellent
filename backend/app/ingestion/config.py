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
