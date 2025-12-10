
import os
import requests
from groq import Groq
from dotenv import load_dotenv
import traceback
import json
import re
from trip_data.CovertAddressToCoord import geocode
from trip_data.match_cache import fuzzy_match_place_with_aliases


# ------------------------------------------------------------
# Clean JSON returned by Gemini
# ------------------------------------------------------------
def extract_json(text: str):
    """
    Extract the first valid JSON object by counting braces.
    Safest method for messy LLM output.
    """
    start = text.find("{")
    if start == -1:
        return None

    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1

        if brace_count == 0:
            candidate = text[start:i+1]
            # Validate JSON
            try:
                json.loads(candidate)
                return candidate
            except:
                continue

    return None


# ------------------------------------------------------------
# Main trip-generation function
# ------------------------------------------------------------
def generate_trip_plan(user_query: str, DB_ITEMS, TOKEN_INDEX):
    client = None
    try:
        # 1. Setup Groq client
        client = Groq(api_key="apiKey")

        # 2. Compose prompt (very lightweight — low token cost)
        prompt = f"""
        You are a trip planning assistant for Ho Chi Minh City.
        Based on the user's request below, create a travel plan.

        User request: "{user_query}"

        When suggesting places to eat, ALWAYS return the actual restaurant names (no generic labels). 
        Prefer places that are near one another.

        Output rules:
        - Return ONLY a valid JSON object
        - NO markdown, no explanation, no introduction
        - City: Ho Chi Minh City
        - For each itinerary item include:
            - place: official name (Vietnamese if known)
            - aliases: an array of other common names (may be empty)
            - short_address: a short address or district if possible
        - JSON format:

        {{
        "title": "string",
        "itinerary": [
            {{
            "time": "string",
            "activity": "string",
            "place": "string",
            "aliases": ["string", "..."],
            "address": "string",
            "cost": "string"
            }}
        ],
        "totalCost": 0
        }}
        """

        completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

        # ✅ Groq uses .choices[0].message.content
        raw_text = completion.choices[0].message.content.strip()

        clean = extract_json(raw_text)

        # 4. Parse JSON (Gemini should output clean JSON)
        trip = json.loads(clean)

        # 5. Post-process → match each place to your DB
        for item in trip.get("itinerary", []):
            place_raw = item.get("place", "")
            matched = fuzzy_match_place_with_aliases(place_raw, item["aliases"], DB_ITEMS, TOKEN_INDEX)

            if matched:
                item["matched"] = True
                item["db_name"] = matched["name"]
                item["lat"] = float(matched["lat"])
                item["lng"] = float(matched["lng"])
                item["image_url"] = matched["image_local_path"]
            else:

                result = geocode(item["address"] + ", Ho Chi Minh City, Vietnam")
                if result:
                    item["lat"] = result["lat"]
                    item["lng"] = result["lng"]
                item["image_url"] = None
                item["matched"] = False
        
        print(json.dumps(trip, ensure_ascii=False, indent=4))
        return trip

    except json.JSONDecodeError as e:
        print("⚠️ JSON decode error:", e)
        print("Raw:", raw_text[:300])
        return {"error": "Invalid JSON from Gemini"}

    except Exception as e:
        print("❌ Error in generate_trip_plan:", e)
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        if client:
            client.close()


# ------------------------------------------------------------
# Optional test
# ------------------------------------------------------------
if __name__ == "__main__":
    query = "Tôi muốn đi tham quan Sài Gòn 1 ngày, ăn uống và thăm các địa điểm nổi tiếng."
    plan = generate_trip_plan(query)
    print(json.dumps(plan, ensure_ascii=False, indent=4))
