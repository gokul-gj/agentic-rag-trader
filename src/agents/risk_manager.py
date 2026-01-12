from typing import Dict, Any

def validate_order(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Risk Manager Node.
    Validates the proposed order against safety checks.
    """
    print("--- [Risk Manager] Validating Order ---")
    order = state.get("final_order", {})
    market_data = state.get("market_data", {})
    
    if not order:
        return {"error": "No order to validate."}
    
    # Example Risk Rule: Do not sell calls if IV is very low (Gamma risk)
    iv = market_data.get("iv", 0)
    if iv < 10: # Stricter check than Scanner
        print(f"Risk Alert: IV {iv}% is too low for safe selling. Rejecting.")
        return {"error": "Risk Rejection: Low IV"}
    
    # Example Risk Rule: Delta check (Simulated)
    # in a real system we'd calculate delta
    
    print("Order Approved by Risk Manager.")
    return {"risk_status": "approved"}
