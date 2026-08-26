import os

from dotenv import load_dotenv
from google import genai

# Load variables from a local .env file (see .env.example) into the environment.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set"
    )

# Single shared client for the whole app
client = genai.Client(api_key=GEMINI_API_KEY)
