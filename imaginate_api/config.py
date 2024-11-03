import os
from dotenv import load_dotenv
import sys


VALID_ENVS = ["dev", "prod"]


def get_db_env():
  env = os.getenv("ENV")
  if not env:
    env = "dev"  # Default to dev environment
  elif env.lower() not in VALID_ENVS:
    print(f"Environment should be one of: {VALID_ENVS}", file=sys.stderr)
    sys.exit(1)
  return env.lower()


class Config:
  load_dotenv()
  MONGO_TOKEN = os.getenv("MONGO_TOKEN")
  PEXELS_TOKEN = os.getenv("PEXELS_TOKEN")
  DB_ENV = get_db_env()
  AUTH_PROVIDERS = {
    "google": {
      "client_id": os.getenv("GOOGLE_CLIENT_ID"),
      "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
      "authorize_url": "https://accounts.google.com/o/oauth2/auth",
      "token_url": "https://accounts.google.com/o/oauth2/token",
      "user_info": {
        "url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "data": lambda json: {"email": json["email"], "id": json["sub"]},
      },
      "scopes": ["https://www.googleapis.com/auth/userinfo.email"],
    }
  }
  BASE_URL = (
    "https://playimaginate.com" if DB_ENV == "prod" else "http://127.0.0.1:5000"
  )
  TESTING = False
