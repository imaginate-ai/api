import requests
import mimetypes

# Quick script to test our POST create/ endpoint
IMAGE = "../samples/discord.png"
URL = "http://127.0.0.1:5000/create"
MIME = mimetypes.guess_type(IMAGE)

if not MIME:
    print("Could not guess file type")
    exit(1)

files = {"file": (IMAGE.split("/")[-1], open(IMAGE, "rb"), MIME[0])}
req = requests.post(URL, {
    "real": True,
    "date": 0,
    "theme": "placeholder"
}, files=files)
print(req.status_code)
print(req.json())
