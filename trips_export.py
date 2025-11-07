import os
import io
import csv
import json
import gzip
import zlib
import math

RAW_STATIONS = os.path.join("raw", "stations.xyz")
OUT_RAW_STATIONS = os.path.join("out", "stations_hcm.raw.json")
STOPS_CSV = os.path.join("out", "stops.csv")
OUT_DIR = "out"
DEST = os.path.join(OUT_DIR, "trips.csv")

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
        with open(path, "r", encoding="utf-8") as fr:
            obj = json.load(fr)
    return obj

def _first(d: dict, keys):
    for k in keys:
        if k in d:
            return d[k]
    return None

def _to_int(v, default=None):
    try:
        return int(v)
    except Exception:
        try:
            return int(float(str(v).strip()))
        except Exception:
            return default

def _to_float(v, default=None):
    try:
        return float(v)
    except Exception:
        try:
            return float(str(v).strip())
        except Exception:
            return default

def iter_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for it in obj:
            yield from iter_dicts(it)

def haversine_m(lat1, lon1, lat2, lon2):
    # meters
    R = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2.0)**2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return R * c

def load_station_coords_from_stops_csv():
    coords = {}
    if not os.path.exists(STOPS_CSV):
        return coords
    with open(STOPS_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = row.get("stopId")
            lat = _to_float(row.get("lat"))
            lng = _to_float(row.get("lng"))
            if sid and lat is not None and lng is not None:
                coords[sid] = (lat, lng)
    return coords

def extract_records_and_coords(stations_obj):
    """
    Returns:
      records: list of {routeId, direction, order, stationId, distanceHint}
      coords: dict[stationId] = (lat, lng)
    """
    records = []
    coords = {}

    for d in iter_dicts(stations_obj):
        # skip pure shape segments
        if "pathPoints" in d and not any(k in d for k in ("Lat","lat","Lng","lng","StationId","stationId")):
            continue

        rid = _first(d, ("RouteId","routeId"))
        sid = _first(d, ("StationId","stationId","StopId","stopId","id","sid"))
        order = _first(d, ("StationOrder","stationOrder","Order","order","StopOrder","stopOrder"))
        direction = _first(d, ("StationDirection","stationDirection","Direction","direction","dir"))

        # coordinates present in this object?
        lat = _first(d, ("Lat","lat","latitude","y"))
        lng = _first(d, ("Lng","lng","longitude","x"))
        if (lat is None or lng is None) and isinstance(d.get("location"), dict):
            lat = _first(d["location"], ("Lat","lat","latitude","y"))
            lng = _first(d["location"], ("Lng","lng","longitude","x"))
        lat = _to_float(lat)
        lng = _to_float(lng)
        if sid is not None and lat is not None and lng is not None:
            coords[str(sid)] = (lat, lng)

        # distance hint if already provided by dataset
        dist_hint = _first(d, ("DistanceToNext","distanceToNext","Distance","distance"))

        # only keep record rows that look like a route-stop mapping
        if rid is not None and sid is not None and order is not None:
            records.append({
                "routeId": str(rid),
                "direction": _to_int(direction, 0),
                "order": _to_int(order, 0),
                "stationId": str(sid),
                "distanceHint": _to_float(dist_hint),
            })

    return records, coords

def build_trips(records, coords_index):
    """
    Build rows: routeId, stopSequence, stopId, distanceToNextStop
    Grouped by (routeId, direction), ordered by 'order'.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for r in records:
        groups[(r["routeId"], r["direction"])].append(r)

    rows = []
    for (rid, direction), lst in groups.items():
        lst.sort(key=lambda r: (r["order"], r["stationId"]))
        for i, cur in enumerate(lst):
            stop_seq = cur["order"]
            stop_id = cur["stationId"]
            # prefer provided distance hint if available and positive
            dist_m = cur["distanceHint"] if (cur["distanceHint"] is not None and cur["distanceHint"] >= 0) else None

            if dist_m is None:
                if i + 1 < len(lst):
                    nxt = lst[i + 1]
                    c1 = coords_index.get(stop_id)
                    c2 = coords_index.get(nxt["stationId"])
                    if c1 and c2:
                        dist_m = haversine_m(c1[0], c1[1], c2[0], c2[1])
                else:
                    dist_m = 0.0  # last stop

            rows.append({
                "routeId": rid,
                "stopSequence": stop_seq,
                "stopId": stop_id,
                "distanceToNextStop": int(round(dist_m)) if dist_m is not None else ""
            })
    # stable ordering
    rows.sort(key=lambda r: (r["routeId"], r["stopSequence"], r["stopId"]))
    return rows

def main():
    # pick source
    source = RAW_STATIONS if os.path.exists(RAW_STATIONS) else OUT_RAW_STATIONS
    if not os.path.exists(source):
        raise SystemExit("No stations source found (raw/stations.xyz or out/stations_hcm.raw.json)")

    stations_obj = load_json_any(source)

    # collect records and in-file coordinates
    records, coords = extract_records_and_coords(stations_obj)

    # augment with stops.csv coordinates if present
    if os.path.exists(STOPS_CSV):
        coords.update(load_station_coords_from_stops_csv())

    if not records:
        print("No route-stop mappings found. Inspect out/stations_hcm.raw.json to confirm key names (RouteId, StationId, StationOrder).")
        return

    trips = build_trips(records, coords)

    with open(DEST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["routeId","stopSequence","stopId","distanceToNextStop"])
        w.writeheader()
        for r in trips:
            w.writerow(r)

    print(f"Wrote {len(trips)} trip rows -> {DEST}")

if __name__ == "__main__":
    main()