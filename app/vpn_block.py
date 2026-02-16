import requests

def is_vpn(ip: str):
    try:
        r = requests.get(f"https://ip-api.com/json/{ip}?fields=proxy,hosting")
        data = r.json()
        return data.get("proxy") or data.get("hosting")
    except:
        return False
