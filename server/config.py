import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

API_KEY_HEADER = "x-api-key"

LOG_FILE = os.environ.get("LOG_FILE", "server.log")
STATIC_DIR = os.environ.get("STATIC_DIR", "static")