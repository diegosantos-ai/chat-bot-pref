import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from pyngrok import ngrok

# Load env
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

def start_tunnel():
    try:
        app_port = int(os.getenv("APP_PORT", "8000"))
        tunnel = ngrok.connect(app_port)
        public_url = tunnel.public_url
        print(f"Tunnel Started: {public_url}")
        sys.stdout.flush()

        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Error starting tunnel: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_tunnel()
