from flask import Blueprint, jsonify, make_response, request
from imaginate_api.extensions import fs
from image_handler_client.schemas.image_info import ImageStatus
from imaginate_api.utils import (
  validate_id,
  search_id,
  build_result,
  validate_post_image_create_request,
  build_image_from_url,
)

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
  request_url = request.form.get(
    "url", None
  )  # Determine if our request wants us to use a url
  if request_url:
    print("Getting file data through url attribute")
    request_file = build_image_from_url(request_url)
  else:
    print("Getting file data through file attribute")
    request_file = request.files.get("file")
  file, date, theme, real = validate_post_image_create_request(
    request_file,
    request.form.get("date"),
    request.form.get("theme"),
    request.form.get("real"),
  )
  status = ImageStatus.UNVERIFIED.value
  _id = fs.put(
    file.stream.read(),
    filename=file.filename,
    type=file.content_type,
    date=date,
    theme=theme,
    real=real,
    status=status,
  )
  return jsonify(build_result(_id, real, date, theme, status, file.filename))


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
  return jsonify(
    build_result(res._id, res.real, res.date, res.theme, res.status, res.filename)
  )


# DELETE /delete/<id>: used for deleting a single image
@bp.route("/<id>", methods=["DELETE"])
def delete_image(id):
  _id = validate_id(id)
  res = search_id(_id)

  res_real = getattr(res, "real", None)
  res_date = getattr(res, "date", None)
  res_theme = getattr(res, "theme", None)
  res_status = getattr(res, "status", None)
  res_filename = getattr(res, "filename", None)

  info = build_result(res._id, res_real, res_date, res_theme, res_status, res_filename)
  fs.delete(res._id)
  return jsonify(info)
