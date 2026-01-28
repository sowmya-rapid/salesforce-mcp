import os
from dotenv import load_dotenv

load_dotenv()

SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
SF_REFRESH_TOKEN = os.getenv("SF_REFRESH_TOKEN")
SF_INSTANCE_URL = os.getenv("SF_INSTANCE_URL")
SF_TOKEN_URL = os.getenv("SF_TOKEN_URL")
SF_API_VERSION = os.getenv("SF_API_VERSION", "v59.0")

if not all([
    SF_CLIENT_ID,
    SF_CLIENT_SECRET,
    SF_REFRESH_TOKEN,
    SF_INSTANCE_URL,
    SF_TOKEN_URL,
]):
    raise RuntimeError("Missing required Salesforce environment variables")
