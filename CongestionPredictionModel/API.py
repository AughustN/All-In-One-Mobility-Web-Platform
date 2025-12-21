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
import math
from pathlib import Path
import datetime
from functools import wraps
from werkzeug.utils import secure_filename
import uuid
import numpy as np
from typing import Any
from congestion.detector_batch import run_detection_for_cameras  
from werkzeug.utils import secure_filename
from threading import Thread
from congestion.segment_aggregation import ( SegmentAggregator, CameraToSegmentMapper )
from congestion.classified_congestion import (
    CongestionClassifier, PercentileThresholdCalculator, GoongRoadGeometryFetcher
)
from trip_data.PlanTrip_API import generate_trip_plan
import base64
import sqlite3
from dotenv import load_dotenv
import os


load_dotenv() # reads .env file
MODAL_API_URL = os.getenv("MODAL_API_URL")
GOONG_API_KEY = os.getenv("GOONG_API_KEY", "")
USE_MODAL_DETECTION = True  # Set to False to use local detection
GEOM_GEOJSON = Path("segment_geometries.geojson")
GEOJSON_WITH_CONG = Path("segment_geometries_with_congestion.geojson")
EARTH_RADIUS_M = 6371000.0
CAMERA_LOCATIONS_FILE = "camera_locations.json"
# Import bus routing modules
BUS_ROUTING_AVAILABLE = False
MATCH_TRIP_AVAILABLE = False

try:
    import trip_data.match_cache
    trip_data.match_cache.load_database()
    MATCH_TRIP_AVAILABLE = True
    print("✅ Trip matching module loaded successfully")
except ImportError as e:
    print(f"⚠️ Match modules not available: {e}")
except Exception as e:
    print(f"❌ Failed to load Match data: {e}")

try:
    import bus_data.graph_cache
    from bus_data.Bus_Routing_Module import a_star, nearby_stops, make_heuristic, calculate_First_Last_walkingCoords, calculate_transfer_walkingCoords
    print("✅ Bus routing modules loaded successfully")
    
    # Load data immediately after import
    print("\n🚌 Loading bus routing data...")
    print("💡 Tip: First load builds graph (~10-30s), subsequent loads use cache (<1s)")
    import time
    start_time = time.time()
    bus_data.graph_cache.load_all_data()
    load_time = time.time() - start_time
    BUS_ROUTING_AVAILABLE = True
    print(f"✅ Bus routing ready in {load_time:.2f}s!\n")
except ImportError as e:
    print(f"⚠️ Bus routing modules not available: {e}")
except Exception as e:
    print(f"❌ Failed to load bus routing data: {e}")


SOS_UPLOAD_DIR = './sos_images'
if not os.path.exists(SOS_UPLOAD_DIR):
    os.makedirs(SOS_UPLOAD_DIR)

IMAGE_TRIP_FOLDER = './images'
if not os.path.exists(IMAGE_TRIP_FOLDER):
    os.makedirs(IMAGE_TRIP_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS







app = Flask(__name__)
CORS(app)

# Helper function to convert numpy types to Python types
def to_python(obj: Any) -> Any:
    """Recursively convert numpy types → native python types"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_python(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        return to_python(obj.__dict__)
    else:
        return obj
    

def safe_segment_name(raw_name, seg_id, route_name=None):
    # Handle pandas NaN (float), None, empty string
    if raw_name is None:
        raw_name = ""
    if isinstance(raw_name, float) and math.isnan(raw_name):
        raw_name = ""
    if isinstance(raw_name, str):
        raw_name = raw_name.strip()

    if raw_name:
        return raw_name
    if isinstance(route_name, str) and route_name.strip() and route_name.strip().lower() != "unknown":
        return route_name.strip()
    return f"Segment {seg_id}"



# ============================
# 🔑 CONFIGURATION
# ============================
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
CAMERA_FRAMES_DIR = './camera_frames'
SECRET_KEY = os.getenv("SECRET_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# ============================
# 🛠️ HELPERS
# ============================
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
# load camera method
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

def ensure_geometries(force: bool = False, rate_limit_delay: float = 0.5) -> None:
    """
    Ensure segment_geometries.geojson exists (or rebuild it if forced).
    """
    if (not force) and GEOM_GEOJSON.exists():
        print(f"[BG] Base geometries exist: {GEOM_GEOJSON}")
        return

    if not GOONG_API_KEY:
        raise RuntimeError("GOONG_API_KEY is not set. Cannot fetch geometries.")

    print(f"[BG] Building base geometries -> {GEOM_GEOJSON} (force={force})")

    fetcher = GoongRoadGeometryFetcher(
        segments_csv=str("segments.csv"),
        output_geojson=str(GEOM_GEOJSON),
        goong_api_key=GOONG_API_KEY
    )
    fetcher.fetch_all_geometries(rate_limit_delay=rate_limit_delay)

    print(f"[BG] Done building base geometries: {GEOM_GEOJSON}")


def run_congestion_update_background(force_rebuild_geometries: bool = True):
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

            # 2) thresholds
            thresh_calc = PercentileThresholdCalculator(
                aggregated_csv="segment_aggregated.csv",
                output_file="segment_thresholds.json",
            )
            thresh_calc.calculate_thresholds(min_samples=6)

            ensure_geometries(force=force_rebuild_geometries, rate_limit_delay=0.5)

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


GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@app.route('/api/auth/github', methods=['POST'])
def github_auth():
    """Handle GitHub OAuth login"""
    data = request.json
    code = data.get('code')  # Authorization code from GitHub
    
    if not code:
        return jsonify({'message': 'Authorization code required'}), 400
    
    try:
        # Exchange code for access token
        GITHUB_CLIENT_ID = 'Ov23ctE7T96xTrp7hSqY'  # Cần cập nhật
        
        import requests as req
        token_response = req.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            return jsonify({'message': 'Failed to get GitHub access token'}), 401
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return jsonify({'message': 'Invalid GitHub authorization'}), 401
        
        # Get user info from GitHub
        user_response = req.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        if user_response.status_code != 200:
            return jsonify({'message': 'Failed to get GitHub user info'}), 401
        
        user_info = user_response.json()
        github_id = str(user_info.get('id'))
        username = user_info.get('login')
        name = user_info.get('name', username)
        email = user_info.get('email')
        
        # Get email if not public
        if not email:
            email_response = req.get(
                'https://api.github.com/user/emails',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                },
                timeout=10
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((e for e in emails if e.get('primary')), None)
                if primary_email:
                    email = primary_email.get('email')
        
        if not email:
            email = f'github_{github_id}@github.com'
        
        # Check if user exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s OR oauth_provider_id = %s", 
                      (email, github_id))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute(
                "INSERT INTO users (username, email, oauth_provider, oauth_provider_id) VALUES (%s, %s, %s, %s)",
                (name, email, 'github', github_id)
            )
            conn.commit()
            user_id = cursor.lastrowid
            db_username = name
        else:
            user_id = user['id']
            db_username = user['username']
        
        cursor.close()
        conn.close()
        
        # Generate JWT token
        jwt_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': jwt_token, 'username': db_username})
        
    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return jsonify({'message': 'GitHub authentication failed', 'error': str(e)}), 500
@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Handle Google OAuth login"""
    data = request.json
    token = data.get('token')  # Google ID token from frontend
    
    if not token:
        return jsonify({'message': 'Token required'}), 400
    
    try:
        # Verify Google token
        import requests as req
        response = req.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}',
            timeout=5
        )
        
        if response.status_code != 200:
            return jsonify({'message': 'Invalid Google token'}), 401
        
        user_info = response.json()
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        google_id = user_info.get('sub')
        
        # Check if user exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s OR oauth_provider_id = %s", 
                      (email, google_id))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute(
                "INSERT INTO users (username, email, oauth_provider, oauth_provider_id) VALUES (%s, %s, %s, %s)",
                (name, email, 'google', google_id)
            )
            conn.commit()
            user_id = cursor.lastrowid
            username = name
        else:
            user_id = user['id']
            username = user['username']
        
        cursor.close()
        conn.close()
        
        # Generate JWT token
        jwt_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': jwt_token, 'username': username})
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return jsonify({'message': 'Google authentication failed', 'error': str(e)}), 500

@app.route('/api/auth/facebook', methods=['POST'])
def facebook_auth():
    """Handle Facebook OAuth login"""
    data = request.json
    access_token = data.get('accessToken')
    
    if not access_token:
        return jsonify({'message': 'Access token required'}), 400
    
    try:
        # Verify Facebook token and get user info
        import requests as req
        response = req.get(
            f'https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}',
            timeout=5
        )
        
        if response.status_code != 200:
            return jsonify({'message': 'Invalid Facebook token'}), 401
        
        user_info = response.json()
        facebook_id = user_info.get('id')
        name = user_info.get('name')
        email = user_info.get('email', f'fb_{facebook_id}@facebook.com')
        
        # Check if user exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s OR oauth_provider_id = %s", 
                      (email, facebook_id))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            cursor.execute(
                "INSERT INTO users (username, email, oauth_provider, oauth_provider_id) VALUES (%s, %s, %s, %s)",
                (name, email, 'facebook', facebook_id)
            )
            conn.commit()
            user_id = cursor.lastrowid
            username = name
        else:
            user_id = user['id']
            username = user['username']
        
        cursor.close()
        conn.close()
        
        # Generate JWT token
        jwt_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': jwt_token, 'username': username})
        
    except Exception as e:
        print(f"Facebook OAuth error: {e}")
        return jsonify({'message': 'Facebook authentication failed', 'error': str(e)}), 500

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

@app.route('/api/user/trips', methods=['GET', 'POST'])
@token_required
def user_trips(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        trip_data = request.get_json()

        if not trip_data:
            return jsonify({"error": "Empty JSON"}), 400

        try:
            sql = "INSERT INTO trips (user_id, trip_json) VALUES (%s, %s)"
            cursor.execute(sql, (current_user["id"], json.dumps(trip_data)))
            conn.commit()

            return jsonify({"message": "Trip saved successfully"}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            cursor.close()
            conn.close()
    else:
        try:
            sql = """
                SELECT id, trip_json, created_at
                FROM trips
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            """

            cursor.execute(sql, (current_user["id"],))
            rows = cursor.fetchall()

            for r in rows:
                r["trip_json"] = json.loads(r["trip_json"])

            return jsonify(rows), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            cursor.close()
            conn.close()

@app.route('/api/user/trips/<int:trip_id>', methods=['DELETE'])
@token_required
def delete_trip(current_user, trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = "DELETE FROM trips WHERE id = %s AND user_id = %s"
        cursor.execute(sql, (trip_id, current_user["id"]))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Trip not found"}), 404

        return jsonify({"message": "Trip deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

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
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Chặn spam
        cursor.execute("SELECT id FROM sos_alerts WHERE user_id = %s AND status = 'active'", (current_user['id'],))
        if cursor.fetchone():
            return jsonify({'message': 'Bạn đang có một báo cáo chưa xử lý. Không thể gửi thêm!'}), 400

        # 2. Lấy dữ liệu
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        description = request.form.get('description')
        
        if not lat or not lng:
            return jsonify({'message': 'Missing location data'}), 400

        # 3. Xử lý ảnh
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"sos_{int(datetime.datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(SOS_UPLOAD_DIR, filename))
                image_url = f"/sos_images/{filename}"

        # 4. Lưu vào DB
        cursor.execute(
            "INSERT INTO sos_alerts (user_id, lat, lng, description, image_url, status) VALUES (%s, %s, %s, %s, %s, 'active')",
            (current_user['id'], lat, lng, description, image_url)
        )
        conn.commit()
        return jsonify({'message': 'SOS reported successfully', 'image_url': image_url}), 201

    except Exception as e:
        print(f"❌ Error reporting SOS: {e}")
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500
        
    finally:
        # --- QUAN TRỌNG: Luôn đóng kết nối dù thành công hay thất bại ---
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

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

@app.route('/api/sos/comments/<int:sos_id>', methods=['GET'])
def get_sos_comments(sos_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Lấy comment kèm tên người bình luận
        query = """
            SELECT c.*, u.username 
            FROM sos_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.sos_id = %s
            ORDER BY c.created_at ASC
        """
        cursor.execute(query, (sos_id,))
        comments = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(comments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/comment', methods=['POST'])
@token_required
def add_comment(current_user):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sos_comments (sos_id, user_id, content) VALUES (%s, %s, %s)",
            (data['sos_id'], current_user['id'], data['content'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Bình luận thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sos/report', methods=['POST'])
@token_required
def report_sos_post(current_user):
    data = request.json
    sos_id = data.get('sos_id')
    reason = data.get('reason', 'Fake news')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Kiểm tra xem user này đã báo cáo bài này chưa
        cursor.execute("SELECT id FROM sos_reports WHERE sos_id = %s AND user_id = %s", (sos_id, current_user['id']))
        if cursor.fetchone():
            return jsonify({'message': 'Bạn đã báo cáo bài này rồi!'}), 400

        # 2. Thêm báo cáo mới
        cursor.execute("INSERT INTO sos_reports (sos_id, user_id, reason) VALUES (%s, %s, %s)", 
                       (sos_id, current_user['id'], reason))
        
        # 3. Đếm tổng số báo cáo của bài này
        cursor.execute("SELECT COUNT(*) as count FROM sos_reports WHERE sos_id = %s", (sos_id,))
        result = cursor.fetchone()
        report_count = result['count']

        msg = 'Đã gửi báo cáo.'

        # 4. QUY TẮC: Nếu quá 3 người báo cáo -> Ẩn bài luôn (chuyển status thành 'hidden')
        LIMIT_REPORT = 3
        if report_count >= LIMIT_REPORT:
            cursor.execute("UPDATE sos_alerts SET status = 'hidden' WHERE id = %s", (sos_id,))
            msg = f'Bài viết đã bị gỡ do có {report_count} người báo cáo.'

        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': msg, 'hidden': report_count >= LIMIT_REPORT}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


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
def calculate_route(start, end, travel_mode="car", route_type="fastest"):
    if not start or not end:
        return {"error": "start and end locations required"}, 400

    if not is_in_hcm(start["lat"], start["lon"]):
        return {"error": "Điểm xuất phát nằm ngoài TP.HCM"}, 400
    if not is_in_hcm(end["lat"], end["lon"]):
        return {"error": "Điểm đến nằm ngoài TP.HCM"}, 400

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
        return {"error": "Failed to call TomTom Routing API"}, 500

    data = res.json()

    if "routes" not in data or len(data["routes"]) == 0:
        return {"error": "Không tìm thấy đường đi"}, 404

    route = data["routes"][0]
    points = route["legs"][0]["points"]
    coords = [{"lat": p["latitude"], "lon": p["longitude"]} for p in points]
    summary = route["summary"]

    return {
        "coords": coords,
        "distance_km": summary["lengthInMeters"] / 1000,
        "duration_min": summary["travelTimeInSeconds"] / 60
    }


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
    camera_dir = os.path.join(CAMERA_FRAMES_DIR, camera_id)
    
    if not os.path.exists(camera_dir):
        return jsonify({'error': 'Camera not found', 'images': []}), 404
    
    try:
        images = []

        # Lấy danh sách file và sort theo thời gian (mới nhất trước)
        files = [
            f for f in os.listdir(camera_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
        ]

        # Sort theo thời gian sửa đổi (mtime)
        files.sort(
            key=lambda f: os.path.getmtime(os.path.join(camera_dir, f)),
            reverse=True  # mới nhất lên đầu
        )

        # Build data
        for filename in files:
            images.append({
                'filename': filename,
                'url': f'/camera_frames/{camera_id}/{filename}',
                'mtime': os.path.getmtime(os.path.join(camera_dir, filename))
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
# 👤  Camera on Route
# ============================
@app.route("/api/detect/route-cameras", methods=["POST"])
def detect_route_cameras():
    """
    Run batch detection for cameras on route.
    Uses Modal GPU if enabled, otherwise local detection.
    """
    data = request.json or {}
    camera_ids = data.get("camera_ids") or []

    if isinstance(data, list):
        camera_ids = data
    else:
        data = data or {}
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
        
        # Run detection
        if USE_MODAL_DETECTION:
            # ===== MODAL GPU DETECTION =====
            print(f"🚀 Sending {len(images_b64)} images to Modal GPU...")
            
            response = requests.post(MODAL_API_URL, json={
                "images_b64": images_b64,
                "camera_ids": valid_camera_ids
            }, timeout=300)  # 5 minute timeout
            
            if response.status_code != 200:
                raise Exception(f"Modal API error: {response.text}")
            
            results = response.json()
            print(f"✅ Modal detection complete!")
            
            # Save results to database
            db_path = "detections_optimized.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Ensure schema exists (same as detector_batch._init_database)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL UNIQUE,
                    camera_id TEXT NOT NULL,
                    camera_name TEXT,
                    timestamp TEXT NOT NULL,
                    timestamp_dt DATETIME,
                    total_vehicles INTEGER DEFAULT 0,
                    car_count INTEGER DEFAULT 0,
                    motorcycle_count INTEGER DEFAULT 0,
                    bus_count INTEGER DEFAULT 0,
                    truck_count INTEGER DEFAULT 0,
                    processing_time REAL,
                    optimization_used TEXT,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_camera_timestamp ON detections(camera_id, timestamp_dt)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_camera_id ON detections(camera_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp_dt ON detections(timestamp_dt)')

            total_detections = 0
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            now_dt = datetime.datetime.now()

            # Class id mapping (Ultralytics YOLO11: 2 car, 3 motorcycle, 5 bus, 7 truck)
            for result in results:
                cam_id = result.get("camera_id")
                dets = result.get("detections", [])
                counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

                for det in dets:
                    cls = det.get("class_id")
                    if cls == 2:
                        counts["car"] += 1
                    elif cls == 3:
                        counts["motorcycle"] += 1
                    elif cls == 5:
                        counts["bus"] += 1
                    elif cls == 7:
                        counts["truck"] += 1

                total = counts["car"] + counts["motorcycle"] + counts["bus"] + counts["truck"]
                total_detections += total

                # Build a synthetic image_path keyed by camera+time (unique constraint required)
                image_path = f"modal://{cam_id}/{now_str}"

                cursor.execute('''
                    INSERT OR REPLACE INTO detections 
                    (image_path, camera_id, camera_name, timestamp, timestamp_dt,
                     total_vehicles, car_count, motorcycle_count, bus_count, truck_count,
                     processing_time, optimization_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_path,
                    cam_id,
                    None,
                    now_str,
                    now_dt.isoformat(),
                    total,
                    counts["car"],
                    counts["motorcycle"],
                    counts["bus"],
                    counts["truck"],
                    None,
                    "modal"
                ))

            conn.commit()
            conn.close()
        else:
            # ===== LOCAL DETECTION =====
            print(f"💻 Using local detection for {len(valid_camera_ids)} cameras...")
            run_detection_for_cameras(valid_camera_ids)
            total_detections = 0
        
        # Update congestion data
        run_congestion_update_background(force_rebuild_geometries=True)
        
        return jsonify({
            "status": "ok",
            "processed_cameras": len(valid_camera_ids),
            "total_detections": total_detections,
            "method": "modal-gpu" if USE_MODAL_DETECTION else "local"
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Error during detection: {e}")
        print(traceback.format_exc())
        
        # Fallback to local detection if Modal fails
        if USE_MODAL_DETECTION:
            print("⚠️ Falling back to local detection...")
            try:
                run_detection_for_cameras(camera_ids)
                run_congestion_update_background()
                return jsonify({
                    "status": "ok",
                    "processed_cameras": len(camera_ids),
                    "method": "local-fallback",
                    "note": "Modal failed, used local detection"
                })
            except Exception as fallback_error:
                return jsonify({"error": str(fallback_error)}), 500
        
        return jsonify({"error": str(e)}), 500
    

# Camera on Route helper
@app.route("/route", methods=["POST"])
def route_api():
    data = request.get_json(silent=True) or {}
    start = data.get("start")
    end = data.get("end")
    travel_mode = data.get("travelMode", "car")
    route_type = data.get("routeType", "fastest")

    result = calculate_route(start, end, travel_mode=travel_mode, route_type=route_type)

    # calculate_route() sometimes returns (dict, code) in your style
    if isinstance(result, tuple):
        body, code = result
        return jsonify(body), code

    coords = result.get("coords") or []
    result["cameras_on_route"] = find_cameras_on_route(coords, max_distance_m=150.0)
    return jsonify(result)


@app.route("/api/congestion/geojson", methods=["GET"])
def get_congestion_geojson():
    geojson_path = GEOJSON_WITH_CONG
    if not geojson_path.exists():
        return jsonify({
            "error": "GeoJSON not found. Run classified_congestion.py to generate it."
        }), 404

    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    for i, feat in enumerate(features):
        props = feat.get("properties") or {}

        # Try common keys you might have in properties
        raw_name = props.get("segment_name", props.get("name"))
        seg_id = props.get("segment_id", props.get("segmentId", i))
        route_name = props.get("route_name", props.get("routeName"))

        props["segment_name"] = safe_segment_name(raw_name, seg_id, route_name)
        feat["properties"] = props

    data["features"] = features
    return jsonify(data)

# ============================
# �  BUS ROUTING API
# ============================
# Constants for bus routing
SPEED_MPS = 7.0
WALK_SPEED = 1.5
C_FARE = 5.0
P_TRANSFER_PEN = 10.0 

@app.route('/api/bus/route', methods=['GET'])
def get_bus_route():
    """Calculate bus route between two points"""
    import time
    start_time = time.time()
    
    if not BUS_ROUTING_AVAILABLE:
        return jsonify({"error": "Bus routing module not available"}), 503
    
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lng = float(request.args.get('start_lng'))
        end_lat = float(request.args.get('end_lat'))
        end_lng = float(request.args.get('end_lng'))
        max_walk = float(request.args.get('max_walk', 400))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameters"}), 400
    
    start_coord = (start_lat, start_lng)
    end_coord = (end_lat, end_lng)

    print(f"\n{'='*60}")
    print(f"🚌 Bus routing request received")
    print(f"📍 From: {start_coord}")
    print(f"📍 To: {end_coord}")
    print(f"🚶 Max walk: {max_walk}m")
    print(f"{'='*60}")
    
    # Find nearby stops
    print("⏳ Step 1: Finding nearby stops...")
    start_stops = nearby_stops(start_coord, bus_data.graph_cache.STOPS_DF, max_walk)
    if not start_stops:
        print("❌ No bus stop near start location")
        return jsonify({"error": "No bus stop near start location"}), 404
    print(f"✅ Found {len(start_stops)} start stops")

    dest_stops = nearby_stops(end_coord, bus_data.graph_cache.STOPS_DF, max_walk)
    if not dest_stops:
        print("❌ No bus stop near destination")
        return jsonify({"error": "No bus stop near destination"}), 404
    print(f"✅ Found {len(dest_stops)} destination stops")

    dest_set = {sid for sid, _ in dest_stops}
    heuristic = make_heuristic(bus_data.graph_cache.STOPS_DF, end_coord, SPEED_MPS)

    # Run A* algorithm with timeout
    print("⏳ Step 2: Running A* algorithm...")
    print(f"   Graph: {bus_data.graph_cache.G_BUS.number_of_nodes()} nodes, {bus_data.graph_cache.G_BUS.number_of_edges()} edges")
    print(f"   Start stops: {len(start_stops)}, Dest stops: {len(dest_stops)}")
    
    t1 = time.time()
    
    try:
        # Run A* with timeout using threading
        import threading
        result = [None]
        error_container = [None]
        
        def run_astar():
            try:
                result[0] = a_star(
                    G=bus_data.graph_cache.G_BUS,
                    route_info=bus_data.graph_cache.ROUTE_INFO,
                    stops = bus_data.graph_cache.STOPS_DF,
                    start_stops=start_stops,
                    dest_stop_set=dest_set,
                    heuristic=heuristic,
                    speed=SPEED_MPS,
                    walk_speed=WALK_SPEED,
                    c=C_FARE,
                    p=P_TRANSFER_PEN
                )
            except Exception as e:
                error_container[0] = str(e)
        
        thread = threading.Thread(target=run_astar)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)  # 60 second timeout
        
        if thread.is_alive():
            print("❌ A* algorithm timeout (>60s)")
            return jsonify({"error": "Route calculation timeout. Try locations closer together or increase max_walk distance."}), 408
        
        if error_container[0]:
            print(f"❌ A* algorithm error: {error_container[0]}")
            return jsonify({"error": f"Route calculation failed: {error_container[0]}"}), 500
        
        print(f"✅ A* completed in {time.time()-t1:.2f}s")
        
    except Exception as e:
        print(f"❌ A* algorithm failed: {e}")
        return jsonify({"error": f"Route calculation failed: {str(e)}"}), 500

    if not result[0]:
        print("❌ No route found")
        return jsonify({"error": "No route found between these locations"}), 404

    # Draw map with Folium (simplified version - no OSM routing)
    print("⏳ Step 3: Drawing map...")
    t2 = time.time()
    
    walk_to_bus = None
    walk_to_des = None
    try:
        walk_to_bus, walk_to_des = calculate_First_Last_walkingCoords(
            start_coord=start_coord,
            dest_coord=end_coord,
            stops_df=bus_data.graph_cache.STOPS_DF,
            path=result[0]["coords"]
        )
        print(f"✅ Calculating walking path in {time.time()-t2:.2f}s")
    except Exception as e:
        print(f"❌ Error Calculating walking path map: {e}")
    
    # Read generated map
    print("⏳ Step 4: Reading map file...")


    special_stops_name, special_stops_coords, walk_coords = calculate_transfer_walkingCoords(result[0]["special_stops"]
                                                                                             , bus_data.graph_cache.STOPS_DF
                                                                                             , result[0]["unique_BusNumbers"]            
                                                                                             , walk_to_bus
                                                                                             , walk_to_des)
    transfers = len(result[0]["unique_BusNumbers"]) - len(walk_coords) + 2
    
    response_data = {
        "fare_vnd": int(result[0]["total_fare"]),
        "best_case_min": int(result[0]["best_min"]),
        "worst_case_min": int(result[0]["worst_min"]),
        "transfers": transfers,
        "specialStopsName": special_stops_name,
        "unique_nameRoutes": result[0]["unique_Routes"],
        "unique_BusNumbers": result[0]["unique_BusNumbers"],
        "walk_coords": walk_coords,
        "BusRoute_coords": special_stops_coords
    }

    total_time = time.time() - start_time
    print(f"✅ Bus route calculated in {total_time:.2f}s")
    
    return jsonify(to_python(response_data))


# ----------------------------
# API ROUTE - Groq TRIP PLAN
# ----------------------------
@app.route("/api/groq", methods=["POST"])
def api_groq():   
    data = request.json
    
    if "query" not in data:
        return jsonify({"error": "Missing 'query' in JSON body"}), 400
    
    if not MATCH_TRIP_AVAILABLE:
        return jsonify({"error": "Match trip module not available"}), 503

    user_query = data["query"]
    plan = generate_trip_plan(user_query, trip_data.match_cache.DB_ITEMS, trip_data.match_cache.TOKEN_INDEX)

    # cal route path coords
    itinerary = plan.get("itinerary", [])
    route_lines = []

    # Loop through consecutive itinerary points
    for i in range(len(itinerary) - 1):
        start = itinerary[i]
        end = itinerary[i + 1]

        # Ensure coordinates exist
        if "lat" in start and "lng" in start and "lat" in end and "lng" in end:
            try:
                coords = calculate_route(
                    {"lat": start["lat"], "lon": start["lng"]},
                    {"lat": end["lat"], "lon": end["lng"]}
                )["coords"]

                route_lines.append({
                    "from_index": i,
                    "to_index": i + 1,
                    "coords": coords
                })

            except Exception as e:
                print("Route generation error:", e)
                route_lines.append({
                    "from_index": i,
                    "to_index": i + 1,
                    "coords": []
                })

    # Attach route_lines to plan
    plan["route_lines"] = route_lines

    return jsonify(plan)

@app.route('/images/<path:filename>')
def serve_trip_image(filename):
    """
    Serve any image inside /images/, including subfolders.
    Example:
      /images/landmarks/Ben Thanh Market/cover.jpg
    """
    print("Serving image:", filename)
    return send_from_directory(IMAGE_TRIP_FOLDER, filename)

# ============================
# 🚀 RUN SERVER
# ============================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Combined Flask API Server")
    print("=" * 60)
    print(f"\n📂 Camera frames directory: {os.path.abspath(CAMERA_FRAMES_DIR)}")
    print(f"📂 SOS images directory:    {os.path.abspath(SOS_UPLOAD_DIR)}")
    print(f"🚌 Bus routing:             {'✅ Available' if BUS_ROUTING_AVAILABLE else '❌ Not available'}")
    if BUS_ROUTING_AVAILABLE:
        import os
        cache_exists = os.path.exists('cache/bus_graph_cache.pkl')
        print(f"💾 Cache status:            {'✅ Active' if cache_exists else '❌ Not cached yet'}")
    print("\n🌐 Server running on http://localhost:5000")
    print("\n📋 Available endpoints:")
    
    print("\n  === 🔐 Auth & User ===")
    print("  POST /api/auth/register           - Register new user")
    print("  POST /api/auth/login              - Login user")
    print("  POST /api/auth/github             - GitHub OAuth login")
    print("  POST /api/auth/google             - Google OAuth login")
    print("  POST /api/auth/facebook           - Facebook OAuth login")
    print("  GET/POST /api/user/locations      - Get/Save recent locations")
    print("  GET/POST /api/user/routes         - Get/Save recent routes")
    
    print("\n  === 🆘 SOS APIs ===")
    print("  POST /api/sos                     - Report SOS (Multipart/Form-data)")
    print("  GET  /api/sos                     - Get active SOS alerts")
    print("  POST /api/sos/resolve             - Mark SOS as resolved")
    print("  POST /api/sos/comment             - Add comment to SOS")
    print("  GET  /api/sos/comments/<sos_id>   - Get comments for SOS")
    print("  POST /api/sos/report              - Report SOS as fake/spam")
    print("  GET  /sos_images/<filename>       - Serve SOS image")
    
    print("\n  === 🗺️  TomTom Routing & Search ===")
    print("  POST /search                      - Search location in HCM")
    print("  POST /route                       - Calculate route between two points")
    print("  POST /render-map                  - Render route map to HTML")
    
    print("\n  === 📷 Camera APIs ===")
    print("  GET  /api/cameras                 - List all cameras")
    print("  GET  /api/camera/<id>/images      - Get images for a camera")
    print("  GET  /api/camera/<id>/proxy       - Proxy camera image (real-time from server)")
    print("  GET  /camera_frames/<id>/<file>   - Serve camera image file")
    print("  GET  /api/stats                   - Get statistics (total cameras, images)")

    print("\n  === 👤 Camera on Route Detection ===")
    print("  POST /api/detect/route-cameras    - Run detection for cameras on route")
    print("  GET  /api/congestion/geojson      - Get congestion GeoJSON data")
    
    if BUS_ROUTING_AVAILABLE:
        print("\n  === 🚌 Bus Routing API ===")
        print("  GET  /api/bus/route               - Calculate bus route")
        print("       Params: start_lat, start_lng, end_lat, end_lng, max_walk")
        print("       Returns: fare, duration, transfers, bus routes, walking paths")
    print("\n  === Route Camera Detection ===")
    print("  POST /api/detect/route-cameras - Run detection for cameras on route")
    print("  GET  /api/congestion/geojson   - Get congestion GeoJSON data")
    print("\n" + "=" * 60 + "\n")
    
    # Run server with reloader disabled to prevent double initialization
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)