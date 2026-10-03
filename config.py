from dotenv import load_dotenv
import os

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
WRITE_LOGS = os.getenv("WRITE_LOGS", "False").lower() == "true"