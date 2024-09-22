import requests

URL = "https://o7hgv46qcf7swox3ygn53tayay0zzhgl.lambda-url.us-east-1.on.aws"
response = requests.get(f"{URL}?day=0")
if response.ok:
  print(response.headers)
else:
  print("Error:", response.text)
