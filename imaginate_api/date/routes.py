from flask import Blueprint, abort, jsonify
from imaginate_api.extensions import fs
from imaginate_api.utils import build_result, calculate_date
from http import HTTPStatus
import base64

bp = Blueprint("date", __name__)


# GET /date/<day>/images: used for viewing images of a specified date
@bp.route("/<day>/images")
def images_by_date(day):
  try:
    date = calculate_date(day)
    if not date:
      abort(HTTPStatus.BAD_REQUEST, description="Invalid date")
  except ValueError:
    abort(HTTPStatus.BAD_REQUEST, description="Invalid date")

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
    encoded_data = base64.b64encode(document.read())
    current_res["data"] = encoded_data.decode("utf-8")
    out.append(current_res)
  return jsonify(out)


# GET /date/latest: used for getting the latest date in the database
@bp.route("/latest")
def latest_date():
  # Explanation for this query: https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/#-sort----limit-coalescence
  res = next(fs.find().sort({"date": -1}).limit(1), None)  # Descending sort
  if not res:
    abort(HTTPStatus.NOT_FOUND, description="Empty database")
  return jsonify({"date": res.date})
