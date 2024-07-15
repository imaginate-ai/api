from flask import Blueprint, abort, jsonify, make_response, request
from imaginate_api.extensions import fs
from imaginate_api.schemas.image_info import ImageStatus
from imaginate_api.utils import str_to_bool, validate_id, search_id, build_result
from http import HTTPStatus
bp = Blueprint("image", __name__)

# GET /read: used for viewing all images
# This endpoint is simply for testing purposes
@bp.route("/read")
def read_all():
  content = ""
  for res in fs.find():
    content += f'<li><a href="read/{res._id}">{res.filename} - {res._id}</a></li>\n'
  return f"<ul>\n{content}</ul>"


# POST /create: used for image population
# TODO: Add a lot of validation to fit our needs
@bp.route("/create", methods=["POST"])
def upload():
  try:
    file = request.files["file"]
    date = int(request.form["date"])
    theme = request.form["theme"]
    real = str_to_bool(request.form["real"])
    status = ImageStatus.UNVERIFIED.value
  except (KeyError, TypeError, ValueError):
    abort(HTTPStatus.BAD_REQUEST, description="Invalid schema")
  if not (
    file.filename and file.content_type and file.content_type.startswith("image/")
  ):
    abort(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, description="Invalid file")

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
@bp.route("/read/<id>")
def read(id):
  _id = validate_id(id)
  res = search_id(_id)

  response = make_response(res.read())
  response.headers.set("Content-Type", res.type)
  response.headers.set("Content-Length", f"{res.length}")
  return response


# GET /read/<id>: used for viewing a specific image
@bp.route("/read/<id>/properties")
def read_properties(id):
  _id = validate_id(id)
  res = search_id(_id)
  return jsonify(build_result(res._id, res.real, res.date, res.theme, res.status))


# DELETE /delete/<id>: used for deleting a single image
@bp.route("/<id>", methods=["DELETE"])
def delete_image(id):
  _id = validate_id(id)
  res = search_id(_id)

  res_real = getattr(res, "real", None)
  res_date = getattr(res, "date", None)
  res_theme = getattr(res, "theme", None)
  res_status = getattr(res, "status", None)

  info = build_result(res._id, res_real, res_date, res_theme, res_status)
  fs.delete(res._id)
  return info
