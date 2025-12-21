import overpy
import pandas as pd
import json
import requests
import math
import heapq
import folium
from geopy.geocoders import Nominatim


# ---------------- Haversine ----------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ---------------- Build Graph ----------------
def build_graph_from_json(json_data):
    nodes = {}
    graph = {}

    for el in json_data['elements']:
        if el['type'] == 'node':
            nodes[el['id']] = (el['lat'], el['lon'])

    for el in json_data['elements']:
        if el['type'] == 'way' and 'nodes' in el:
            way_nodes = el['nodes']
            
            tags = el.get('tags', {})
            oneway = tags.get('oneway', 'no')
            
            for i in range(len(way_nodes) - 1):
                n1, n2 = way_nodes[i], way_nodes[i + 1]
                if n1 in nodes and n2 in nodes:
                    dist = haversine(*nodes[n1], *nodes[n2])
                    graph.setdefault(n1, []).append((n2, dist))
                    if oneway not in ['yes']:
                        graph.setdefault(n2, []).append((n1, dist))  # hai chiều
    return nodes, graph

# ---------------- Find nearest node ----------------
def find_nearest_node(lat, lon, nodes):
    nearest = None
    min_dist = float("inf")
    for nid, (nlat, nlon) in nodes.items():
        d = haversine(lat, lon, nlat, nlon)
        if d < min_dist:
            min_dist, nearest = d, nid
    return nearest

# ---------------- A* (A-star) ----------------
def astar(graph, nodes, start, end):
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: haversine(*nodes[start], *nodes[end])}
    visited = set()

    while open_set:
        # Lấy node có f_score nhỏ nhất
        _, current = heapq.heappop(open_set)
        if current in visited:
            continue
        visited.add(current)

        # Nếu đến đích -> truy vết đường đi
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return g_score[end], path

        # Duyệt các node kề
        for neighbor, weight in graph.get(current, []):
            tentative_g = g_score[current] + weight
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + haversine(*nodes[neighbor], *nodes[end])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return float("inf"), []


# # ---------------- Dijkstra ----------------
# def dijkstra(graph, start, end):
#     queue = [(0, start, [])]
#     visited = set()
#     while queue:
#         cost, node, path = heapq.heappop(queue)
#         if node in visited:
#             continue
#         visited.add(node)
#         path = path + [node]
#         if node == end:
#             return cost, path
#         for neighbor, weight in graph.get(node, []):
#             if neighbor not in visited:
#                 heapq.heappush(queue, (cost + weight, neighbor, path))
#     return float("inf"), []

# ---------------- Shortest path ----------------
def find_shortest_path(start_lat, start_lon, end_lat, end_lon, fill_data_name):
    with open(fill_data_name, "r") as f:
        data = json.load(f)

    nodes, graph = build_graph_from_json(data)

    print(f"\n🔹 Tổng số node trong graph: {len(nodes)}")
    print(f"🔹 Tổng số cạnh: {sum(len(v) for v in graph.values())}")

    start_node = find_nearest_node(start_lat, start_lon, nodes)
    end_node = find_nearest_node(end_lat, end_lon, nodes)

    if start_node is None:
        print("❌ Không tìm thấy node gần điểm bắt đầu.")
        return []
    if end_node is None:
        print("❌ Không tìm thấy node gần điểm kết thúc.")
        return []

    distance, path = astar(graph, nodes, start_node, end_node)

    if not path:
        print("❌ Không tìm thấy đường nối giữa hai điểm.")
        return []

    coords = [(nodes[nid][0], nodes[nid][1]) for nid in path]
    print(f"\n✅ Độ dài đường đi ước tính: {distance/1000:.2f} km")
    print(f"✅ Số node đi qua: {len(path)}")
    return coords


# ---------------- Get user input ----------------
def get_input():

    lat1 = float(input("\nNhập vĩ độ điểm bắt đầu: "))
    lon1 = float(input("Nhập kinh độ điểm bắt đầu: "))
    lat2 = float(input("Nhập vĩ độ điểm đích: "))
    lon2 = float(input("Nhập kinh độ điểm đích: "))

    # Tính trung tâm và bán kính để query Overpass
    center_lat = (lat1 + lat2) / 2
    center_lon = (lon1 + lon2) / 2
    radius = haversine(lat1, lon1, lat2, lon2) / 2 + 10000  

    return lat1, lon1, lat2, lon2, center_lat, center_lon, radius

def visualize_path_on_map(coords, start, end):
    if not coords:
        print("⚠️ Không có dữ liệu đường đi để vẽ.")
        return

    # Tạo bản đồ trung tâm tại điểm đầu
    m = folium.Map(location=start, zoom_start=13, tiles="OpenStreetMap")

    # Vẽ đường đi
    folium.PolyLine(coords, color="blue", weight=4, opacity=0.8).add_to(m)

    # Đánh dấu điểm đầu & điểm đích
    folium.Marker(start, popup="Điểm bắt đầu", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end, popup="Điểm đích", icon=folium.Icon(color="red")).add_to(m)

    # Lưu ra file HTML
    m.save("shortest_path_map.html")
    print("✅ Đã lưu bản đồ: shortest_path_map.html")
from geopy.geocoders import Nominatim

# --- Hàm hỗ trợ chọn địa chỉ ---
def choose_location(address):
    geolocator = Nominatim(user_agent="osm-route")
    results = geolocator.geocode(address, exactly_one=False, addressdetails=True, timeout=10)
    
    if not results:
        print(f"❌ Không tìm thấy địa chỉ nào cho: {address}")
        return None
    print(f"\n🔍 Kết quả tìm thấy cho '{address}':")
    for i, loc in enumerate(results):
        print(f"{i+1}. {loc.address} ({loc.latitude}, {loc.longitude})")

    while True:
        try:
            choice = int(input(f"👉 Chọn số thứ tự (1-{len(results)}): "))
            if 1 <= choice <= len(results):
                return results[choice - 1]
            else:
                print("⚠️ Lựa chọn không hợp lệ. Thử lại.")
        except ValueError:
            print("⚠️ Nhập số thứ tự hợp lệ.")

def choose_transports():
    print("\nHãy chọn loại phương tiện di chuyển.")
    print("1. Xe ô tô")
    print("2. Xe gắn máy")
    print("3. Xe đạp")
    print("4. Đi bộ")
    choice = int(input(f"👉 Chọn số thứ tự (1-4): "))
    if choice == 1:
        return "car_data.json"
    elif choice == 2:
        return "motorbike_data.json"
    elif choice == 3:
        return "bicycle_data.json"
    elif choice == 4:
        return "walk_data.json"
    else: return None

# ---------------- Main ----------------
if __name__ == "__main__":
    start_text = input("📍 Nhập địa điểm bắt đầu: ")
    end_text = input("🏁 Nhập địa điểm kết thúc: ")
    # lat1, lon1, lat2, lon2, center_lat, center_lon, radius = get_input()

    loc1 = choose_location(start_text)
    loc2 = choose_location(end_text)
    file_data_name = choose_transports()
    coords = find_shortest_path(loc1.latitude, loc1.longitude, loc2.latitude, loc2.longitude, file_data_name)
    visualize_path_on_map(coords, (loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude))