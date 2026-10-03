from dotenv import load_dotenv
import os

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
WRITE_LOGS = os.getenv("WRITE_LOGS", "False").lower() == "true"


BASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1'
}
