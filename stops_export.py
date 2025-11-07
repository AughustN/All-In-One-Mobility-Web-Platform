import os
import io
import json
import csv
import gzip
import zlib

RAW_STATIONS = os.path.join("raw", "stations.xyz")
OUT_RAW_STATIONS = os.path.join("out", "stations_hcm.raw.json")
OUT_DIR = "out"
OUT_CSV = os.path.join(OUT_DIR, "stops.csv")

os.makedirs(OUT_DIR, exist_ok=True)

def try_parse_json_bytes(b: bytes):
    # plain JSON
    try:
        return json.loads(b.decode("utf-8"))
    except Exception:
        pass
    # gzip JSON
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(b)) as g:
            return json.loads(g.read().decode("utf-8"))
    except Exception:
        pass
    # zlib JSON
    try:
        return json.loads(zlib.decompress(b).decode("utf-8"))
    except Exception:
        pass
    return None

def load_json_any(path: str):
    with open(path, "rb") as f:
        b = f.read()
    obj = try_parse_json_bytes(b)
    if obj is None:
        # last resort: text JSON
        with open(path, "r", encoding="utf-8") as fr:
            return json.load(fr)
    return obj

def _first(d: dict, keys):
    for k in keys:
        if k in d:
            return d[k]
    return None

def _to_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        try:
            return float(str(v).strip())
        except Exception:
            return None

def iter_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for it in obj:
            yield from iter_dicts(it)

def extract_stops(obj):
    rows = []
    seen_ids = set()
    seen_key = set()

    for d in iter_dicts(obj):
        # skip shape-only entries
        if "pathPoints" in d and not any(k in d for k in ("Lat","lat","Lng","lng","location")):
            continue

        stop_id = _first(d, ("StationId","stationId","StopId","stopId","id","sid"))
        name = _first(d, ("StationName","stationName","StopName","stopName","name","title"))

        lat = _first(d, ("Lat","lat","latitude","y"))
        lng = _first(d, ("Lng","lng","longitude","x"))

        # sometimes wrapped in "location": {"lat":...,"lng":...}
        if (lat is None or lng is None) and isinstance(d.get("location"), dict):
            lat = _first(d["location"], ("Lat","lat","latitude","y"))
            lng = _first(d["location"], ("Lng","lng","longitude","x"))

        lat = _to_float(lat)
        lng = _to_float(lng)

        # require coordinates and some identity (id or name)
        if lat is None or lng is None:
            continue
        if stop_id is None and not name:
            continue

        # dedupe: prefer id-based, else coord+name
        if stop_id is not None:
            key = ("id", stop_id)
            if key in seen_ids:
                continue
            seen_ids.add(key)
        else:
            key = ("geo", round(lat, 6), round(lng, 6), (name or "").strip())
            if key in seen_key:
                continue
            seen_key.add(key)

        rows.append({
            "stopId": stop_id if stop_id is not None else "",
            "stopName": (name or "").strip(),
            "lat": lat,
            "lng": lng,
        })
    return rows

def main():
    source = None
    if os.path.exists(RAW_STATIONS):
        source = RAW_STATIONS
    elif os.path.exists(OUT_RAW_STATIONS):
        source = OUT_RAW_STATIONS
    else:
        raise SystemExit("No stations source found (raw/stations.xyz or out/stations_hcm.raw.json)")

    data = load_json_any(source)
    stops = extract_stops(data)
    if not stops:
        print("No stops found. Inspect out/stations_hcm.raw.json to confirm key names.")
        return

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stopId","stopName","lat","lng"])
        w.writeheader()
        for r in stops:
            w.writerow(r)

    print(f"Wrote {len(stops)} stops -> {OUT_CSV}")

if __name__ == "__main__":
    main()