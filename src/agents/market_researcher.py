from typing import Dict, Any, List
from langchain_core.tools import tool
try:
    from googlesearch import search
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    pass # Handle cases where deps might not be installed in CI/CD or minimal envs

from src.integration.llm_client import query_llm

def perform_market_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Market Researcher Node.
    Uses web search to find current market sentiment/events.
    """
    print("--- [Market Researcher] Searching Web for Live Intel ---")
    
    raw_data = ""
    
    try:
        # 1. Google Search for top headlines
        query = "Nifty 50 live market sentiment news india"
        print(f"Searching Google for: {query}")
        
        search_results = []
        try:
            # Fetch top 5 results
            for result_url in search(query, num_results=5, advanced=True):
                search_results.append(result_url)
        except Exception as e:
            print(f"Google Search failed: {e}")

        # 2. Scrape Specific News Sources (Simplified Scraper)
        headlines = []
        
        # Helper to scrape
        def scrape_headlines(url, source_name):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Simple logic to find main headings (this varies by site and is brittle)
                # Just grabbing title and some h1/h2 tags for now as a generic approach
                page_title = soup.title.string if soup.title else ""
                headlines.append(f"{source_name}: {page_title.strip()}")
                
                # Attempt to find article highlights (very generic)
                texts = [h.get_text().strip() for h in soup.find_all(['h1', 'h2'], limit=3)]
                for t in texts:
                    if len(t) > 20:
                        headlines.append(f"{source_name} Head: {t}")
                        
            except Exception as e:
                print(f"Failed to scrape {source_name}: {e}")

        # Scrape MoneyControl (Market Section)
        scrape_headlines("https://www.moneycontrol.com/news/business/markets/", "MoneyControl")
        
        # Scrape MarketWatch (Generic or Asia specific)
        scrape_headlines("https://www.marketwatch.com/latest-news", "MarketWatch")
        
        # Scrape Investing.com India
        scrape_headlines("https://in.investing.com/news/stock-market-news", "Investing.com")

        # Compile results
        if search_results:
             raw_data += f"Top Search Links: {', '.join([r.title for r in search_results])}\n"
             # Add descriptions from search results
             for r in search_results:
                 raw_data += f"- {r.description}\n"
        
        if headlines:
            raw_data += "\nDirect Site Headlines:\n" + "\n".join([f"- {h}" for h in headlines])
            
        if not raw_data:
             raw_data = "Could not fetch live data."
             
    except Exception as e:
        print(f"Market Research Error: {e}")
        raw_data = f"Error performing market research: {str(e)}"

    print(f"Raw Research Data (first 200 chars): {raw_data[:200]}...")
    
    # 3. Summarize with LLM
    print("--- [Market Researcher] Synthesizing with LLM (Llama 3) ---")
    system_prompt = (
        "You are a senior financial market analyst for the Indian Stock Market (Nifty 50). "
        "Your job is to summarize the provided raw news headlines and search results into a concise market sentiment report. "
        "Focus on: Volatility (VIX), FII/DII activity, Global Cues, and Major Domestic Events. "
        "Conclude with a Sentiment Tag: 'Bullish', 'Bearish', 'Neutral', or 'Volatile'."
    )
    user_prompt = f"Raw Market Data:\n{raw_data}"
    
    try:
        # Use Llama 3 via Groq for fast synthesis
        research_summary = query_llm(system_prompt, user_prompt, provider="groq", model="llama-3.3-70b-versatile")
    except Exception as e:
        print(f"LLM Summarization Failed: {e}")
        research_summary = f"LLM Error. Raw Data: {raw_data}"
    
    print(f"LLM Summary: {research_summary}")
    
    return {"research_data": research_summary}
