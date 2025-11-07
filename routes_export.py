import os
import io
import re
import csv
import json
import gzip
import zlib

OUT_DIR = "out"
SRC_PREFS = [
    os.path.join(OUT_DIR, "routeinfo_hcm.raw.json"),
    os.path.join("raw", "routeinfo.xyz"),
]
DEST = os.path.join(OUT_DIR, "routes.csv")
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

def pick_source():
    for p in SRC_PREFS:
        if os.path.exists(p):
            return p
    raise SystemExit("No routeinfo source found (out/routeinfo_hcm.raw.json or raw/routeinfo.xyz)")

def parse_fee(val):
    if val is None:
        return ""
    digits = re.findall(r"\d+", str(val))
    return "".join(digits) if digits else ""

TIME_RE = re.compile(r"(\d{1,2}:\d{2})")

def parse_time_range(op_time):
    """
    Extract start/end HH:MM from strings like '05:30 - 20:30'.
    Returns (start, end) or ("","") if unavailable.
    """
    if not op_time:
        return "", ""
    times = TIME_RE.findall(str(op_time))
    if not times:
        return "", ""
    if len(times) == 1:
        return times[0], ""
    return times[0], times[-1]

def normalize_time_of_trip(val):
    """
    Keep minutes as text; collapse spaces around '-' if present.
    Examples:
      '50 - 55' -> '50-55'
      '80' -> '80'
    """
    if val is None:
        return ""
    s = str(val).strip()
    # Try to rebuild from numbers found (handles stray text)
    nums = re.findall(r"\d+", s)
    if not nums:
        return ""
    if len(nums) == 1:
        return nums[0]
    return f"{nums[0]}-{nums[1]}"

def iter_items(obj):
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                yield it
    elif isinstance(obj, dict):
        # common containers
        for key in ("items", "routeInfos", "routes", "data"):
            v = obj.get(key)
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict):
                        yield it

def main():
    src = pick_source()
    data = load_json_any(src)

    rows = []
    for it in iter_items(data):
        rid = it.get("RouteId")
        rno = it.get("RouteNo")
        rname = it.get("RouteName")
        if rid is None or rno is None or rname is None:
            # skip partial/summary rows (e.g., entries with only TotalTrip)
            continue

        fee = parse_fee(it.get("NormalTicket"))
        start, stop = parse_time_range(it.get("OperationTime"))
        trip = normalize_time_of_trip(it.get("TimeOfTrip"))

        rows.append({
            "routeId": rid,
            "busNumber": rno,
            "routename": rname,
            "fee": fee,                          # numeric string, e.g. 6000
            "activeStartTime": start,            # HH:MM
            "activeStopTime": stop,              # HH:MM
            "busStopSpacing(time of trip)": trip # minutes or min-max
        })

    # Write CSV
    with open(DEST, "w", encoding="utf-8", newline="") as f:
        headers = ["routeId","busNumber","routename","fee","activeStartTime","activeStopTime","busStopSpacing(time of trip)"]
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {len(rows)} routes -> {DEST}")

if __name__ == "__main__":
    main()