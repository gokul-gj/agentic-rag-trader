from typing import Dict, Any
from src.integration.llm_client import query_llm
import json

def validate_order(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Risk Manager Node.
    Validates the proposed order against safety checks using LLM reasoning.
    """
    print("--- [Risk Manager] Validating Order with LLM ---")
    order = state.get("final_order", {})
    market_data = state.get("market_data", {})
    market_sentiment = state.get("research_data", "No sentiment data")
    
    if not order:
        return {"error": "No order to validate."}
    
    # Construct Prompt
    system_prompt = (
        "You are a strict Risk Manager for an options trading desk. "
        "Your goal is to PROTECT CAPITAL. You must validate the proposed trade against current market conditions. "
        "Rules: "
        "1. Do not sell options if IV is extremely low (<11%) as risk/reward is poor. "
        "2. Reject trades if Market Sentiment is 'Volatile' but the strategy is 'Short Strangle' (delta risk). "
        "3. Ensure the trade makes sense given the Nifty Spot price. "
        "Output JSON: {'decision': 'approved' or 'rejected', 'reason': '...'}"
    )
    
    user_prompt = f"""
    Market Data:
    - Spot Price: {market_data.get('spot_price')}
    - IV: {market_data.get('iv')}%
    - Sentiment: {market_sentiment}
    
    Proposed Order:
    {json.dumps(order, indent=2)}
    
    Approve or Reject?
    """
    
    try:
        # Use Llama 3 via Groq logic for "Second Opinion"
        # Since Strategist used GPT-4, we audit with Llama 3
        llm_response = query_llm(system_prompt, user_prompt, provider="groq", model="llama-3.3-70b-versatile")
        
        print(f"Risk Manager Thoughts: {llm_response}")
        
        # Simple parsing logic (robustness would require JSON parser)
        decision = "approved"
        if "rejected" in llm_response.lower():
            decision = "rejected"
            
        return {
            "risk_status": decision,
            "risk_analysis": llm_response
        }
        
    except Exception as e:
        print(f"Risk Manager LLM Failed: {e}")
        # Fail safe: Reject if unsure
        return {"risk_status": "rejected", "risk_analysis": "LLM Failure"}
