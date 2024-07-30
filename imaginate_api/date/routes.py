from flask import Blueprint, abort, jsonify
from imaginate_api.extensions import fs
from imaginate_api.utils import build_result
from http import HTTPStatus

bp = Blueprint("date", __name__)


# GET /date/<day>/images: used for viewing images of a specified date
@bp.route("/<day>/images")
def images_by_date(day):
  try:
    day = int(day)
  except ValueError:
    abort(HTTPStatus.BAD_REQUEST, description="Invalid date")

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
        document.filename,
      )
    )
  return jsonify(out)


# GET /date/latest: used for getting the latest date in the database
@bp.route("/latest")
def latest_date():
  # Explanation for this query: https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/#-sort----limit-coalescence
  res = next(fs.find().sort({"date": -1}).limit(1), None)  # Descending sort
  if not res:
    abort(HTTPStatus.NOT_FOUND, description="Empty database")
  return jsonify({"date": res.date})
