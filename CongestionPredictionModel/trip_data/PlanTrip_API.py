
import os
import requests
from groq import Groq
from dotenv import load_dotenv
import traceback
import json
import re
from trip_data.CovertAddressToCoord import geocode
from trip_data.match_cache import fuzzy_match_place_with_aliases, match_image_in_general
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
        client = Groq(api_key=GROQ_API_KEY)

        # 2. Compose prompt (very lightweight — low token cost)
        prompt = f"""
        You are a trip planning assistant specializing in Ho Chi Minh City. 
        Based on the user's request below, create a detailed, optimized travel itinerary for one or multiple days.

        User request: "{user_query}"

        places to eat, ALWAYS provide the actual official restaurant names (prefer Vietnamese names if available) and avoid generic labels like "local restaurant." 
        Include a variety of attractions such as cultural sites, landmarks, markets, dining spots, and entertainment options relevant to the user's interests. 

        ROUTE OPTIMIZATION RULES:
        - The itinerary MUST follow a geographically optimized path.
        - Order the locations so that the trip goes in a continuous direction without backtracking.
        - Start from the first activity of the day, then choose the next closest location.
        - Continue selecting the next closest point until all stops are arranged.
        - NEVER jump back and forth across different districts.
        - Minimize total travel time between consecutive points.
        - If two locations are similar distance, prioritize the one that matches the natural movement direction of the route.


        Output rules:
        - Return ONLY a valid JSON object
        - NO markdown, no explanation, no introduction
        - City: Ho Chi Minh City
        - For each itinerary item include:
            - place: official name (Vietnamese if known)
            - aliases: an array of other common names (may be empty)
            - address: an exact, specific address if possible

        - IMAGE CLASSIFICATION RULES (Strictly follow specifically for Image Mapping):
                For every location, you MUST analyze and output these 3 fields:
                1. "root_category": Choose ONE [restaurant, hotel, landmarks]
                2. "image_type": Choose ONE best fit:
                - Restaurant: [banhmi, pho, comtam, bunbo, hutieu, banhxeo, drinking, cafe, trasua, general]
                - Hotel: [villa, homestay, apartment, motel, general]
                - Landmark: [market, mall, temple, street, street_food_area, park, general]
            *Note: If a place doesn't fit a specific type perfectly, use 'general'.*
        
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
            "cost": "string",
            "root_category": "string",
            "image_type": "string"
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
                result = geocode(item["address"] + ", thành phố Hồ Chí Minh, Việt Nam")
                if result:
                    item["lat"] = result["lat"]
                    item["lng"] = result["lng"]
                item["image_url"] = match_image_in_general(item)
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
# ------------------------------------------------------------
# Optional test (Thay thế đoạn cuối file bằng đoạn này)
# ------------------------------------------------------------
if __name__ == "__main__":
    import json
    import os

    # 1. Load dữ liệu từ file combined_locations.json
    # (Giả sử file json nằm cùng thư mục với file code này)
    json_path = "combined_locations.json"
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 2. Tạo danh sách DB_ITEMS (gộp nhà hàng, địa điểm, khách sạn lại)
        DB_ITEMS = []
        DB_ITEMS.extend(data.get("restaurants", []))
        DB_ITEMS.extend(data.get("landmarks", []))
        DB_ITEMS.extend(data.get("hotels", []))
        
        print(f"✅ Đã nạp {len(DB_ITEMS)} địa điểm từ database.")

        # 3. Tạo biến TOKEN_INDEX giả (để code không bị lỗi thiếu tham số)
        # (Nếu muốn tính năng tìm kiếm chính xác hơn thì cần import hàm build index)
        TOKEN_INDEX = {} 

        # 4. Gọi hàm với ĐẦY ĐỦ 3 tham số
        query = "Tôi muốn đi chơi với 1 tiếng, ăn uống và thăm các địa điểm nổi tiếng, ăn bánh xèo, uống trà sữa."
        
        # --- SỬA LỖI TẠI ĐÂY: Truyền đủ 3 biến ---
        plan = generate_trip_plan(query, DB_ITEMS, TOKEN_INDEX)
        
        # print(json.dumps(plan, ensure_ascii=False, indent=4))
    
    else:
        print(f"❌ Lỗi: Không tìm thấy file '{json_path}'. Hãy chạy file Create_dataset_json_for_API.py trước!")
