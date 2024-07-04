# Flask related
import os

import gridfs
from bson.errors import InvalidId
from bson.objectid import ObjectId

# Other
from dotenv import load_dotenv
from flask import Flask, abort, json, jsonify, make_response, render_template, request

# MongoDB related
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException


# Helper function to get boolean
def str_to_bool(string: str):
  return string.lower() == "true"


# Helper function to validate MongoDB ID
def validate_id(image_id: str | ObjectId | bytes | None):
  try:
    _id = ObjectId(image_id)
  except (InvalidId, TypeError):
    abort(400, "Invalid ID")
  return _id


# Helper function to search MongoDB ID
def search_id(_id: ObjectId):
  res = next(fs.find({"_id": _id}), None)
  if not res:
    abort(404, "Collection not found")
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


# Initialize clients
app = Flask(__name__)
load_dotenv()
db = MongoClient(os.getenv("MONGO_TOKEN"))["imaginate"]
fs = gridfs.GridFS(db)


# This endpoint is simply for testing purposes
@app.route("/")
def index():
  return render_template("index.html")


# GET /read: used for viewing all images
# This endpoint is simply for testing purposes
@app.route("/image/read")
def read_all():
  content = ""
  for res in fs.find():
    content += f'<li><a href="/read/{res._id}">{res.filename} - {res._id}</a></li>\n'
  return f"<ul>\n{content}</ul>"


# Generic error handler in JSON rather than HTML
@app.errorhandler(HTTPException)
def handle_exception(exc: HTTPException):
  response = exc.get_response()
  response.data = json.dumps(
    {
      "code": exc.code,
      "name": exc.name,
      "description": exc.description,
    }
  )
  response.content_type = "application/json"
  return response


# POST /create: used for image population
# TODO: Add a lot of validation to fit our needs
@app.route("/image/create", methods=["POST"])
def upload():
  try:
    file = request.files["file"]
    date = int(request.form["date"])
    theme = request.form["theme"]
    real = str_to_bool(request.form["real"])
    status = "unverified"
  except (KeyError, TypeError, ValueError):
    abort(400, description="Invalid schema")
  if not (
    file.filename and file.content_type and file.content_type.startswith("image/")
  ):
    abort(400, description="Invalid file")

  _id = fs.put(
    file.stream.read(),
    filename=file.filename,
    type=file.content_type,
    date=date,
    theme=theme,
    real=real,
    status=status,
  )
  return jsonify(build_result(_id, real, date, theme, status))


# GET /read/<id>: used for viewing a specific image
@app.route("/image/read/<id>")
def read(image_id):
  _id = validate_id(image_id)
  res = search_id(_id)

  response = make_response(res.read())
  response.headers.set("Content-Type", res.type)
  response.headers.set("Content-Length", f"{res.length}")
  return response


# GET /read/<id>: used for viewing a specific image
@app.route("/image/read/<id>/properties")
def read_properties(image_id):
  _id = validate_id(image_id)
  res = search_id(_id)
  return jsonify(build_result(res._id, res.real, res.date, res.theme, res.status))


# GET /date/<day>/images: used for viewing images of a specified date
@app.route("/date/<day>/images")
def images_by_date(day):
  try:
    day = int(day)
  except ValueError:
    abort(400, description="Invalid date")

  res = fs.find({"date": day})
  out = []
  for document in res:
    out.append(
      build_result(
        document._id,
        document.real,
        document.date,
        document.theme,
        document.status,
      )
    )
  return jsonify(out)


# GET /date/latest: used for getting the latest date in the database
@app.route("/date/latest")
def latest_date():
  res = next(fs.find().sort({"date": -1}), None)  # Descending sort
  if not res:
    abort(400, description="Empty database")
  return jsonify({"date": res.date})


# DELETE /delete/<id>: used for deleting a single image
@app.route("/image/<id>", methods=["DELETE"])
def delete_image(image_id):
  _id = validate_id(image_id)
  res = search_id(_id)

  res_real = getattr(res, "real", None)
  res_date = getattr(res, "date", None)
  res_theme = getattr(res, "theme", None)
  res_status = getattr(res, "status", None)

  info = build_result(res._id, res_real, res_date, res_theme, res_status)
  fs.delete(res._id)
  return info


# Read endpoint
if __name__ == "__main__":
  app.run()
