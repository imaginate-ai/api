from flask import abort
from bson.errors import InvalidId
from bson.objectid import ObjectId
from http import HTTPStatus
from imaginate_api.extensions import fs
from imaginate_api.schemas.date_info import DateInfo



# Helper function to get boolean
def str_to_bool(string: str):
  return string.lower() == "true"


# Helper function to validate MongoDB ID
def validate_id(image_id: str | ObjectId | bytes):
  if not image_id:
    abort(HTTPStatus.BAD_REQUEST, "Missing ID")
  try:
    _id = ObjectId(image_id)
  except (InvalidId, TypeError):
    abort(HTTPStatus.BAD_REQUEST, "Invalid ID")
  return _id


# Helper function to search MongoDB ID
def search_id(_id: ObjectId):
  print(fs)
  res = next(fs.find({"_id": _id}), None)
  if not res:
    abort(HTTPStatus.NOT_FOUND, "Collection not found")
  return res


# Helper function to build schema-matching JSON response
def build_result(_id: ObjectId, real: bool, date: int, theme: str, status: str):
  return {
    "url": "/read/" + str(_id),
    "real": real,
    "date": date,
    "theme": theme,
    "status": status,
  }


# helper function that returns a timestamp date object
def calculate_date(day: int):
  if day > DateInfo.START_DATE.value:
    return day
  return DateInfo.START_DATE.value + day * DateInfo.SECONDS_PER_DAY.value
