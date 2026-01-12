import numpy as np
from scipy.stats import norm

# Risk-free rate assumption (India ~ 7%)
R = 0.07

def calculate_greeks(spot, strike, time_to_expiry_days, iv, option_type="CE"):
    """
    Calculates Option Greeks using Black-Scholes Model.
    """
    S = spot
    K = strike
    T = time_to_expiry_days / 365.0
    v = iv / 100.0
    r = R
    
    if T <= 0:
        return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "price": 0}

    d1 = (np.log(S / K) + (r + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    d2 = d1 - v * np.sqrt(T)

    if option_type == "CE":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (- (S * norm.pdf(d1) * v) / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365.0
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = (- (S * norm.pdf(d1) * v) / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365.0

    gamma = norm.pdf(d1) / (S * v * np.sqrt(T))
    vega = (S * norm.pdf(d1) * np.sqrt(T)) / 100.0 # Sensitivity per 1% change

    return {
        "price": round(price, 2),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 4),
        "vega": round(vega, 4)
    }
