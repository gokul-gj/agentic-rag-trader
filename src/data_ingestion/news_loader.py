import sys
import os

# Ensure src is in path
sys.path.append(os.getcwd())

from src.knowledge.vector_store import add_texts

def fetch_mock_news():
    """Simulates fetching relevant financial news."""
    return [
        {
            "headline": "RBI keeps repo rate unchanged, maintains neutral stance.",
            "source": "Financial Times",
            "sentiment": "neutral"
        },
        {
            "headline": "Global markets rally as inflation data cools down.",
            "source": "Bloomberg",
            "sentiment": "bullish"
        },
        {
            "headline": "Tech sell-off continues amid high valuation concerns.",
            "source": "Reuters",
            "sentiment": "bearish"
        }
    ]

def ingest_news():
    """Fetches news and stores it in the vector database."""
    print("Fetching news feeds...")
    news_items = fetch_mock_news()
    
    texts = []
    metadatas = []
    
    for item in news_items:
        # We store the headline + sentiment as the content
        content = f"News: {item['headline']} | Sentiment: {item['sentiment']}"
        texts.append(content)
        metadatas.append({"source": item['source'], "type": "news"})
        
    add_texts(texts, metadatas)
    print("News ingestion complete.")

if __name__ == "__main__":
    ingest_news()
