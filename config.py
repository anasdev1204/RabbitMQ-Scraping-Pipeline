from dotenv import load_dotenv
import os

load_dotenv()

WRITE_LOGS = os.getenv("WRITE_LOGS", "False").lower() == "true"