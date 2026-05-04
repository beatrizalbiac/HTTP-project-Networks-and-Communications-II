import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

API_KEY_HEADER = "x-api-key"

LOG_FILE = os.path.join(BASE_DIR, "server.log")
STATIC_DIR = os.path.join(BASE_DIR, "static")