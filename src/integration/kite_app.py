import os
import logging
from kiteconnect import KiteConnect

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KiteApp:
    def __init__(self):
        self.api_key = os.environ.get("KITE_API_KEY")
        self.api_secret = os.environ.get("KITE_API_SECRET")
        self.access_token = os.environ.get("KITE_ACCESS_TOKEN")
        
        if not self.api_key:
            logger.warning("KITE_API_KEY not found in env.")
            self.kite = None
            return

        self.kite = KiteConnect(api_key=self.api_key)

        if self.access_token:
            self.kite.set_access_token(self.access_token)
        else:
            logger.warning("Kite Access Token not found. Login flow required.")

    def login_url(self):
        """Returns the login URL for manual authentication."""
        if self.kite:
            return self.kite.login_url()
        return "Error: Kite not initialized"

    def generate_session(self, request_token):
        """Generates access token from request token."""
        if not self.kite: return
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        self.kite.set_access_token(data["access_token"])
        return data["access_token"]
    
    def get_quote(self, instruments):
        """Fetches live quotes for a list of instrument tokens."""
        if not self.kite:
            # Mock response
            return {inst: {"last_price": 100.0, "oi": 50000} for inst in instruments}
        return self.kite.quote(instruments)

    def place_order(self, symbol, transaction_type, quantity, price=None, order_type="MARKET"):
        """Places an order."""
        if not self.kite:
            logger.info(f"[MOCK] Placing {transaction_type} order for {symbol} Qty={quantity}")
            return "mock_order_id_123"
            
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NFO,
                transaction_type=transaction_type,
                quantity=quantity,
                variety=self.kite.VARIETY_REGULAR,
                order_type=self.kite.ORDER_TYPE_MARKET if order_type == "MARKET" else self.kite.ORDER_TYPE_LIMIT,
                price=price,
                product=self.kite.PRODUCT_NRML,
                validity=self.kite.VALIDITY_DAY
            )
            return order_id
        except Exception as e:
            logger.error(f"Order Placement Failed: {e}")
            return None

    def get_instruments(self):
        """Downloads master instrument dump."""
        if not self.kite:
            return []
        return self.kite.instruments("NFO")

# Singleton instance
kite_client = KiteApp()
