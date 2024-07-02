# Flask related
from flask import Flask, json, jsonify, render_template, make_response, abort, request
from werkzeug.exceptions import HTTPException

# MongoDB related
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId
from bson.errors import InvalidId

# Other
from dotenv import load_dotenv
import os

# Helper function to get boolean
def str_to_bool(string: str):
    return string.lower() == "true"

# Helper function to validate MongoDB ID
def validate_id(id: str | ObjectId | bytes | None):
    try:
        _id = ObjectId(id)
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
def build_result(_id: ObjectId, real: bool, date: int, theme: str):
    return {
        "url": "/read/" + str(_id),
        "real": real,
        "date": date,
        "theme": theme
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
@app.route("/read")
def read_all():
    content = ""
    for res in fs.find():
        content += f'<li><a href="/read/{res._id}">{res.filename} - {res._id}</a></li>\n'
    return f"<ul>\n{content}</ul>"

# Generic error handler in JSON rather than HTML
@app.errorhandler(HTTPException)
def handle_exception(e: HTTPException):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

# POST /create: used for image population
# TODO: Add a lot of validation to fit our needs
@app.route("/create", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        date = int(request.form["date"])
        theme = request.form["theme"]
        real = str_to_bool(request.form["real"])
    except (KeyError, TypeError, ValueError):
        abort(400, description="Invalid schema")
    if not (file.filename and file.content_type and file.content_type.startswith("image/")):
        abort(400, description="Invalid file")

    _id = fs.put(file.stream.read(), filename=file.filename, type=file.content_type,
                 date=date, theme=theme, real=real)
    return jsonify(build_result(_id, real, date, theme))

# GET /read/<id>: used for viewing a specific image 
@app.route("/read/<id>")
def read(id):
    _id = validate_id(id)
    res = search_id(_id)
    
    response = make_response(res.read())
    response.headers.set("Content-Type", res.type)
    response.headers.set("Content-Length", f"{res.length}")
    return response

# GET /read/<id>: used for viewing a specific image 
@app.route("/read/<id>/properties")
def read_properties(id):
    _id = validate_id(id)
    res = search_id(_id)
    return jsonify(build_result(res._id, res.real, res.date, res.theme))

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
        out.append(build_result(document._id, document.real, document.date, document.theme))
    return jsonify(out)

# GET /date/latest: used for getting the latest date in the database
@app.route("/date/latest")
def latest_date():
    res = next(fs.find().sort({"date": -1}), None) # Descending sort 
    if not res:
        abort(400, description="Empty database")
    return jsonify({"date": res.date})

# Read endpoint
if __name__ == "__main__":
    app.run()