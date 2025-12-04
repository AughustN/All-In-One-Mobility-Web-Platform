from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import urllib.parse
import folium
import os
import json
import mysql.connector
import bcrypt
import jwt
import datetime
from pathlib import Path
from functools import wraps
from detector_batch import run_detection_for_cameras  
from werkzeug.utils import secure_filename
import math  
from threading import Thread
from segment_aggregation import ( SegmentAggregator, CameraToSegmentMapper )
from classified_congestion import (
    PercentileThresholdCalculator,
    CongestionClassifier,
)
import modal
import base64
from pathlib import Path
import sqlite3

# Import Modal app with different name to avoid conflict
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from CongestionPredictionModel.modal_deployment import app as modal_app, detect_images_batch  # Renamed!


EARTH_RADIUS_M = 6371000.0  # mean Earth radius in meters

SOS_UPLOAD_DIR = './sos_images'
if not os.path.exists(SOS_UPLOAD_DIR):
    os.makedirs(SOS_UPLOAD_DIR)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
CAMERA_LOCATIONS_FILE = "camera_locations.json"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



app = Flask(__name__)
CORS(app)

# ============================
# 🔑 CONFIGURATION
# ============================
TOMTOM_API_KEY = "dcS4AgK0puDJlKhUT8zOfIUA5VK0pKsi"
CAMERA_FRAMES_DIR = './camera_frames'
SECRET_KEY = "your_secret_key_here"  # Change this in production!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'osm_app'
}

# ============================
# 🛠️ HELPERS
# ============================
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (data['user_id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            if not current_user:
                raise Exception("User not found")
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def latlon_to_xy_m(lat, lon, ref_lat_rad):
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    x = EARTH_RADIUS_M * lon_rad * math.cos(ref_lat_rad)
    y = EARTH_RADIUS_M * lat_rad
    return x, y


def point_to_segment_distance(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        # A and B are the same point
        return math.hypot(px - ax, py - ay)

    # project P onto AB, clamp t to [0,1]
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    closest_x = ax + t * dx
    closest_y = ay + t * dy

    return math.hypot(px - closest_x, py - closest_y)

def load_camera_locations():
    """Load all camera locations from JSON."""
    try:
        with open(CAMERA_LOCATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CAMERA_LOCATIONS_FILE not found: {CAMERA_LOCATIONS_FILE}")
        return {}
    except Exception as e:
        print(f"Error loading camera locations: {e}")
        return {}
    

def find_cameras_on_route(coords, max_distance_m=150.0):
    cameras = load_camera_locations()
    if not cameras or not coords:
        return []

    # reference latitude = mean of route lats
    avg_lat = sum(p["lat"] for p in coords) / len(coords)
    ref_lat_rad = math.radians(avg_lat)

    # precompute route points in meters
    route_xy = [
        latlon_to_xy_m(p["lat"], p["lon"], ref_lat_rad)
        for p in coords
    ]

    # build segments indices (i, i+1)
    segments = list(zip(route_xy[:-1], route_xy[1:]))

    selected = []

    for cam_id, info in cameras.items():
        clat = info.get("lat")
        clon = info.get("lon")
        if clat is None or clon is None:
            continue

        # camera position in meters
        cx, cy = latlon_to_xy_m(clat, clon, ref_lat_rad)

        # compute min distance to route segments
        min_dist = float("inf")
        for (ax, ay), (bx, by) in segments:
            d = point_to_segment_distance(cx, cy, ax, ay, bx, by)
            if d < min_dist:
                min_dist = d
            # small optimization: break early if already close enough
            if min_dist <= max_distance_m:
                break

        if min_dist <= max_distance_m:
            selected.append({
                "id": cam_id,
                "camera_name": info.get("camera_name"),
                "lat": clat,
                "lon": clon,
                "display_name": info.get("display_name")
            })

    return selected

def run_congestion_update_background():
    def job():
        try:
            print("\n[BG] Starting congestion update...")

            # Step 0: Verify static thresholds exist
            thresholds_path = Path("segment_thresholds.json")
            if not thresholds_path.exists():
                print("[BG] ❌ ERROR: segment_thresholds.json not found!")
                print("[BG] Static thresholds are required. Please run classified_congestion.py first.")
                return

            print("[BG] ✓ Using static thresholds from segment_thresholds.json")

            mapper = CameraToSegmentMapper(
            camera_locations_file='camera_locations.json',
            db_path='detections_optimized.db')
        
            segments_df = mapper.create_simple_segments()
            mapper.save_segments(segments_df, 'segments.csv')

            # 1) aggregate detections
            aggregator = SegmentAggregator(
                db_path="detections_optimized.db",
                segments_file="segments.csv",
            )
            agg_df = aggregator.aggregate_to_time_windows(window_minutes=15)
            aggregator.save_aggregated_data(agg_df, "segment_aggregated.csv")

            # # 2) thresholds
            # thresh_calc = PercentileThresholdCalculator(
            #     aggregated_csv="segment_aggregated.csv",
            #     output_file="segment_thresholds.json",
            # )
            # thresh_calc.calculate_thresholds(min_samples=20)

            # 3) classify + update geojson
            classifier = CongestionClassifier(
                thresholds_file="segment_thresholds.json",
                aggregated_csv="segment_aggregated.csv",
                geometries_file="segment_geometries.geojson",
            )
            classifier.classify_latest_data(
                output_csv="segment_congestion_classified.csv"
            )
            classifier.update_geojson_with_congestion(
                classified_csv="segment_congestion_classified.csv",
                output_geojson="segment_geometries_with_congestion.geojson",
            )
            print("[BG] Congestion update done.")
        except Exception as e:
            print(f"[BG] Error in congestion update: {e}")

    Thread(target=job, daemon=True).start() 


# ============================
# 👤 AUTH API
# ============================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                    (username, hashed_password.decode('utf-8')))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'User created successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'message': f'Error: {err}'}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': token, 'username': username})
    
    return jsonify({'message': 'Invalid credentials'}), 401

# ============================
# 💾 USER DATA API
# ============================
@app.route('/api/user/locations', methods=['GET', 'POST'])
@token_required
def user_locations(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO user_locations (user_id, name, lat, lng) VALUES (%s, %s, %s, %s)",
            (current_user['id'], data['name'], data['lat'], data['lng'])
        )
        conn.commit()
        msg = 'Location saved'
    else:
        cursor.execute(
            "SELECT * FROM user_locations WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10",
            (current_user['id'],)
        )
        msg = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return jsonify(msg)

@app.route('/api/user/routes', methods=['GET', 'POST'])
@token_required
def user_routes(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.json
        cursor.execute(
            "INSERT INTO user_routes (user_id, start_name, start_lat, start_lng, end_name, end_lat, end_lng) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (current_user['id'], data['start_name'], data['start_lat'], data['start_lng'], 
            data['end_name'], data['end_lat'], data['end_lng'])
        )
        conn.commit()
        msg = 'Route saved'
    else:
        cursor.execute(
            "SELECT * FROM user_routes WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10",
            (current_user['id'],)
        )
        msg = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return jsonify(msg)

# ============================
# 💾 SOS API
# ============================
@app.route('/api/sos/resolve', methods=['POST'])
@token_required
def resolve_sos(current_user):
    """Đánh dấu một SOS là đã giải quyết"""
    data = request.json
    sos_id = data.get('sos_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Kiểm tra xem SOS này có phải của user này đăng không
    cursor.execute("SELECT * FROM sos_alerts WHERE id = %s", (sos_id,))
    alert = cursor.fetchone()
    
    if not alert:
        return jsonify({'message': 'Không tìm thấy báo cáo'}), 404
        
    if alert['user_id'] != current_user['id']:
        return jsonify({'message': 'Bạn không có quyền xóa báo cáo này'}), 403

    # Cập nhật trạng thái
    cursor.execute("UPDATE sos_alerts SET status = 'resolved' WHERE id = %s", (sos_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Đã giải quyết sự cố thành công'}), 200


@app.route('/api/sos', methods=['POST'])
@token_required
def report_sos(current_user):
    """Người dùng gửi báo cáo SOS"""
    try:
        # 1. KIỂM TRA: User này đã có báo cáo nào chưa?
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Tìm xem user này có bài đăng nào status = 'active' không
        cursor.execute(
            "SELECT id FROM sos_alerts WHERE user_id = %s AND status = 'active'", 
            (current_user['id'],)
        )
        existing_alert = cursor.fetchone()
        
        # Nếu tìm thấy -> Báo lỗi ngay
        if existing_alert:
            cursor.close()
            conn.close()
            return jsonify({
                'message': 'Bạn đang có một báo cáo chưa xử lý. Không thể gửi thêm!'
            }), 400

        # 2. Nếu chưa có -> Tiếp tục xử lý như cũ
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        description = request.form.get('description')
        
        if not lat or not lng:
            return jsonify({'message': 'Missing location data'}), 400

        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"sos_{int(datetime.datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(SOS_UPLOAD_DIR, filename))
                image_url = f"/sos_images/{filename}"

        # Lưu mới
        # (Lưu ý: Mở cursor mới vì cursor cũ đã dùng ở trên, hoặc dùng lại cursor cũ nhưng phải cẩn thận)
        # Ở đây ta dùng lại cursor cũ nhưng chuyển về chế độ thường để insert
        cursor = conn.cursor() 
        cursor.execute(
            "INSERT INTO sos_alerts (user_id, lat, lng, description, image_url, status) VALUES (%s, %s, %s, %s, %s, 'active')",
            (current_user['id'], lat, lng, description, image_url)
        )
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ Đã lưu SOS mới: {description}")
        return jsonify({'message': 'SOS reported successfully', 'image_url': image_url}), 201

    except Exception as e:
        print(f"❌ Error reporting SOS: {e}")
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

@app.route('/api/sos', methods=['GET'])
def get_sos_alerts():
    """Chỉ lấy danh sách các SOS đang ACTIVE"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # QUAN TRỌNG: Chỉ lấy status = 'active'
        query = """
            SELECT s.*, u.username 
            FROM sos_alerts s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.status = 'active'
            ORDER BY s.timestamp DESC
        """
        cursor.execute(query)
        alerts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'message': 'Error fetching SOS', 'error': str(e)}), 500

@app.route('/sos_images/<filename>')
def serve_sos_image(filename):
    """API để hiển thị ảnh SOS"""
    return send_from_directory(SOS_UPLOAD_DIR, filename)

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
    points = route["legs"][0]["points"]
    coords = [{"lat": p["latitude"], "lon": p["longitude"]} for p in points]
    summary = route["summary"]


    cameras_on_route = find_cameras_on_route(coords)

    return jsonify({
        "coords": coords,
        "distance_km": summary["lengthInMeters"] / 1000,
        "duration_min": summary["travelTimeInSeconds"] / 60,
        "cameras_on_route": cameras_on_route,
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
    """Proxy camera image directly from HCMC traffic server (no saving)"""
    try:
        # Generate unique URL with timestamp
        timestamp_ms = int(datetime.datetime.now().timestamp() * 1000)
        
        # Return proxy URL that frontend will use
        proxy_url = f"/api/camera/{camera_id}/proxy?t={timestamp_ms}"
        
        return jsonify({
            'camera_id': camera_id,
            'count': 1,
            'images': [{
                'url': proxy_url,
                'timestamp': timestamp_ms
            }]
        })
            
    except Exception as e:
        return jsonify({'error': str(e), 'images': []}), 500

@app.route('/api/camera/<camera_id>/proxy', methods=['GET'])
def proxy_camera_image(camera_id):
    """Proxy the actual image from HCMC traffic server"""
    try:
        timestamp = request.args.get('t', int(datetime.datetime.now().timestamp() * 1000))
        image_url = f"https://giaothong.hochiminhcity.gov.vn:8007/Render/CameraHandler.ashx?id={camera_id}&bg=black&w=600&h=400&t={timestamp}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': 'https://giaothong.hochiminhcity.gov.vn/',
        }
        
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        
        if response.status_code == 200:
            # Stream image directly to client without saving
            return response.content, 200, {
                'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        else:
            return jsonify({'error': f'Failed to fetch image: HTTP {response.status_code}'}), 404
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout fetching camera image'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
# 👤  Camera on Route
# ============================
@app.route("/api/detect/route-cameras", methods=["POST"])
def detect_route_cameras():
    """
    Run batch detection for cameras on route using Modal GPUs.
    """
    data = request.json or {}
    camera_ids = data.get("camera_ids") or []

    if not camera_ids:
        return jsonify({"error": "camera_ids required"}), 400

    try:
        # Collect latest images for each camera
        images_b64 = []
        valid_camera_ids = []
        
        for cam_id in camera_ids:
            cam_dir = Path(CAMERA_FRAMES_DIR) / cam_id
            if cam_dir.exists():
                images = sorted(cam_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
                if images:
                    # Encode image to base64
                    with open(images[0], "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                        images_b64.append(img_b64)
                        valid_camera_ids.append(cam_id)
        
        if not images_b64:
            return jsonify({"error": "No images found for cameras"}), 404
        
        # ===== MODAL INTEGRATION: REPLACE LOCAL DETECTION =====
        print(f"🚀 Sending {len(images_b64)} images to Modal GPU...")
        
        with modal_app.run():
            results = detect_images_batch.remote(images_b64, valid_camera_ids)
        
        print(f"✅ Modal detection complete!")
        # =======================================================
        
        # Save results to database (same as before)
        db_path = "detections_optimized.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        total_detections = 0
        for result in results:
            if "error" not in result:
                cam_id = result["camera_id"]
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for det in result["detections"]:
                    cursor.execute("""
                        INSERT INTO detections 
                        (camera_id, timestamp, class_id, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cam_id, timestamp, det["class_id"], det["confidence"],
                        det["bbox"][0], det["bbox"][1], det["bbox"][2], det["bbox"][3]
                    ))
                    total_detections += 1
        
        conn.commit()
        conn.close()
        
        # Update congestion data (same as before)
        run_congestion_update_background()
        
        return jsonify({
            "status": "ok",
            "processed_cameras": len(valid_camera_ids),
            "total_detections": total_detections
        })
        
    except Exception as e:
        print(f"❌ Error during Modal detection: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route("/api/congestion/geojson", methods=["GET"])
def get_congestion_geojson():
    geojson_path = Path("segment_geometries_with_congestion.geojson")
    if not geojson_path.exists():
        return jsonify({
            "error": "GeoJSON not found. Run classified_congestion.py to generate it."
        }), 404

    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify(data)


# ============================
# 🚀 RUN SERVER
# ============================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Combined Flask API Server")
    print("=" * 60)
    print(f"\n📂 Camera frames directory: {os.path.abspath(CAMERA_FRAMES_DIR)}")
    print(f"📂 SOS images directory:    {os.path.abspath(SOS_UPLOAD_DIR)}") # Thêm dòng này
    print(f"🗺️  TomTom API Key:         {TOMTOM_API_KEY[:20]}...")
    print("\n🌐 Server running on http://localhost:5000")
    print("\n📋 Available endpoints:")
    
    print("\n  === Auth & User ===")
    print("  POST /api/auth/register       - Register new user")
    print("  POST /api/auth/login          - Login user")
    print("  GET/POST /api/user/locations  - Get/Save recent locations")
    print("  GET/POST /api/user/routes     - Get/Save recent routes")
    
    print("\n  === SOS APIs (Mới) ===")     # Thêm phần này
    print("  POST /api/sos                 - Report SOS (Multipart/Form-data)")
    print("  GET  /api/sos                 - Get active SOS alerts")
    print("  GET  /sos_images/<filename>   - Serve SOS image")

    print("\n  === TomTom Routing & Search ===")
    print("  POST /search                  - Search location in HCM")
    print("  POST /route                   - Calculate route between two points")
    print("  POST /render-map              - Render route map to HTML")
    
    print("\n  === Camera APIs ===")
    print("  GET  /api/cameras             - List all cameras")
    print("  GET  /api/camera/<id>/images  - Get images for a camera")
    print("  GET  /camera_frames/<id>/...  - Serve camera image")
    print("  GET  /api/stats                - Get statistics")

    print("\n  === Route Camera Detection ===")
    print("  POST /api/detect/route-cameras - Run detection for cameras on route")
    print("  GET  /api/congestion/geojson   - Get congestion GeoJSON data")

    print("\n" + "=" * 60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)