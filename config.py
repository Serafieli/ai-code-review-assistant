import os
from dotenv import load_dotenv
# test webhook

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_BASE_URL = os.getenv("GITLAB_BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "12345")
