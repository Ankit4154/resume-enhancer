from dotenv import load_dotenv
import os

load_dotenv()

GLOBAL_API_KEY = os.getenv("GLOBAL_API_KEY","")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:11434")
ENDPOINT = os.getenv("ENDPOINT", "/api/chat")
MODEL = os.getenv("MODEL", "llama3.2")
