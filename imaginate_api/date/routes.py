from flask import Blueprint, abort, jsonify
from imaginate_api.extensions import fs, db
from imaginate_api.utils import build_result, calculate_date
from http import HTTPStatus
from base64 import b64encode

bp = Blueprint("date", __name__)

# Explanation of our employed dating system:
# - Days can be entered by ID or by timestamp
# - Valid timestamps are the start of a new day (i.e. midnight) while IDs are simply numbered as increasing integers starting from zero
# - IDs are the set of natural numbers (including zero) and are converted to timestamp using a start date of (for example) September 1st 2024
#   - Examples: ID: 0 -> Date: September 1st 2024; ID: 1 -> Date: September 2nd 2024; ID: 10 -> Date: September 11th 2024


# GET /date/<day>/images: used for viewing images of a specified date
@bp.route("/<day>/images")
def images_by_date(day):
  try:
    # This code is from GET /date/latest and is NOT internally called for aws/build_lambda_code.py
    res = next(fs.find().sort({"date": -1}).limit(1), None)  # Descending sort
    if not res:
      abort(HTTPStatus.NOT_FOUND, description="Empty database")

    date = calculate_date(day, db, res.date)
    if not date:
      abort(HTTPStatus.BAD_REQUEST, description="Invalid date")
  except ValueError:
    abort(HTTPStatus.BAD_REQUEST, description="Invalid date")

  day_document = db['days'].find_one(
    {"_id": date},
  )
  res = fs.find({"_id": {"$in": day_document.get("images", [])}})
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
  return jsonify(out)


# GET /date/latest: used for getting the latest date in the database
@bp.route("/latest")
def latest_date():
  # Explanation for this query: https://www.mongodb.com/docs/manual/core/aggregation-pipeline-optimization/#-sort----limit-coalescence
  res = next(fs.find().sort({"date": -1}).limit(1), None)  # Descending sort
  if not res:
    abort(HTTPStatus.NOT_FOUND, description="Empty database")
  return jsonify({"date": res.date})


@bp.route("/delete-rejected/<day>", methods=["DELETE"])
def delete_rejected_by_day(day):
    if not day:
        return jsonify({"error": "Date is required"}), HTTPStatus.BAD_REQUEST

    try:
        # Convert the provided day into the expected date format
        date = calculate_date(day)

        # Query the GridFS to find all rejected images for the given date
        images_to_delete = fs.find({"date": date, "status": "rejected"})

        deleted_count = 0
        for image in images_to_delete:
            fs.delete(image._id)
            deleted_count += 1

        if deleted_count == 0:
            return jsonify({"message": "No rejected images found for the given date."}), HTTPStatus.NOT_FOUND

        return jsonify({
            "message": f"Deleted {deleted_count} rejected images from the date '{date}'."
        }), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

