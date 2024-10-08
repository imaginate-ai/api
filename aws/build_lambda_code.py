import sys

sys.path.append(
  "."
)  # Adds all root directories as a package, which in our case is: imaginate_api
import inspect
import re
import os
import subprocess
import shutil
import zipfile
from imaginate_api.date.routes import images_by_date
from imaginate_api.utils import build_result, calculate_date
from imaginate_api.schemas.date_info import DateInfo


ENV = "prod"
FRONTEND_URL = "https://playimaginate.com"
DIR = "aws"
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
LAMBDA_SETUP = f"""db_name = 'imaginate_{ENV}' # Database names: ['imaginate_dev', 'imaginate_prod']
conn_uri = os.environ.get('MONGO_TOKEN')
client = MongoClient(conn_uri)
db = client[db_name]
fs = GridFS(db)
allowed_origins = [
    "vermillion-biscuit-931b88.netlify.app"
]
"""
LAMBDA_FUNC = f"""def handler(event, context):
    print("Headers:", event['headers'])
    origin = event['headers'].get('origin', '')
    cors_origin = "{FRONTEND_URL}" # Default CORS origin
    for allowed_origin in allowed_origins:
        if allowed_origin in origin:
            cors_origin = origin
            break
    headers = {{
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }}
    if event and 'queryStringParameters' in event and event['queryStringParameters'] and 'day' in event['queryStringParameters']:
        result = images_by_date(event['queryStringParameters']['day'])
        result['headers'] = headers
        return result
    else:
        return {{'statusCode': HTTPStatus.BAD_REQUEST, 'body': json.dumps('Invalid date'), 'headers': headers}}
"""
LAMBDA_SUBS = {
  "abort\\(HTTPStatus.BAD_REQUEST": "return {'statusCode': HTTPStatus.BAD_REQUEST, 'body': json.dumps('Invalid date')}",
  "abort\\(HTTPStatus.NOT_FOUND": "return {'statusCode': HTTPStatus.NOT_FOUND, 'body': json.dumps('Empty database')}",
  "@bp.route": "",  # Remove function decorator entirely
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

  # Save our Lambda function code
  with open(f"{DIR}/index.py", "w") as f:
    f.write(LAMBDA_LIBRARIES + "\n")  # Libaries defined as constants
    f.write(LAMBDA_SETUP + "\n")
    f.write("\n".join(all_functions) + "\n\n")  # Functions retrieved from source code
    f.write(LAMBDA_FUNC)

  # Format our Lambda funtion code with ruff before packaging
  subprocess.run("ruff format index.py", shell=True, cwd=CWD)

  # Following documentation from here:
  # https://www.mongodb.com/developer/products/atlas/awslambda-pymongo/
  subprocess.run("mkdir dependencies", shell=True, cwd=CWD)
  subprocess.run(
    "pip install --upgrade --target ./dependencies pymongo", shell=True, cwd=CWD
  )
  shutil.make_archive(f"{DIR}/aws", "zip", f"{DIR}/dependencies")
  zf = zipfile.ZipFile(f"{DIR}/aws.zip", "a")
  zf.write(f"{DIR}/index.py", "index.py")
  zf.close()
  print(f"aws.zip successfully saved in {DIR} directory")
