from typing import Dict, Any
from src.knowledge.retrieval_tool import lookup_strategy_rules
from src.integration.llm_client import query_llm

def analyze_strategy(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Strategist Node.
    Analyzes the market state and queries the knowledge base for rules.
    """
    market_data = state.get("market_data", {})
    iv = market_data.get("iv", 0)
    
    print("--- [Strategist] Querying RAG for Short Strangle & Straddle Rules ---")
    strangle_rules = lookup_strategy_rules.invoke("Short Strangle management")
    straddle_rules = lookup_strategy_rules.invoke("Short Straddle management")
    
    print("--- [Strategist] Querying RAG for Market News ---")
    news = lookup_strategy_rules.invoke("market news")
    
    user_override = state.get("user_selected_strategy")
    
    if user_override:
         print(f"--- [Strategist] Manual Override Active: {user_override} ---")
         strategy = user_override
         rationale = f"User manually selected {user_override}."
         # Load constraints for selected strategy
         constraints = straddle_rules if user_override == "Short Straddle" else strangle_rules
         llm_response = "Manual Override. LLM analysis skipped."
    else: 
        # Use LLM to decide Strategy (Existing Logic)
        system_prompt = (
            "You are an expert options strategist. "
            "Decide between 'Short Strangle' (Range Bound) and 'Short Straddle' (Low Volatility, Max Premium). "
            "Output JSON only: {'strategy': 'Short Strangle' or 'Short Straddle', 'rationale': '...', 'constraints': '...'}"
        )
        user_prompt = f"Market IV: {iv}%\nStrangle Rules: {strangle_rules}\nStraddle Rules: {straddle_rules}\nNews: {news}\n\nRecommmend the best strategy."
        
        llm_response = query_llm(system_prompt, user_prompt)
        
        # Simple parsing (Mock fallback if LLM fail)
        if "Error" in llm_response:
            strategy = "Short Strangle"
            rationale = f"Defaulting to safer strategy due to LLM error. IV is {iv}%."
            constraints = strangle_rules
        else:
            # We try to extract JSON, here we just trust the string contains the decision for demo
            if "Straddle" in llm_response:
                strategy = "Short Straddle"
                constraints = straddle_rules
            else:
                strategy = "Short Strangle"
                constraints = strangle_rules
            rationale = llm_response

    strategy_decision = {
        "strategy": strategy,
        "rationale": rationale,
        "constraints": constraints,
        "market_sentiment": news,
        "llm_analysis": llm_response
    }
    
    return {"strategy_decision": strategy_decision}
