import csv
import json
import unicodedata

# ---- Input CSV files ----
RESTAURANTS_CSV = "trip_data/restaurants_simple.csv"
LANDMARKS_CSV = "trip_data/landmarks_simple.csv"
HOTELS_CSV = "trip_data/hotels_simple.csv"

# ---- Output merged JSON ----
OUTPUT_JSON = "trip_data/combined_locations.json"

# Normalization function
def normalize_text(text):
    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower().strip()

    # Remove Vietnamese accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    # Replace special characters with spaces
    for ch in [",", ".", "-", "_", "/", "(", ")", "[", "]", ":", ";"]:
        text = text.replace(ch, " ")

    # Collapse multiple spaces
    text = " ".join(text.split())

    return text


def load_infor_from_csv(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            image_url = (row.get("image_local_path") or "").strip()

            lat_raw = row.get("lat")
            lng_raw = row.get("lng")

            lat_str = lat_raw.strip() if isinstance(lat_raw, str) else ""
            lng_str = lng_raw.strip() if isinstance(lng_raw, str) else ""

            if lat_str == "":
                print(f"[MISSING LAT] Line {line_number}: {row}")
            if lng_str == "":
                print(f"[MISSING LNG] Line {line_number}: {row}")
            
            norm = normalize_text(name)

            if name:
                items.append({
                    "name": name,
                    "norm": norm,
                    "image_local_path": image_url,
                    "lat": lat_str,
                    "lng": lng_str
                })
    return items


# ---- Load data ----
landmarks = load_infor_from_csv(LANDMARKS_CSV)
restaurants = load_infor_from_csv(RESTAURANTS_CSV)
hotels = load_infor_from_csv(HOTELS_CSV)


# ---- FINAL JSON ----
combined = {
    "restaurants": restaurants,
    "landmarks": landmarks,
    "hotels": hotels,
}

# ---- Save JSON ----
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=4)

print("✅ Created combined_locations.json successfully!")
print(f"- Restaurants: {len(restaurants)}")
print(f"- Landmarks:   {len(landmarks)}")
print(f"- Hotels:      {len(hotels)}")
