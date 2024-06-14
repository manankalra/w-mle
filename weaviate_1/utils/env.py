import os
from dotenv import load_dotenv


load_dotenv()

WCS_URL = os.getenv("WCS_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
