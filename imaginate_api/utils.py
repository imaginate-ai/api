from flask import abort, current_app
from bson.errors import InvalidId
from bson.objectid import ObjectId
from http import HTTPStatus
from imaginate_api.extensions import fs
import requests
from werkzeug.datastructures import FileStorage
from io import BytesIO
from urllib.parse import urlparse
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
  res = next(fs.find({"_id": _id}), None)
  if not res:
    abort(HTTPStatus.NOT_FOUND, "Collection not found")
  return res


# Helper function to build schema-matching JSON response
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


# Helper function to validate POST image/create endpoint
def validate_post_image_create_request(file, date, theme, real):
  if any(x is None for x in [file, date, theme, real]):
    abort(HTTPStatus.BAD_REQUEST, description="Invalid schema")
  try:
    date = int(date)
    real = str_to_bool(real)
  except (KeyError, TypeError, ValueError):
    abort(HTTPStatus.BAD_REQUEST, description="Invalid schema")
  if not (
    file.filename and file.content_type and file.content_type.startswith("image/")
  ):
    abort(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, description="Invalid file")
  return file, date, theme, real


# This catches most urls but not all!
def validate_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except AttributeError:
    return False


def build_image_from_url(url):
  if not validate_url(url):
    abort(HTTPStatus.BAD_REQUEST, description=f"Malformed URL: {url}")

  # Get raw content of the source image
  photo_response = requests.get(
    url, headers={"Authorization": current_app.config["PEXELS_TOKEN"]}, stream=True
  )
  if not photo_response.ok:
    abort(
      photo_response.status_code,
      description=f"Request to URL failed with: {photo_response.reason}",
    )
  raw_photo = photo_response.content
  type_photo = photo_response.headers.get("Content-Type")
  if not (type_photo and type_photo.startswith("image/")):
    abort(
      HTTPStatus.UNSUPPORTED_MEDIA_TYPE, description=f"Invalid file from URL: {url}"
    )

  # Return content using file storage
  return FileStorage(
    stream=BytesIO(raw_photo),
    filename=str(url).rstrip("/").split("/")[-1],
    content_type=type_photo,
  )


# Helper function that returns a timestamp as an integer, where day is a timestamp or day number
# WARNING: Do not enter a timestamp BEFORE August 1st 2024
def calculate_date(day: str | int | None):
  if day is not None:
    if isinstance(day, str):
      day = int(day)
    if day >= DateInfo.START_DATE.value:
      return day
    return DateInfo.START_DATE.value + day * DateInfo.SECONDS_PER_DAY.value
  return None
