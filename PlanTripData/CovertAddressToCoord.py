import requests
import time
import hashlib

# ----------------------------
# CONFIG
# ----------------------------
GEOAPIFY_API_KEY = "apiKey"   # <-- put your key here

USE_CACHE = True
CACHE = {}     # memory cache for testing


# ==========================================================
# HASH ADDRESS → for caching
# ==========================================================
def cache_key(address: str):
    return hashlib.sha256(address.lower().strip().encode()).hexdigest()


# ==========================================================
# Geoapify primary geocoder
# ==========================================================
def geocode_geoapify(address: str):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "apiKey": GEOAPIFY_API_KEY,
        "text": address,
        "lang": "vi"
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            return None
        
        data = r.json()
        if not data.get("features"):
            return None
        
        feature = data["features"][0]
        props = feature["properties"]
        
        return {
            "lat": props.get("lat"),
            "lng": props.get("lon"),
            "source": "geoapify"
        }

    except Exception:
        return None


# ==========================================================
# OSM Nominatim fallback geocoder (1 req/sec required)
# ==========================================================
def geocode_nominatim(address: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 0,
        "limit": 1
    }

    headers = {
        "User-Agent": "TripPlanner/1.0 (your_email@example.com)"
    }

    try:
        time.sleep(1)  # MUST sleep 1 sec for OSM limit
        r = requests.get(url, params=params, headers=headers, timeout=5)
        if r.status_code != 200:
            return None
        
        res = r.json()
        if not res:
            return None

        return {
            "lat": float(res[0]["lat"]),
            "lng": float(res[0]["lon"]),
            "source": "nominatim"
        }

    except Exception:
        return None


# ==========================================================
# Main geocoder: try Geoapify → fallback to OSM
# ==========================================================
def geocode(address: str):
    key = cache_key(address)

    # Check cache
    if USE_CACHE and key in CACHE:
        return CACHE[key]

    # Try Geoapify first
    geo = geocode_geoapify(address)
    if geo:
        CACHE[key] = geo
        return geo

    # Try fallback (OSM)
    osm = geocode_nominatim(address)
    if osm:
        CACHE[key] = osm
        return osm

    return None


# ==========================================================
# TESTING
# ==========================================================
if __name__ == "__main__":
    tests = [
        "Pho 2000",
        "1-3 Trần Hưng Đạo, Phường Phạm Ngũ Lão, Quận 1, Thành phố Hồ Chí Minh",
    ]

    for t in tests:
        print("Searching:", t)
        result = geocode(t)
        print("Result:", result)
        print("-" * 40)
