import requests
import folium
import urllib.parse

from folium.plugins import PolyLineTextPath

def visualize_path_on_map(coords, start, end):
    if not coords:
        print("⚠️ Không có dữ liệu đường đi để vẽ.")
        return

    m = folium.Map(tiles="OpenStreetMap")
    m.fit_bounds([start, end])

    # Viền tối
    folium.PolyLine(coords, color="black", weight=8, opacity=0.3).add_to(m)
    # Đường chính
    route = folium.PolyLine(coords, color="blue", weight=5, opacity=0.9).add_to(m)

    # Marker bắt đầu - kết thúc
    folium.Marker(start, popup="🚩 Điểm bắt đầu", tooltip="Bắt đầu", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end, popup="🏁 Điểm đích", tooltip="Kết thúc", icon=folium.Icon(color="red", icon="flag")).add_to(m)

    m.save("route_map.html")
    print("✅ Đã lưu bản đồ: route_map.html")


def search_api(address, start_lat = None, start_lon = None):
    base_url = "https://api.tomtom.com/search/2/search/"
    encoded_address = urllib.parse.quote(address)
    url = f"{base_url}{encoded_address}.json"

    params = {
        "key": api_key,
        "countrySet": "VN",
        "limit": 10,
        "language": "vi-VN",
    }
    if start_lat is not None and start_lon is not None:
        base_url = "https://api.tomtom.com/search/2/nearbySearch/.json"
        params["lat"] = start_lat
        params["lon"] = start_lon
        params["radius"] = 5000


    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print("❌ Lỗi khi kết nối TomTom:", e)
        return None

    data = response.json()
    results = data.get("results", [])
    if not results:
        print(f"❌ Không tìm thấy địa chỉ nào cho: {address}")
        return None
    
    # Lọc chỉ lấy kết quả thuộc thành phố Hồ Chí Minh
    # Duyệt trên bản sao để an toàn khi loại bỏ phần tử khỏi danh sách gốc
    for r in results[:]:
        if ", Hồ Chí Minh" not in r["address"]["freeformAddress"]:
            results.remove(r)

    if not results:
        print(f"❌ Không tìm thấy địa chỉ nào cho: {address} ở thành phố Hồ Chí Minh")
        return None

    print(f"🔍 Kết quả tìm thấy cho '{address}':")
    for i, r in enumerate(results):
        poi_info = r.get("poi", {})
        name = poi_info.get("name", "(Không có tên riêng)")
        addr = r["address"]["freeformAddress"]
        lat = r["position"]["lat"]
        lon = r["position"]["lon"]
        print(f"{i + 1}. {name} - {addr} ({lat}, {lon})")

    while True:
        try:
            choice = int(input(f"👉 Chọn số thứ tự (1-{len(results)}): "))
            if 1 <= choice <= len(results):
                chosen = results[choice - 1]
                return {
                    "latitude": chosen["position"]["lat"],
                    "longitude": chosen["position"]["lon"]
                }
            else:
                print("⚠️ Lựa chọn không hợp lệ. Thử lại.")
        except ValueError:
            print("⚠️ Nhập số thứ tự hợp lệ.")

# ------------------- CHỌN ĐỊA CHỈ -------------------
def choose_location(api_key):
    start_address = input("📍 Nhập vị trí xuất phát hoặc vị trí hiện tại: ")
    start_location = search_api(start_address)
    if start_location is None:
        return None, None

    while True:
        print("\n🚗 Chọn cách tìm điểm đến:")
        print("1️⃣  Tìm địa điểm gần vị trí hiện tại")
        print("2️⃣  Tìm địa điểm khác (không phụ thuộc vị trí xuất phát)")
        choice = input("👉 Nhập lựa chọn (1 hoặc 2): ")
        if choice not in ["1", "2"]:
            print("⚠️ Vui lòng chọn đúng số 1 hoặc 2!")
            continue
        break

    end_address = input("\n🏁 Nhập điểm đến hoặc địa điểm muốn tìm: ")

    if choice == "1":
        end_location = search_api(end_address, start_location["latitude"], start_location["longitude"])
    else:
        end_location = search_api(end_address)

    return start_location, end_location


    


# ------------------- CHỌN PHƯƠNG TIỆN -------------------
def choose_travel_mode():
    print("\nChọn loại phương tiện:")
    print("1. Ô tô")
    print("2. Xe máy")
    print("3. Xe đạp")
    print("4. Đi bộ")
    print("5. Xe tải")
    print("6. Xe van")
    print("7. Xe taxi")
    print("8. Xe buýt")
    print("⚙️  Mặc định: Ô tô nếu không chọn hợp lệ")

    try:
        choice = int(input("👉 Chọn số (1-8): "))
    except ValueError:
        return "car"

    modes = {
        1: "car",
        2: "motorcycle",
        3: "bicycle",
        4: "pedestrian",
        5: "truck",
        6: "van",
        7: "taxi",
        8: "bus"
    }
    return modes.get(choice, "car")


# ------------------- CHỌN LOẠI ĐƯỜNG -------------------
def choose_route_type():
    print("\nChọn loại chuyến đi:")
    print("1. Nhanh nhất")
    print("2. Ngắn nhất")
    print("3. Cân bằng")
    print("4. Tiết kiệm nhiên liệu")
    print("⚙️  Mặc định: nhanh nhất nếu không chọn hợp lệ")

    try:
        choice = int(input("👉 Chọn số (1-4): "))
    except ValueError:
        return "fastest"

    types = {
        1: "fastest",
        2: "shortest",
        3: "short",
        4: "eco"
    }
    return types.get(choice, "fastest")

# ------------------- GỌI ROUTING API -------------------
def tomtom_route(start_lat, start_lon, end_lat, end_lon, api_key, travel_mode, route_type):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_lat},{start_lon}:{end_lat},{end_lon}/json"
    params = {
        "key": api_key,
        "traffic": "true",
        "routeType": route_type,
        "travelMode": travel_mode,
        "avoid": "borderCrossings"
        # "avoid": "unpavedRoads,borderCrossings"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print("❌ Lỗi khi gọi TomTom API:", e)
        return []

    data = response.json()
    if "routes" not in data or not data["routes"]:
        print("❌ Không tìm thấy lộ trình.")
        return []

    route = data["routes"][0] 
    summary = route["summary"]
    points = route["legs"][0]["points"]
    coords = [(pt["latitude"], pt["longitude"]) for pt in points]

    time_min = summary['travelTimeInSeconds'] / 60
    distance_km = summary['lengthInMeters'] / 1000

    print(f"\n✅ Chiều dài: {distance_km:.2f} km")
    print(f"🕒 Thời gian ước tính: {time_min:.2f} phút")

    return coords


# ------------------- MAIN -------------------
if __name__ == "__main__":
    api_key = "YOUR_KEY"

    loc1, loc2 = choose_location(api_key)

    if not loc1 or not loc2:
        print("\n❌ Không thể tiếp tục do thiếu dữ liệu địa điểm.")
        exit()

    travel_mode = choose_travel_mode()
    route_type = choose_route_type()

    coords = tomtom_route(
        loc1["latitude"], loc1["longitude"],
        loc2["latitude"], loc2["longitude"],
        api_key, travel_mode, route_type
    )

    visualize_path_on_map(
        coords,
        (loc1["latitude"], loc1["longitude"]),
        (loc2["latitude"], loc2["longitude"]),
    )
