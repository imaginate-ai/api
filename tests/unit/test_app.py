import gridfs.grid_file
import mongomock.gridfs
import pytest

# Core libraries
import gridfs

# Imaginate modules
from imaginate_api.utils import (
  str_to_bool,
  validate_id,
  search_id,
  build_result,
  calculate_date,
)
from imaginate_api.app import create_app
from imaginate_api.schemas.date_info import DateInfo

# Other
from werkzeug.exceptions import BadRequest, NotFound, HTTPException
from werkzeug.datastructures import FileStorage
from bson.objectid import ObjectId
from io import BytesIO
from http import HTTPStatus
from image_handler_client.schemas.image_info import ImageStatus

# Mocking
from unittest.mock import patch, MagicMock
import mongomock  # NOTE: mongomock doesn't work well with sorting


# A struct class to convert a dictionary to a object
# This is useful since MongoDB uses attributes and does not support dictionary keys
class Struct:
  def __init__(self, **entries):
    self.__dict__.update(entries)


@pytest.fixture()
def client():
  app = create_app()
  app.config.update({"TESTING": True})
  return app.test_client()


@pytest.fixture
def mock_mongo_client():
  mock_mongo_client = mongomock.MongoClient()
  return mock_mongo_client


@pytest.fixture
def mock_db(mock_mongo_client):
  mock_db = mock_mongo_client["imaginate_dev"]
  return mock_db


@pytest.fixture
def mock_fs(mock_db):
  mongomock.gridfs.enable_gridfs_integration()
  mock_fs = gridfs.GridFS(mock_db)
  return mock_fs


@pytest.fixture
def mock_data():
  mock_data = [
    {
      "data": b"data",
      "filename": f"sample-{i}",
      "type": "image/png",
      "date": calculate_date(i),
      "theme": "sample",
      "real": True,
      "status": ImageStatus.UNVERIFIED.value,
    }
    for i in range(5)
  ]
  return mock_data


# Set up database before running tests
@pytest.fixture(autouse=True)
def setup(mock_fs):
  with (
    patch("imaginate_api.date.routes.fs", mock_fs),
    patch("imaginate_api.image.routes.fs", mock_fs),
    patch("imaginate_api.utils.fs", mock_fs),
  ):
    yield


@pytest.mark.parametrize(
  "string, expected", [("true", True), ("false", False), ("foo", False)]
)
def test_str_to_bool(string, expected):
  assert str_to_bool(string) == expected


@pytest.mark.parametrize(
  "image_id, expected",
  [
    ("621f1d71aec9313aa2b9074c", ObjectId("621f1d71aec9313aa2b9074c")),
    ("621f1d71aec9313aa2b9074cd", BadRequest),
    ("", BadRequest),
    (None, BadRequest),
  ],
)
def test_validate_id(image_id, expected):
  if expected is BadRequest:
    with pytest.raises(HTTPException) as err:
      validate_id(image_id)
    assert err.errisinstance(expected)
  else:
    assert validate_id(image_id) == expected


def test_search_id_success(mock_fs, mock_data):
  for entry in mock_data:
    _id = mock_fs.put(**entry)
    res = search_id(_id)
    assert res._id == _id


@pytest.mark.parametrize(
  "_id, expected",
  [("621f1d71aec9313aa2b9074cd", NotFound), ("", NotFound), (None, NotFound)],
)
def test_search_id_exception(_id, expected):
  with pytest.raises(HTTPException) as err:
    search_id(_id)
  assert err.errisinstance(expected)


# Not sure how to test this function since it just organizes data
def test_build_result():
  pass


@pytest.mark.parametrize(
  "data, expected",
  [
    ([0], DateInfo.START_DATE.value),
    (["3"], DateInfo.START_DATE.value + 3 * DateInfo.SECONDS_PER_DAY.value),
    ([DateInfo.START_DATE.value + 123], DateInfo.START_DATE.value + 123),
    (
      [
        DateInfo.START_DATE.value, 
        None, # db param
        DateInfo.START_DATE.value
      ], 
      DateInfo.START_DATE.value
    ),
    # Range of [0, 4] -> 5 possible dates, therefore every date will circle back to itself 5 days apart
    # Explanation for example below: 14 - 5 = 9 -> 9 - 5 = 4; therefore this timestamp will map to the same result as day = 4, 9, 14, 19, ...
    (
      [
        DateInfo.START_DATE.value + 14 * DateInfo.SECONDS_PER_DAY.value,
        None, # db param
        DateInfo.START_DATE.value + 4 * DateInfo.SECONDS_PER_DAY.value,
      ],
      DateInfo.START_DATE.value + 4 * DateInfo.SECONDS_PER_DAY.value,
    ),
  ],
)
def test_calculate_date(data, expected):
  assert calculate_date(*data) == expected


# Not testing as this endpoint will likely be removed in future
def test_get_root_endpoint():
  pass


# Not testing as this endpoint will likely be removed in future
def test_get_image_read_all_endpoint():
  pass


def test_post_image_create_endpoint_success(client, mock_data):
  for entry in mock_data:
    entry["file"] = FileStorage(
      stream=BytesIO(entry["data"]),
      filename=entry["filename"],
      content_type=entry["type"],
    )
    res = client.post("/image/create", data=entry, content_type="multipart/form-data")
    assert res.json == build_result(
      res.json["url"].split("/")[-1],
      entry["real"],
      calculate_date(entry["date"]),
      entry["theme"],
      entry["status"],
      entry["filename"],
    )


@pytest.mark.parametrize(
  "data, expected",
  [
    (
      {"file": FileStorage(stream=BytesIO(b"data"), content_type="image/png")},
      HTTPStatus.BAD_REQUEST,
    ),
    (
      {
        "date": 0,
        "theme": "sample",
        "real": True,
        "status": ImageStatus.UNVERIFIED.value,
        "file": FileStorage(
          stream=BytesIO(b"data"), filename="test.pdf", content_type="application/pdf"
        ),
      },
      HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
    ),
    (
      {
        "date": 0,
        "theme": "sample",
        "real": True,
        "status": ImageStatus.UNVERIFIED.value,
        "url": "https://www.google.com",  # Causes endpoint to take a different flow
        "file": FileStorage(
          stream=BytesIO(b"data"), filename="test.png", content_type="image/png"
        ),
      },
      HTTPStatus.OK,
    ),
  ],
)
def test_post_image_create_endpoint_status_code(data, expected, client):
  with patch("requests.get") as mock_get:
    mock_response = MagicMock()
    mock_response.content = data["file"].stream.read()
    mock_response.headers.get = MagicMock(return_value=data["file"].content_type)
    mock_get.return_value = mock_response
    res = client.post("/image/create", data=data, content_type="multipart/form-data")
    assert res.status_code == expected


# Not testing scenarios with exceptions as they have been tested by helper functions:
# validate_id, search_id
def test_get_image_read_endpoint(mock_fs, mock_data, client):
  for entry in mock_data:
    _id = mock_fs.put(**entry)
    res = client.get(f"/image/read/{_id}")
    assert res.status_code == HTTPStatus.OK
    assert res.data == entry["data"]


# Not testing scenarios with exceptions as they have been tested by helper functions:
# validate_id, search_id
def test_get_image_read_properties_endpoint(mock_fs, mock_data, client):
  for entry in mock_data:
    _id = mock_fs.put(**entry)
    res = client.get(f"/image/read/{_id}/properties")
    assert res.status_code == HTTPStatus.OK
    assert res.json == build_result(
      _id,
      entry["real"],
      entry["date"],
      entry["theme"],
      entry["status"],
      entry["filename"],
    )


# NOTE: The test cases below will need to be reworked as they use pymongo's .sort() which
# isn't implemented into mongomock (yet)! The solution here would be to mock fs.find() but doing this
# will prevent us from using mongomock at all, which would then make testing this function a difficult task

# def test_get_date_images_endpoint_success(mock_fs, mock_data, client):
#   for entry in mock_data:
#     entry["date"] = calculate_date(entry["date"])
#     _id = mock_fs.put(**entry)
#     res = client.get(f"/date/{entry['date']}/images")
#     assert res.status_code == HTTPStatus.OK
#     return_image = build_result(
#       _id,
#       entry["real"],
#       entry["date"],
#       entry["theme"],
#       entry["status"],
#       entry["filename"],
#     )
#     encoded_data = base64.b64encode(entry["data"])
#     return_image["data"] = encoded_data.decode("utf-8")
#     assert res.json == [return_image]


# @pytest.mark.parametrize(
#   "day, expected", [("abc", HTTPStatus.BAD_REQUEST), (0, HTTPStatus.OK)]
# )
# def test_get_date_images_endpoint_exception(day, expected, client):
#   res = client.get(f"date/{day}/images")
#   assert res.status_code == expected


# Tested differently since the endpoint involves sorting
def test_get_date_latest_endpoint_success(mock_data, client):
  with patch("imaginate_api.date.routes.fs.find") as mock_find:
    sorted_data = sorted(mock_data, key=lambda x: x["date"], reverse=True)
    data = iter([Struct(**entry) for entry in sorted_data])
    mock_find.return_value.sort.return_value.limit.return_value = data
    res = client.get("date/latest")
    assert res.status_code == HTTPStatus.OK
    assert res.json == {"date": sorted_data[0]["date"]}


# Tested differently since the endpoint involves sorting
def test_get_date_latest_endpoint_exception(client):
  with patch("imaginate_api.date.routes.fs.find") as mock_find:
    data = iter([])
    mock_find.return_value.sort.return_value.limit.return_value = data
    res = client.get("date/latest")
    assert res.status_code == HTTPStatus.NOT_FOUND


def test_delete_image_endpoint(mock_fs, mock_data, client):
  for entry in mock_data:
    _id = mock_fs.put(**entry)
    res = client.delete(f"/image/{_id}")
    assert res.status_code == HTTPStatus.OK
    assert res.json == build_result(
      _id,
      entry["real"],
      entry["date"],
      entry["theme"],
      entry["status"],
      entry["filename"],
    )


def test_delete_image_success(client, mock_fs, mock_data):
  for entry in mock_data:
    _id = mock_fs.put(**entry)
    res = client.delete(f"/image/{_id}")
    assert res.status_code == 200

    response_data = res.get_json()
    res_id = response_data.get("url").split("/")[-1]
    assert res_id == str(_id)
