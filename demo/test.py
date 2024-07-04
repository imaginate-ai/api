import mimetypes
import sys

import requests

# Quick script to test our POST create/ endpoint
IMAGE = "../samples/discord.png"
URL = "http://127.0.0.1:5000/create"
MIME = mimetypes.guess_type(IMAGE)

if not MIME:
  print("Could not guess file type")
  sys.exit(1)

# Use with statement to ensure the file is properly closed after use
with open(IMAGE, "rb") as file:
  files = {"file": (IMAGE.rsplit("/", maxsplit=1)[-1], file, MIME[0])}
  req = requests.post(
    URL, {"real": True, "date": 0, "theme": "placeholder"}, files=files, timeout=10
  )

print(req.status_code)
print(req.json())
