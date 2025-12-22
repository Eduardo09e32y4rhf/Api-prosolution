import requests

API_KEY = "SUA_CHAVE_IPQUALITYSCORE"

def is_vpn(ip: str) -> bool:
    url = f"https://ipqualityscore.com/api/json/ip/{API_KEY}/{ip}"
    data = requests.get(url, timeout=5).json()

    return any([
        data.get("vpn"),
        data.get("proxy"),
        data.get("tor"),
        data.get("hosting")
    ])
