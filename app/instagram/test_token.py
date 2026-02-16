import requests
from app.config import INSTAGRAM_ACCESS_TOKEN

url = "https://graph.facebook.com/v19.0/me"
params = {
    "access_token": INSTAGRAM_ACCESS_TOKEN
}

r = requests.get(url, params=params)
print(r.json())