from pymongo import MongoClient
import gridfs
from imaginate_api.config import Config
import sys
from flask_caching import Cache


def connect_mongodb(conn_uri: str, db_name: str):
    client = MongoClient(conn_uri)

    # If the connection was not established properly, an exception will be raised by this if statement
    if db_name not in client.list_database_names():
        print(f"Database \"{db_name}\" does not exist", file=sys.stderr)
        sys.exit(1)
    
    return client[db_name], gridfs.GridFS(client[db_name])


# Setup
print(f"Running in \"{Config.DB_ENV}\" environment")
db, fs = connect_mongodb(Config.MONGO_TOKEN, f"imaginate_{Config.DB_ENV}")
cache = Cache()