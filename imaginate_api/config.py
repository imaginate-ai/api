import os
from dotenv import load_dotenv
import sys


VALID_ENVS = ["dev", "prod"]
def get_db_env():
    env = os.getenv("ENV")
    if not env:
        env = "dev" # Default to dev environment
    elif env.lower() not in VALID_ENVS:
        print(f"Environment should be one of: {VALID_ENVS}", file=sys.stderr)
        sys.exit(1)
    return env.lower()


class Config:
    def __init__(self):
        load_dotenv()

    MONGO_TOKEN = os.getenv("MONGO_TOKEN")
    DB_ENV = get_db_env()
    TESTING = False