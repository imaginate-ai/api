import os
import json
from enum import Enum
from http import HTTPStatus
from base64 import b64encode

# External libraries from pymongo:
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId

db_name = "imaginate_prod"  # Database names: ['imaginate_dev', 'imaginate_prod']
conn_uri = os.environ.get("MONGO_TOKEN")
client = MongoClient(conn_uri)
db = client[db_name]
fs = GridFS(db)
allowed_origins = ["vermillion-biscuit-931b88.netlify.app"]


class DateInfo(Enum):
  START_DATE = 1725163200  # Timestamp for September 1st, 2024
  SECONDS_PER_DAY = 86400


def build_result(
  _id: ObjectId, real: bool, date: int, theme: str, status: str, filename: str
):
  return {
    "filename": filename,
    "url": "image/read/" + str(_id),
    "real": real,
    "date": date,
    "theme": theme,
    "status": status,
  }


def calculate_date(day: str | int | None, latest_day=None):
  if day is not None:
    print(f"Inputted day is: {day}")
    if isinstance(day, str):
      day = int(day)

    # Covert date to timestamp
    if day >= DateInfo.START_DATE.value:
      timestamp_day = day
    else:
      timestamp_day = DateInfo.START_DATE.value + day * DateInfo.SECONDS_PER_DAY.value

    # Check if circular behaviour was requested
    if latest_day is None:
      return timestamp_day

    MIN = DateInfo.START_DATE.value
    MAX = latest_day + DateInfo.SECONDS_PER_DAY.value
    timestamp_day = (timestamp_day - MIN) % (MAX - MIN) + MIN
    print(f"Circular date with range: [{MIN}, {MAX}] and value: {timestamp_day}")
    return timestamp_day
  return None


def images_by_date(day):
  try:
    # This code is from GET /date/latest and is NOT internally called for aws/build_lambda_code.py
    res = next(fs.find().sort({"date": -1}).limit(1), None)  # Descending sort
    if not res:
      return {"statusCode": HTTPStatus.NOT_FOUND, "body": json.dumps("Empty database")}

    date = calculate_date(day, res.date)
    if not date:
      return {"statusCode": HTTPStatus.BAD_REQUEST, "body": json.dumps("Invalid date")}
  except ValueError:
    return {"statusCode": HTTPStatus.BAD_REQUEST, "body": json.dumps("Invalid date")}

  res = fs.find({"date": date})
  out = []
  for document in res:
    current_res = build_result(
      document._id,
      document.real,
      document.date,
      document.theme,
      document.status,
      document.filename,
    )
    encoded_data = b64encode(document.read())
    current_res["data"] = encoded_data.decode("utf-8")
    out.append(current_res)
  return {"statusCode": HTTPStatus.OK, "body": json.dumps(out)}


def handler(event, context):
  print("Headers:", event["headers"])
  origin = event["headers"].get("origin", "")
  cors_origin = "https://playimaginate.com"  # Default CORS origin
  for allowed_origin in allowed_origins:
    if allowed_origin in origin:
      cors_origin = origin
      break
  headers = {
    "Access-Control-Allow-Origin": cors_origin,
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
  }
  if (
    event
    and "queryStringParameters" in event
    and event["queryStringParameters"]
    and "day" in event["queryStringParameters"]
  ):
    result = images_by_date(event["queryStringParameters"]["day"])
    result["headers"] = headers
    return result
  else:
    return {
      "statusCode": HTTPStatus.BAD_REQUEST,
      "body": json.dumps("Invalid date"),
      "headers": headers,
    }
