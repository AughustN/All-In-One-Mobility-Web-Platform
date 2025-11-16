from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import urllib.parse
import folium
import os
import json

app = Flask(__name__)
CORS(app)

# ============================
# 🔑 API KEYS & DIRECTORIES
# ============================
TOMTOM_API_KEY = "YOUR_KEY"
CAMERA_FRAMES_DIR = './camera_frames'

# ============================
# 🌍 HCM City Boundaries
# ============================
HCM_CENTER = {"lat": 10.8231, "lon": 106.6297}
HCM_BBOX = {
    "minLat": 10.35,   # Biên giới phía Nam
    "maxLat": 11.15,   # Biên giới phía Bắc
    "minLon": 106.35,  # Biên giới phía Tây
    "maxLon": 107.05   # Biên giới phía Đông
}

def is_in_hcm(lat, lon):
    """Kiểm tra tọa độ có nằm trong HCM không"""
    return (HCM_BBOX["minLat"] <= lat <= HCM_BBOX["maxLat"] and 
            HCM_BBOX["minLon"] <= lon <= HCM_BBOX["maxLon"])

# ============================
# 🔍 SEARCH API (TomTom)
# ============================
@app.route("/search", methods=["POST"])
def search_location():
    data = request.json
    address = data.get("address")
    lat = data.get("lat")
    lon = data.get("lon")
    
    if not address:
        return jsonify({"error": "address is required"}), 400
    
    # Nếu có tọa độ → dùng Nearby Search
    if lat and lon:
        url = "https://api.tomtom.com/search/2/nearbySearch/.json"
        params = {
            "key": TOMTOM_API_KEY,
            "lat": lat,
            "lon": lon,
            "radius": 5000,
            "limit": 20
        }
    else:
        encoded = urllib.parse.quote(address)
        url = f"https://api.tomtom.com/search/2/search/{encoded}.json"
        params = {
            "key": TOMTOM_API_KEY,
            "countrySet": "VN",
            "limit": 20,
            "language": "vi-VN",
            "lat": HCM_CENTER["lat"],
            "lon": HCM_CENTER["lon"],
            "radius": 30000
        }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except:
        return jsonify({"error": "TomTom API connection failed"}), 500
    
    results = res.json().get("results", [])
    
    # Lọc chỉ lấy kết quả trong HCM
    filtered_results = []
    for result in results:
        pos = result.get("position", {})
        lat = pos.get("lat")
        lon = pos.get("lon")
        
        if lat and lon and is_in_hcm(lat, lon):
            filtered_results.append(result)
        
        if len(filtered_results) >= 10:
            break
    
    return jsonify(filtered_results)

# ============================
# 🗺 ROUTING API (TomTom)
# ============================
@app.route("/route", methods=["POST"])
def route_api():
    data = request.json
    start = data.get("start")
    end = data.get("end")
    travel_mode = data.get("travelMode", "car")
    route_type = data.get("routeType", "fastest")
    
    if not start or not end:
        return jsonify({"error": "start and end locations required"}), 400
    
    # Kiểm tra xem cả 2 điểm có trong HCM không
    if not is_in_hcm(start["lat"], start["lon"]):
        return jsonify({"error": "Điểm xuất phát nằm ngoài TP.HCM"}), 400
    
    if not is_in_hcm(end["lat"], end["lon"]):
        return jsonify({"error": "Điểm đến nằm ngoài TP.HCM"}), 400
    
    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/"
        f"{start['lat']},{start['lon']}:{end['lat']},{end['lon']}/json"
    )
    
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "routeType": route_type,
        "travelMode": travel_mode,
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except:
        return jsonify({"error": "Failed to call TomTom Routing API"}), 500
    
    data = res.json()
    
    if "routes" not in data or len(data["routes"]) == 0:
        return jsonify({"error": "Không tìm thấy đường đi"}), 404
    
    route = data["routes"][0]
    
    # Lấy polyline (tọa độ đường đi)
    points = route["legs"][0]["points"]
    coords = [{"lat": p["latitude"], "lon": p["longitude"]} for p in points]
    
    summary = route["summary"]
    
    return jsonify({
        "coords": coords,
        "distance_km": summary["lengthInMeters"] / 1000,
        "duration_min": summary["travelTimeInSeconds"] / 60
    })

# ============================
# 🗺 RENDER MAP (TomTom)
# ============================
@app.route("/render-map", methods=["POST"])
def render_map():
    data = request.json
    coords = data.get("coords")
    start = data.get("start")
    end = data.get("end")
    
    if not coords or not start or not end:
        return jsonify({"error": "coords/start/end required"}), 400
    
    m = folium.Map(tiles="OpenStreetMap")
    m.fit_bounds([[start["lat"], start["lon"]], [end["lat"], end["lon"]]])
    
    # Polyline
    folium.PolyLine(
        [(p["lat"], p["lon"]) for p in coords],
        color="blue",
        weight=5,
        opacity=0.9
    ).add_to(m)
    
    folium.Marker([start["lat"], start["lon"]],
                  popup="Start",
                  icon=folium.Icon(color="green")).add_to(m)
    
    folium.Marker([end["lat"], end["lon"]],
                  popup="End",
                  icon=folium.Icon(color="red")).add_to(m)
    
    file_name = "route_map.html"
    m.save(file_name)
    
    return send_file(file_name, as_attachment=False)

# ============================
# 📷 CAMERA APIs
# ============================
@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get list of all cameras with their locations"""
    try:
        with open('camera_locations.json', 'r', encoding='utf-8') as f:
            cameras = json.load(f)
        return jsonify(cameras)
    except FileNotFoundError:
        return jsonify({"error": "camera_locations.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camera/<camera_id>/images', methods=['GET'])
def get_camera_images(camera_id):
    """Get list of images for a specific camera"""
    camera_dir = os.path.join(CAMERA_FRAMES_DIR, camera_id)
    
    if not os.path.exists(camera_dir):
        return jsonify({'error': 'Camera not found', 'images': []}), 404
    
    try:
        # Get all image files
        images = []
        for filename in os.listdir(camera_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                images.append({
                    'filename': filename,
                    'url': f'/camera_frames/{camera_id}/{filename}'
                })
        
        return jsonify({
            'camera_id': camera_id,
            'count': len(images),
            'images': images
        })
    except Exception as e:
        return jsonify({'error': str(e), 'images': []}), 500

@app.route('/camera_frames/<camera_id>/<filename>')
def serve_camera_image(camera_id, filename):
    """Serve camera image file"""
    camera_dir = os.path.join(CAMERA_FRAMES_DIR, camera_id)
    return send_from_directory(camera_dir, filename)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about cameras and images"""
    try:
        with open('camera_locations.json', 'r', encoding='utf-8') as f:
            cameras = json.load(f)
        
        total_cameras = len(cameras)
        cameras_with_images = 0
        total_images = 0
        
        for camera_id in cameras.keys():
            camera_dir = os.path.join(CAMERA_FRAMES_DIR, camera_id)
            if os.path.exists(camera_dir):
                images = [f for f in os.listdir(camera_dir) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                if images:
                    cameras_with_images += 1
                    total_images += len(images)
        
        return jsonify({
            'total_cameras': total_cameras,
            'cameras_with_images': cameras_with_images,
            'total_images': total_images
        })
    except FileNotFoundError:
        return jsonify({"error": "camera_locations.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================
# 🚀 RUN SERVER
# ============================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Combined Flask API Server")
    print("=" * 60)
    print(f"\n📂 Camera frames directory: {os.path.abspath(CAMERA_FRAMES_DIR)}")
    print(f"🗺️  TomTom API Key: {TOMTOM_API_KEY[:20]}...")
    print("\n🌐 Server running on http://localhost:5000")
    print("\n📋 Available endpoints:")
    print("\n  === TomTom Routing & Search ===")
    print("  POST /search - Search location in HCM")
    print("  POST /route - Calculate route between two points")
    print("  POST /render-map - Render route map to HTML")
    print("\n  === Camera APIs ===")
    print("  GET  /api/cameras - List all cameras")
    print("  GET  /api/camera/<id>/images - Get images for a camera")
    print("  GET  /camera_frames/<id>/<filename> - Serve camera image")
    print("  GET  /api/stats - Get statistics")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)