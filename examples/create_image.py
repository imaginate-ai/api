import requests
import mimetypes
from image_handler_client.schemas.image_info import ImageStatus
import os
from dotenv import load_dotenv

# Quick script to test our POST image/create endpoint
# See also imaginate_api/templates/index.html for other ways to call the same endpoint
load_dotenv()

# First type of call (via bytes)
IMAGE = "examples/images/pokemon.png"
URL = "http://127.0.0.1:5000/image/create"
MIME = mimetypes.guess_type(IMAGE)
PEXELS_BASE_URL = "https://api.pexels.com/v1"

if not MIME:
  print("Could not guess file type")
  exit(1)
files = {"file": (IMAGE.split("/")[-1], open(IMAGE, "rb"), MIME[0])}
response = requests.post(
  URL,
  {"real": True, "date": 1, "theme": "pokemon", "status": ImageStatus.UNVERIFIED.value},
  files=files,
)
if response.ok:
  print(f"Endpoint returned: {response.json()}")
else:
  print(f"Endpoint returned: {response.status_code}")

# Second type of call (via Pexels)
QUERY = "pokemon"
TOTAL_RESULTS = 1  # Max per page is 80: https://www.pexels.com/api/documentation/#photos-search__parameters__per_page
response = requests.get(
  f"{PEXELS_BASE_URL}/search",
  params={"query": QUERY, "per_page": TOTAL_RESULTS},
  headers={"Authorization": os.getenv("PEXELS_TOKEN")},
)
response_data = response.json()
if TOTAL_RESULTS > response_data["total_results"]:
  print(f"Requested {TOTAL_RESULTS} > Total {response_data['total_results']}")
photos_data = response_data["photos"]
for photo in photos_data:
  response = requests.post(
    URL,
    {
      "url": photo["src"]["original"],
      "real": True,
      "date": 1,
      "theme": "pokemon",
      "status": ImageStatus.UNVERIFIED.value,
    },
    files=files,
  )
  if response.ok:
    print(f"Endpoint returned: {response.json()}")
  else:
    print(f"Endpoint returned: {response.status_code}")
