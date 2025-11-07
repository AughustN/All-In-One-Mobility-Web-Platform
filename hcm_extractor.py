import os
import io
import csv
import json
import gzip
import zlib
import argparse
import requests
from urllib.parse import urlparse, urlencode

DECRYPTED_FILE = "busmap_decrypted_data.json"
OUT_DIR = "out"
RAW_DIR = "raw"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

def load_decrypted():
    with open(DECRYPTED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_hcm_region(decrypted_items):
    for it in decrypted_items:
        if it.get("url", "").endswith("/web/public/region/list"):
            regions = it.get("data", [])
            for r in regions:
                if r.get("code") == "hcm":
                    return r
    return None

def dl(url, dest):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest

def try_parse_json_bytes(b):
    # Try plain JSON
    try:
        return json.loads(b.decode("utf-8"))
    except Exception:
        pass
    # Try gzip -> JSON
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(b)) as g:
            data = g.read().decode("utf-8")
            return json.loads(data)
    except Exception:
        pass
    # Try zlib -> JSON
    try:
        uz = zlib.decompress(b)
        return json.loads(uz.decode("utf-8"))
    except Exception:
        pass
    return None

def load_raw_json(path):
    with open(path, "rb") as f:
        b = f.read()
    obj = try_parse_json_bytes(b)
    if obj is None:
        raise ValueError(f"Cannot parse {path} as JSON/gzip-json/zlib-json")
    return obj

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def normalize_routes(routes_raw):
    rows = []
    for r in routes_raw if isinstance(routes_raw, list) else routes_raw.get("routes", []):
        rid = r.get("id") or r.get("routeId") or r.get("rid")
        code = r.get("code") or r.get("routeNo") or r.get("shortName") or r.get("name")
        name = r.get("name") or r.get("title") or r.get("longName") or r.get("displayName")
        rtype = r.get("routeType") or r.get("type")
        operator = r.get("operator") or r.get("agency") or r.get("company")
        rows.append({
            "routeId": rid,
            "code": code,
            "name": name,
            "routeType": rtype,
            "operator": operator,
        })
    return rows

def normalize_stations(stations_raw):
    rows = []
    src = stations_raw if isinstance(stations_raw, list) else stations_raw.get("stations", [])
    for s in src:
        sid = s.get("id") or s.get("stationId") or s.get("sid")
        name = s.get("stationName") or s.get("name") or s.get("title")
        lat = s.get("lat") or s.get("latitude") or s.get("y")
        lng = s.get("lng") or s.get("longitude") or s.get("x")
        rows.append({
            "stationId": sid,
            "stationName": name,
            "lat": lat,
            "lng": lng,
        })
    return rows

def guess_station_sequences(routeinfo_raw, known_station_ids):
    """
    Try to derive ordered station sequences per route/direction from routeinfo structures.
    This is heuristic across possible key names.
    """
    rows = []
    items = routeinfo_raw if isinstance(routeinfo_raw, list) else routeinfo_raw.get("routeInfos") or routeinfo_raw.get("items") or []
    candidate_keys = ["stations", "stationIds", "stopIds", "stops", "pathStations", "seqStations"]
    dir_keys = ["direction", "dir", "direction_id", "d"]
    rid_keys = ["routeId", "rid", "id"]

    for it in items:
        # route id
        rid = None
        for k in rid_keys:
            if k in it:
                rid = it[k]
                break
        # direction
        direction = 0
        for k in dir_keys:
            if k in it:
                direction = it.get(k) or 0
                break
        # station list
        station_list = None
        for k in candidate_keys:
            val = it.get(k)
            if isinstance(val, list) and val:
                # filter only ints that look like station ids
                ints = [v for v in val if isinstance(v, int)]
                if ints and (len(set(ints).intersection(known_station_ids)) / len(ints) > 0.3):
                    station_list = ints
                    break
        if station_list:
            for seq, sid in enumerate(station_list, start=1):
                rows.append({
                    "routeId": rid,
                    "direction": direction,
                    "seq": seq,
                    "stationId": sid
                })
    return rows

def fetch_timeline(apiRouteTimeline, route_id, region_code="hcm"):
    # Common patterns: ?regionCode=hcm&routeId=XYZ
    params = {"regionCode": region_code, "routeId": route_id}
    url = f"{apiRouteTimeline}?{urlencode(params)}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return try_parse_json_bytes(r.content) or {}

def fetch_vehicles(apiVehicle, region_code="hcm", route_id=None):
    # Common patterns:
    #   ?regionCode=hcm
    #   ?regionCode=hcm&routeId=XYZ
    params = {"regionCode": region_code}
    if route_id:
        params["routeId"] = route_id
    url = f"{apiVehicle}?{urlencode(params)}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return try_parse_json_bytes(r.content) or {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch-timeline", type=int, default=0, help="Fetch timeline for N routes (0=skip)")
    parser.add_argument("--fetch-vehicles", action="store_true", help="Fetch live vehicles snapshot for all routes")
    args = parser.parse_args()

    items = load_decrypted()
    hcm = get_hcm_region(items)
    if not hcm:
        raise SystemExit("Cannot find HCM region in busmap_decrypted_data.json")

    routes_url = hcm.get("apiRoutes")
    routeinfo_url = hcm.get("apiRouteinfo")
    stations_url = hcm.get("apiStations")
    api_route_timeline = hcm.get("apiRouteTimeline")
    api_vehicle = hcm.get("apiVehicle")

    print(f"Static: routes={routes_url} routeinfo={routeinfo_url} stations={stations_url}")

    # Download static catalogs
    paths = {}
    for key, url in [("routes", routes_url), ("routeinfo", routeinfo_url), ("stations", stations_url)]:
        if not url:
            print(f"Missing {key} URL")
            continue
        fname = os.path.basename(urlparse(url).path) or f"{key}.bin"
        dest = os.path.join(RAW_DIR, fname)
        if not os.path.exists(dest):
            print(f"Downloading {key} -> {dest}")
            dl(url, dest)
        else:
            print(f"Using cached {dest}")
        paths[key] = dest

    # Parse static
    routes_raw = load_raw_json(paths["routes"]) if "routes" in paths else []
    routeinfo_raw = load_raw_json(paths["routeinfo"]) if "routeinfo" in paths else []
    stations_raw = load_raw_json(paths["stations"]) if "stations" in paths else []

    # Persist raw decoded JSON for inspection
    write_json(os.path.join(OUT_DIR, "routes_hcm.raw.json"), routes_raw)
    write_json(os.path.join(OUT_DIR, "routeinfo_hcm.raw.json"), routeinfo_raw)
    write_json(os.path.join(OUT_DIR, "stations_hcm.raw.json"), stations_raw)

    # Normalize CSVs
    routes_rows = normalize_routes(routes_raw)
    stations_rows = normalize_stations(stations_raw)
    write_csv(os.path.join(OUT_DIR, "routes_hcm.csv"), ["routeId","code","name","routeType","operator"], routes_rows)
    write_csv(os.path.join(OUT_DIR, "stations_hcm.csv"), ["stationId","stationName","lat","lng"], stations_rows)

    # Try to derive ordered station sequences
    known_ids = {r.get("stationId") for r in stations_rows if r.get("stationId") is not None}
    route_stations_rows = guess_station_sequences(routeinfo_raw, known_ids)
    if route_stations_rows:
        write_csv(os.path.join(OUT_DIR, "route_stations_hcm.csv"), ["routeId","direction","seq","stationId"], route_stations_rows)
        print(f"Wrote {len(route_stations_rows)} route-station rows")
    else:
        print("Could not derive route-station sequences heuristically. Check routeinfo_hcm.raw.json to map keys.")

    # Optionally fetch timetables for first N routes
    if args.fetch_timeline and api_route_timeline:
        for r in routes_rows[:args.fetch_timeline]:
            rid = r.get("routeId")
            if not rid:
                continue
            try:
                tl = fetch_timeline(api_route_timeline, rid, "hcm")
                outp = os.path.join(OUT_DIR, f"timetable_route_{rid}.json")
                write_json(outp, tl)
                print(f"Timeline saved: {outp}")
            except Exception as e:
                print(f"Timeline fetch failed for routeId={rid}: {e}")

    # Optionally fetch a live vehicles snapshot (all routes)
    if args.fetch_vehicles and api_vehicle:
        try:
            vehicles = fetch_vehicles(api_vehicle, "hcm")
            write_json(os.path.join(OUT_DIR, "vehicles_hcm.json"), vehicles)
            print("Vehicles snapshot saved")
        except Exception as e:
            print(f"Vehicles fetch failed: {e}")

if __name__ == "__main__":
    main()