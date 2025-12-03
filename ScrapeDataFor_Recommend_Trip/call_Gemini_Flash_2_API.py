from google import genai
import os, json

# 1. Configure client
client = genai.Client(api_key="APIKEY_HERE")
# OR: client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Load summary JSON
with open("combined_locations.json", "r", encoding="utf-8") as f:
    locations = json.load(f)

restaurants = [loc["name"] for loc in locations["restaurants"]]
landmarks   = [loc["name"] for loc in locations["landmarks"]]

# 3. Build prompt (Vietnamese)
user_query = "Lập lịch trình du lịch 1 ngày ở TP.HCM cho người thích ẩm thực Nhật Bản và Hàn Quốc, tổng giá không quá 1 triệu VND, bắt đầu từ quận 1."

prompt = f"""
Bạn là một trợ lý lập kế hoạch du lịch. 
Đây là danh sách địa điểm hợp lệ:
Nhà hàng:
{', '.join(restaurants)}

Điểm tham quan:
{', '.join(landmarks)}

Yêu cầu của người dùng: "{user_query}"

Hãy tạo lịch trình tối ưu thời gian và khoảng cách, 
và CHỈ sử dụng các địa điểm trong danh sách trên.

Trả về danh sách tên địa điểm theo thứ tự tham quan.
"""

# 4. Call Gemini API
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt
)

print("=== KẾ HOẠCH DU LỊCH ===")
print(response.text)

client.close()
