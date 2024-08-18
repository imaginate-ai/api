import os
import json
from enum import Enum
from http import HTTPStatus
from base64 import b64encode

# External libraries from pymongo:
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId

db_name = "imaginate_dev"
conn_uri = os.environ.get("MONGO_TOKEN")
client = MongoClient(conn_uri)
db = client[db_name]
fs = GridFS(db)


class DateInfo(Enum):
  START_DATE = 1722484800  # Timestamp for August 1st, 2024
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


def calculate_date(day: str | int | None):
  if day is not None:
    if isinstance(day, str):
      day = int(day)
    if day >= DateInfo.START_DATE.value:
      return day
    return DateInfo.START_DATE.value + day * DateInfo.SECONDS_PER_DAY.value
  return None


def images_by_date(day):
  try:
    date = calculate_date(day)
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
  if (
    event
    and "queryStringParameters" in event
    and "day" in event["queryStringParameters"]
  ):
    return images_by_date(event["queryStringParameters"]["day"])
  else:
    return {"statusCode": HTTPStatus.BAD_REQUEST, "body": json.dumps("Invalid date")}
