# 🚀 Combined Flask API Server

Server Flask tích hợp tất cả các API: Auth, Routes, Camera, SOS, và Bus Routing.

## 📦 Requirements

```bash
pip install flask flask-cors requests folium mysql-connector-python bcrypt pyjwt numpy pandas networkx
```

## 🗂️ File Structure

```
temp_server/
├── API.py                      # Main server file
├── Bus_Routing_Module.py       # Bus routing algorithm
├── draw_bus_path.py            # Draw bus route on map
├── graph_cache.py              # Cache bus graph data
├── routes.csv                  # Bus routes data
├── stops.csv                   # Bus stops data
├── trips.csv                   # Bus trips data
├── car_data.json               # Car routing data
├── walk_data.json              # Walking routing data
├── camera_locations.json       # Camera locations
├── camera_frames/              # Camera images folder
└── sos_images/                 # SOS images folder
```

## 🚀 Start Server

```bash
cd temp_server
python API.py
```

Server sẽ chạy tại: `http://localhost:5000`

## 📡 API Endpoints

### 🔐 Authentication
- `POST /api/auth/register` - Đăng ký user mới
- `POST /api/auth/login` - Đăng nhập

### 💾 User Data
- `GET/POST /api/user/locations` - Lấy/Lưu địa điểm
- `GET/POST /api/user/routes` - Lấy/Lưu tuyến đường

### 🚨 SOS
- `POST /api/sos` - Báo cáo SOS (với hình ảnh)
- `GET /api/sos` - Lấy danh sách SOS đang active
- `POST /api/sos/resolve` - Đánh dấu SOS đã giải quyết
- `GET /sos_images/<filename>` - Xem ảnh SOS

### 🗺️ TomTom Routing
- `POST /search` - Tìm kiếm địa điểm trong HCM
- `POST /route` - Tính toán tuyến đường (car/motorcycle/bicycle/pedestrian)
- `POST /render-map` - Render bản đồ HTML

### 📷 Camera
- `GET /api/cameras` - Danh sách tất cả camera
- `GET /api/camera/<id>/images` - Lấy ảnh từ camera
- `GET /api/camera/<id>/proxy` - Proxy ảnh camera
- `GET /api/stats` - Thống kê camera

### 🚌 Bus Routing (NEW!)
- `GET /api/bus/route` - Tính toán tuyến xe buýt

**Parameters:**
- `start_lat` (float): Vĩ độ điểm bắt đầu
- `start_lng` (float): Kinh độ điểm bắt đầu
- `end_lat` (float): Vĩ độ điểm đến
- `end_lng` (float): Kinh độ điểm đến
- `max_walk` (float, optional): Khoảng cách đi bộ tối đa (mét), mặc định 400m

**Example:**
```
GET http://localhost:5000/api/bus/route?start_lat=10.762622&start_lng=106.660172&end_lat=10.772622&end_lng=106.670172&max_walk=500
```

**Response:**
```json
{
  "fare_vnd": 7000,
  "best_case_min": 25.5,
  "worst_case_min": 35.2,
  "transfers": 1,
  "map_url": "/static/route_abc123.html",
  "map_html": "<html>...</html>",
  "specialStops": ["Bến xe Miền Đông", "Chợ Bến Thành"],
  "stops": [
    {"lat": 10.762622, "lon": 106.660172},
    ...
  ]
}
```

## 🔧 Configuration

### Database (MySQL)
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'osm_app'
}
```

### API Keys
```python
TOMTOM_API_KEY = "your_tomtom_api_key"
SECRET_KEY = "your_jwt_secret_key"
```

## 🗄️ Database Schema

```sql
CREATE DATABASE osm_app;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    lat DOUBLE NOT NULL,
    lng DOUBLE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE user_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_name VARCHAR(255) NOT NULL,
    start_lat DOUBLE NOT NULL,
    start_lng DOUBLE NOT NULL,
    end_name VARCHAR(255) NOT NULL,
    end_lat DOUBLE NOT NULL,
    end_lng DOUBLE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE sos_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    lat DOUBLE NOT NULL,
    lng DOUBLE NOT NULL,
    description TEXT,
    image_url VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🐛 Troubleshooting

### Bus routing not working
- Kiểm tra các file CSV (routes.csv, stops.csv, trips.csv) có tồn tại không
- Kiểm tra car_data.json và walk_data.json
- Xem log khi server khởi động: "✅ Bus routing data loaded successfully"

### Camera images not loading
- Kiểm tra camera_locations.json
- Kiểm tra kết nối internet (proxy từ HCMC traffic server)

### Database connection error
- Kiểm tra MySQL đã chạy chưa
- Kiểm tra DB_CONFIG
- Tạo database và tables theo schema ở trên

## 📝 Notes

- Server chạy ở port 5000
- Frontend React chạy ở port 3000
- CORS đã được enable cho localhost:3000
- Bus routing data được load khi server khởi động
- Token JWT hết hạn sau 24 giờ
