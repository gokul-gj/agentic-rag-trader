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
    recommended_sigma = 1.0  # Default sigma value
    
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
            "Also recommend the sigma multiplier for strike selection (1.0 for standard, 1.5 for conservative, 2.0 for very conservative). "
            "Output JSON only: {'strategy': 'Short Strangle' or 'Short Straddle', 'recommended_sigma': 1.0-2.0, 'rationale': '...', 'constraints': '...'}"
        )
        user_prompt = f"Market IV: {iv}%\nStrangle Rules: {strangle_rules}\nStraddle Rules: {straddle_rules}\nNews: {news}\n\nRecommend the best strategy and sigma multiplier."
        
        llm_response = query_llm(system_prompt, user_prompt)
        
        # Enhanced parsing with robust JSON extraction
        if "Error" in llm_response:
            print("⚠️ [FALLBACK] LLM Error - Using default Strangle strategy")
            strategy = "Short Strangle"
            rationale = f"Defaulting to safer strategy due to LLM error. IV is {iv}%."
            constraints = strangle_rules
            recommended_sigma = 1.0  # Conservative default on error
        else:
            # Try to parse JSON response
            import json
            import re
            
            strategy = None
            rationale = llm_response
            recommended_sigma = 1.0
            
            try:
                # Attempt to parse as JSON
                # Remove markdown code blocks if present
                clean_response = re.sub(r'```json\s*|\s*```', '', llm_response)
                llm_json = json.loads(clean_response)
                
                # Extract values from JSON
                strategy = llm_json.get('strategy')
                recommended_sigma = float(llm_json.get('recommended_sigma', 1.0))
                rationale = llm_json.get('rationale', llm_response)
                
                print(f"✅ Successfully parsed JSON: strategy={strategy}, sigma={recommended_sigma}")
                
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback to regex extraction
                print(f"⚠️ JSON parsing failed, using regex fallback: {e}")
                
                # Extract strategy using regex (more robust)
                if re.search(r'\bshort\s+straddle\b', llm_response, re.IGNORECASE):
                    strategy = "Short Straddle"
                elif re.search(r'\bshort\s+strangle\b', llm_response, re.IGNORECASE):
                    strategy = "Short Strangle"
                elif re.search(r'\bstraddle\b', llm_response, re.IGNORECASE):
                    strategy = "Short Straddle"
                elif re.search(r'\bstrangle\b', llm_response, re.IGNORECASE):
                    strategy = "Short Strangle"
                
                # Extract sigma if mentioned
                sigma_match = re.search(r'sigma[:\s]*(\d+\.?\d*)', llm_response, re.IGNORECASE)
                if sigma_match:
                    try:
                        recommended_sigma = float(sigma_match.group(1))
                        print(f"✅ Extracted sigma from text: {recommended_sigma}")
                    except ValueError:
                        pass
            
            # Final check: if strategy still not determined, default safely
            if not strategy:
                print(f"⚠️ [FALLBACK] Could not determine strategy from LLM response. Defaulting to Strangle.")
                print(f"LLM Response excerpt: {llm_response[:200]}")
                strategy = "Short Strangle"
            
            # ✅ FIXED: Dynamically load constraints based on FINAL strategy decision
            if strategy == "Short Straddle":
                constraints = straddle_rules
            else:
                constraints = strangle_rules

    strategy_decision = {
        "strategy": strategy,
        "rationale": rationale,
        "constraints": constraints,
        "market_sentiment": news,
        "llm_analysis": llm_response,
        "recommended_sigma": recommended_sigma  # Pass sigma to executor
    }
    
    return {"strategy_decision": strategy_decision}
