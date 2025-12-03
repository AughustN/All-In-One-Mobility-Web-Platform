import csv
import json

# ---- Input CSV files ----
RESTAURANTS_CSV = "restaurants_pasgo_simple.csv"
LANDMARKS_CSV = "landmarks_simple.csv"

# ---- Output merged JSON ----
OUTPUT_JSON = "combined_locations.json"

def load_names_from_csv(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if name:
                items.append({"name": name})
    return items

# ---- Load restaurant names ----
restaurants = load_names_from_csv(RESTAURANTS_CSV)

# ---- Load landmark names ----
landmarks = load_names_from_csv(LANDMARKS_CSV)

# ---- Merge structure ----
combined = {
    "restaurants": restaurants,
    "landmarks": landmarks
}

# ---- Save JSON ----
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(combined, f, ensure_ascii=False, indent=4)

print("✅ Created combined_locations.json successfully!")
print(f"- Restaurants: {len(restaurants)}")
print(f"- Landmarks:   {len(landmarks)}")
