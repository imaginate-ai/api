import inspect
import re
import os
import subprocess
import shutil
import zipfile
from imaginate_api.date.routes import images_by_date
from imaginate_api.utils import build_result, calculate_date
from imaginate_api.schemas.date_info import DateInfo


CWD = os.path.dirname(os.path.realpath(__file__))
LAMBDA_LIBRARIES = """import os
import json
from enum import Enum
from http import HTTPStatus
from base64 import b64encode

# External libraries from pymongo:
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId
"""
LAMBDA_SETUP = """db_name = 'imaginate_dev'
conn_uri = os.environ.get('MONGO_TOKEN')
client = MongoClient(conn_uri)
db = client[db_name]
fs = GridFS(db)
"""
LAMBDA_FUNC = """def handler(event, context):
    if event and 'queryStringParameters' in event and event['queryStringParameters'] and 'day' in event['queryStringParameters']:
        return images_by_date(event['queryStringParameters']['day'])
    else:
        return {'statusCode': HTTPStatus.BAD_REQUEST, 'body': json.dumps('Invalid date')}
"""
LAMBDA_SUBS = {
  "abort": "return {'statusCode': HTTPStatus.BAD_REQUEST, 'body': json.dumps('Invalid date')}",
  "@bp.route": "",  # Remove this from function decorator
  "return jsonify": "return {'statusCode': HTTPStatus.OK, 'body': json.dumps(out)}",
}


# Meta-program our source function to substitute Flask related libraries
def edit_source_function(source_function: str) -> str:
  for sub in LAMBDA_SUBS:
    source_function = re.sub(
      r"^(\s*)" + sub + r".*$",
      r"\g<1>" + LAMBDA_SUBS[sub],
      source_function,
      flags=re.MULTILINE,
    )
  return source_function.strip()


if __name__ == "__main__":
  # The main function AWS Lambda will directly invoke
  source_function = edit_source_function(inspect.getsource(images_by_date))

  # Order all the required external code needed: helper functions, classes and source function
  all_functions = [
    inspect.getsource(DateInfo),
    inspect.getsource(build_result),
    inspect.getsource(calculate_date),
    source_function,
  ]

  # Save a .py file of our Lambda function code (mainly for verification purposes)
  with open("aws/index.py", "w") as f:
    f.write(LAMBDA_LIBRARIES + "\n")  # Libaries defined as constants
    f.write(LAMBDA_SETUP + "\n")
    f.write("\n".join(all_functions) + "\n\n")  # Functions retrieved from source code
    f.write(LAMBDA_FUNC)

  # Following documentation from here:
  # https://www.mongodb.com/developer/products/atlas/awslambda-pymongo/
  subprocess.run("mkdir dependencies", shell=True, cwd=CWD)
  subprocess.run(
    "pip install --upgrade --target ./dependencies pymongo", shell=True, cwd=CWD
  )
  shutil.make_archive("aws", "zip", "aws/dependencies")
  zf = zipfile.ZipFile("aws.zip", "a")
  zf.write("aws/index.py", "index.py")
  zf.close()
  print("aws.zip successfully saved at root directory!")
