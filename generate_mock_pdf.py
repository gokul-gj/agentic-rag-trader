from fpdf import FPDF
import os

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    lines = [
        "Short Strangle Strategy Rules and Constraints",
        "",
        "1. Market Conditions:",
        "   - Implied Volatility (IV) should be above the 50th percentile.",
        "   - Avoid entering before major events (earnings, policy announcements).",
        "   - Do not trade before 9:30 AM to avoid initial volatility.",
        "",
        "2. Strike Selection:",
        "   - Sell Call Strike at 15-20 Delta.",
        "   - Sell Put Strike at 15-20 Delta.",
        "   - Ideally, strikes should be outside the 1 Standard Deviation range.",
        "",
        "3. Management:",
        "   - Exit if loss exceeds 2x the credit received.",
        "   - Adjust strikes if the spot price breaches one of the breakeven points.",
        "   - Take profit at 50% max profit.",
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
