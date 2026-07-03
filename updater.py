"""
updater.py
----------
بيتأكد من وجود نسخة جديدة على GitHub Releases، وبيرجع تفاصيلها لو موجودة.
"""

import requests

APP_VERSION = "1.0.0"
GITHUB_REPO = "Ahmed-Atef-Tech/telegram-anki-bridge"


def _parse_version(v: str):
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_update():
    """بيرجع dict فيه (version, url, download_url) لو فيه نسخة أحدث على GitHub، أو None."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    resp = requests.get(url, timeout=6, headers={"Accept": "application/vnd.github+json"})
    resp.raise_for_status()
    data = resp.json()

    latest_tag = data.get("tag_name", "")
    if not latest_tag or _parse_version(latest_tag) <= _parse_version(APP_VERSION):
        return None

    download_url = None
    for asset in data.get("assets", []):
        if asset.get("name", "").lower().endswith(".exe"):
            download_url = asset.get("browser_download_url")
            break

    return {
        "version": latest_tag,
        "url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest"),
        "download_url": download_url,
    }
