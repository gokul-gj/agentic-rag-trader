import os
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import threading
import time

# Load env variables if not using dotenv separate loader, 
# typically we assume they are set or we read .env manually here for the script
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val

load_env()

API_KEY = os.environ.get("KITE_API_KEY")
API_SECRET = os.environ.get("KITE_API_SECRET")

if not API_KEY or not API_SECRET:
    print("Error: KITE_API_KEY and KITE_API_SECRET must be set in .env file.")
    exit()

kite = KiteConnect(api_key=API_KEY)

# Simple server to handle the callback
class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if "request_token" in query_params:
            request_token = query_params["request_token"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Token received! You can close this window and check the terminal.")
            
            print(f"\n[+] Request Token: {request_token}")
            
            try:
                data = kite.generate_session(request_token, api_secret=API_SECRET)
                access_token = data["access_token"]
                print(f"[+] Access Token generated: {access_token}")
                print(f"\n[ACTION REQUIRED] Copy the Access Token above and paste it into your .env file as KITE_ACCESS_TOKEN={access_token}")
            except Exception as e:
                print(f"[-] Error generating session: {e}")
            
            # Kill server
            threading.Thread(target=httpd.shutdown).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No request_token found.")

print("Starting Login Flow...")
print("Please ensure your Zerodha App 'Redirect URL' is set to: http://localhost:8000/callback")

server_address = ('', 8000)
httpd = HTTPServer(server_address, CallbackHandler)

login_url = kite.login_url()
print(f"Opening Login URL: {login_url}")
webbrowser.open(login_url)

print("Waiting for callback on port 8000...")
httpd.serve_forever()
print("Done.")
