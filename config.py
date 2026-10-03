from dotenv import load_dotenv
import os

load_dotenv()

WRITE_LOGS = os.get_env("WRITE_LOGS", "False").lower() == "true"