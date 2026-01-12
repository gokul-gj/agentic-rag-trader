from fpdf import FPDF
import os

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    lines = [
        "Short Strangle Strategy Rules and Constraints",
        "",
        "1. Market Regime & Strategy Selection:",
        "   - LOW VOLATILITY (IV Percentile < 40): Deploy SHORT STRADDLE.",
        "     * Capture maximum premium in range-bound markets.",
        "     * Entry Time: 09:45 AM (allow initial settlement).",
        "   - HIGH VOLATILITY (IV Percentile > 50): Deploy SHORT STRANGLE.",
        "     * Widen breakevens to handle larger swings.",
        "     * Strike Selection: Dynamic Delta.",
        "       > If VIX < 15: Sell 20 Delta Strikes.",
        "       > If VIX > 20: Sell 15 Delta Strikes (Safety first).",
        "",
        "2. Risk Management (The Holy Grail):",
        "   - STOP LOSS: Combined Premium SL of 25%. (e.g., entered at 100+100=200, exit at 250).",
        "   - ADJUSTMENT (Delta Neutralizing):",
        "     * If Spot breaches 0.30 Delta on one leg, roll the UNTESTED leg closer.",
        "     * Maintain total delta within +/- 0.10.",
        "   - GAMMA RISK:",
        "     * Hard Exit if < 2 DTE (Days to Expiry) and Spot is within 1% of Short Strike.",
        "     * Do not carry overnight positions into Earnings.",
        "   - BLACK SWAN PROTECTION:",
        "     * If India VIX spikes > 15% in a single day, liquidate all Short Vegas immediately.",
        "     * Buy cheap wings (5-10 Delta) as hedge if VIX is at multi-year lows (< 11).",
    ]
    
    for line in lines:
        pdf.cell(200, 10, txt=line, ln=True, align='L')
        
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pdf.output("data/strategy_rules.pdf")
    print("Created data/strategy_rules.pdf")

if __name__ == "__main__":
    create_pdf()
