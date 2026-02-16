import requests


def is_vpn(ip: str) -> bool:
    """
    Heurística simples via ip-api (proxy/hosting).
    """
    try:
        r = requests.get(f"https://ip-api.com/json/{ip}?fields=proxy,hosting", timeout=5)
        data = r.json()
        return bool(data.get("proxy") or data.get("hosting"))
    except Exception:
        return False
