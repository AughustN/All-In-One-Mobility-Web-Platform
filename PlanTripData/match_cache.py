# matcher.py
import json
import re
import os
import pickle
from rapidfuzz import fuzz
import unidecode

CACHE_FILE = "cache/matcher_cache.pkl"
DB_JSON_PATH = "trip_data/combined_locations.json"

DB_ITEMS, TOKEN_INDEX = None, None

# ---------------------------------------------------------
# 1. Normalize text (fallback, not needed if db already has "norm")
# ---------------------------------------------------------
def normalize(s: str) -> str:
    s = unidecode.unidecode(s)         # <-- REMOVE ACCENTS
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------
# 2. Build or Load Cached Database Index
# ---------------------------------------------------------
def build_index(db):
    """
    Convert db structure into:
        DB_ITEMS = list of (id, name, norm, lat, lng, image)
        TOKEN_INDEX = {token: set(ids)}
    """
    db_items = []
    token_index = {}

    uid = 0  # auto-generated ID for indexing

    for category in ["restaurants", "landmarks", "hotels"]:
        for item in db.get(category, []):
            name = item["name"]
            norm = item.get("norm") or normalize(name)
            lat = float(item["lat"])
            lng = float(item["lng"])
            image = item["image_local_path"]

            db_items.append({
                "id": uid,
                "name": name,
                "norm": norm,
                "lat": lat,
                "lng": lng,
                "image_local_path": image
            })

            # build token index
            tokens = norm.split()
            for t in tokens:
                if t not in token_index:
                    token_index[t] = set()
                token_index[t].add(uid)

            uid += 1

    return db_items, token_index


def load_database():
    """
    Load database from JSON.
    If cache exists: load matcher_cache.pkl instead (fast).
    If not: build index and save cache.
    """
    global DB_ITEMS, TOKEN_INDEX
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            DB_ITEMS, TOKEN_INDEX = pickle.load(f)
        return True

    # No cache → load JSON normally
    with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    DB_ITEMS, TOKEN_INDEX = build_index(db)

    # Save cache for next time
    with open(CACHE_FILE, "wb") as f:
        pickle.dump((DB_ITEMS, TOKEN_INDEX), f)

    return True


# Combined fuzzy score function
def combined_score(a, b):
    """
    Combine several fuzzy metrics into one score (0-100).
    Tweak weights if needed.
    """
    a = a or ""
    b = b or ""
    s1 = fuzz.token_set_ratio(a, b)
    s2 = fuzz.partial_ratio(a, b)
    s3 = fuzz.token_sort_ratio(a, b)
    # weighted average
    score = (0.5 * s1) + (0.25 * s2) + (0.25 * s3)
    return score


# --- small manual alias map (extend it) ---
ALIASES = {
    # normalized form -> canonical normalized form
    "dinh thong nhat": "dinh doc lap",
    "bao tang lich su viet nam": "bao tang lich su thanh pho ho chi minh",
    "bao tang chien tranh": "bao tang chung tich chien tranh"
}

# utility to try alias canonicalization
def canonicalize_by_alias(norm_name):
    if norm_name in ALIASES:
        print("⚡ Using alias canonicalization:", norm_name, "→", ALIASES[norm_name])
        return ALIASES[norm_name]
    return norm_name

# ---------------------------------------------------------
# 3. Fuzzy Matching Using Token Index (FAST)
# ---------------------------------------------------------
def fuzzy_match_place_with_aliases(groq_place, groq_aliases, DB_ITEMS, TOKEN_INDEX, threshold=80):
    """
    gem_place: raw place (string) from Groq
    gem_aliases: list of alias strings (can be empty)
    gem_address: short address or district (string)

    Returns best match item or None plus score.
    """
      
    query_norm = normalize(groq_place)
    query_norm = canonicalize_by_alias(query_norm) # try alias canonicalization if any exists
    alias_norms = [canonicalize_by_alias(normalize(a)) for a in (groq_aliases or [])]

    q_tokens = set(query_norm.split())
    candidate_ids = set()

    # Gather all items whose name share at least 1 token
    for t in q_tokens:
        if t in TOKEN_INDEX:
            candidate_ids |= TOKEN_INDEX[t]

    # If no candidates from tokens → brute force fallback (still fast)
    if not candidate_ids:
        candidate_ids = range(len(DB_ITEMS))

    best_score = -1
    best_item = None

    for cid in candidate_ids:
        item = DB_ITEMS[cid]
        score_name = combined_score(query_norm, item["norm"])

        score_aliases = 0
        for an in alias_norms:
            score_aliases = max(score_aliases, combined_score(an, item["norm"]))
        
        score = max(score_name, score_aliases)

        if score > best_score:
            best_score = score
            best_item = item

    if best_score < threshold:
        return None

    print(f"✅ Match found: '{groq_place}' → '{best_item['name']}' (score: {best_score:.1f})")
    return best_item
