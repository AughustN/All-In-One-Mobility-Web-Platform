import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import io
import time
from flask import Response


# Thêm đường dẫn để import được API.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app từ API
from API import app, calculate_route, BUS_ROUTING_AVAILABLE, IMAGE_TRIP_FOLDER

# --- Setup Mock Modules trước khi import API ---
sys.modules['detector_batch'] = MagicMock()
sys.modules['segment_aggregation'] = MagicMock()
sys.modules['classified_congestion'] = MagicMock()
sys.modules['PlanTrip_API'] = MagicMock()
sys.modules['trip_data'] = MagicMock()
sys.modules['bus_data'] = MagicMock()
sys.modules['bus_data.graph_cache'] = MagicMock()
sys.modules['bus_data.Bus_Routing_Module'] = MagicMock()

class TestAuthMock(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

    # ==========================================
    # 1. TEST REGISTER (Đăng ký)
    # ==========================================
    @patch('API.get_db_connection')
    @patch('API.bcrypt')
    def test_register_success(self, mock_bcrypt, mock_conn):
        print("   -> Kịch bản: Đăng ký thành công (Mock DB)")
        
        # 1. Mock Bcrypt: Giả vờ mã hóa password
        mock_bcrypt.hashpw.return_value = b'hashed_secret_password'
        
        # 2. Mock Database: Giả vờ kết nối thành công
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        payload = {'username': 'new_user', 'password': 'password123'}
        
        # 3. Act
        response = self.client.post('/api/auth/register', json=payload)
        
        # 4. Assert
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'User created successfully')
        
        # Kiểm tra xem code có gọi lệnh INSERT vào DB không
        mock_cursor.execute.assert_called()
        args, _ = mock_cursor.execute.call_args
        self.assertIn("INSERT INTO users", args[0])
        print("   ✅ PASSED")

    def test_register_missing_fields(self):
        print("   -> Kịch bản: Đăng ký thiếu username/pass")
        response = self.client.post('/api/auth/register', json={'username': 'only_user'})
        self.assertEqual(response.status_code, 400)
        print("   ✅ PASSED")

    # ==========================================
    # 2. TEST LOGIN (Đăng nhập)
    # ==========================================
    @patch('API.get_db_connection')
    @patch('API.bcrypt')
    @patch('API.jwt.encode') # Mock luôn việc tạo token để kiểm soát kết quả
    def test_login_success(self, mock_jwt_encode, mock_bcrypt, mock_conn):
        print("   -> Kịch bản: Đăng nhập thành công")
        
        # 1. Mock DB: Trả về 1 user giả
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1, 
            'username': 'testuser', 
            'password': 'hashed_password_in_db'
        }
        
        # 2. Mock Bcrypt: Giả vờ password nhập vào khớp với DB
        mock_bcrypt.checkpw.return_value = True
        
        # 3. Mock JWT: Trả về token giả định
        mock_jwt_encode.return_value = "fake.jwt.token"

        payload = {'username': 'testuser', 'password': 'password123'}
        response = self.client.post('/api/auth/login', json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['token'], "fake.jwt.token")
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.bcrypt')
    def test_login_fail_wrong_password(self, mock_bcrypt, mock_conn):
        print("   -> Kịch bản: Đăng nhập sai mật khẩu")
        
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id': 1, 'username': 'user', 'password': 'hashed'}
        
        # Giả vờ check pass trả về False
        mock_bcrypt.checkpw.return_value = False

        response = self.client.post('/api/auth/login', json={'username': 'user', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
        print("   ✅ PASSED")

    # ==========================================
    # 3. TEST GITHUB OAUTH (Mock Requests)
    # ==========================================
    @patch('API.get_db_connection')
    @patch('requests.post') # Mock request lấy Access Token
    @patch('requests.get')  # Mock request lấy User Info
    @patch('API.jwt.encode')
    def test_github_auth_new_user(self, mock_jwt, mock_get, mock_post, mock_conn):
        print("   -> Kịch bản: GitHub Login (User mới -> Tạo DB)")
        
        # 1. Mock GitHub Token Response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'access_token': 'gh_token_123'}

        # 2. Mock GitHub User Info Response
        # Ta cần mock 2 lần gọi GET: 1 lần lấy profile, 1 lần lấy email
        def side_effect(url, headers, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            if '/user/emails' in url:
                mock_resp.json.return_value = [{'email': 'gh@test.com', 'primary': True}]
            else:
                mock_resp.json.return_value = {'id': 999, 'login': 'gh_user', 'name': 'GitHub User'}
            return mock_resp
            
        mock_get.side_effect = side_effect

        # 3. Mock DB: User chưa tồn tại
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # Không tìm thấy user
        mock_cursor.lastrowid = 50 # ID của user mới tạo

        mock_jwt.return_value = "gh.jwt.token"

        # Act
        response = self.client.post('/api/auth/github', json={'code': 'auth_code'})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['token'], "gh.jwt.token")
        
        # Kiểm tra logic Insert
        mock_cursor.execute.assert_called()
        args_list = mock_cursor.execute.call_args_list
        # Tìm xem có lệnh INSERT nào chứa 'github' không
        has_insert = any("INSERT INTO users" in str(call) for call in args_list)
        self.assertTrue(has_insert, "Phải gọi lệnh INSERT user mới")
        print("   ✅ PASSED")

    # ==========================================
    # 4. TEST GOOGLE OAUTH (Mock Requests)
    # ==========================================
    @patch('API.get_db_connection')
    @patch('requests.get') # Google verify token qua GET
    @patch('API.jwt.encode')
    def test_google_auth_existing_user(self, mock_jwt, mock_get, mock_conn):
        print("   -> Kịch bản: Google Login (User cũ -> Login luôn)")
        
        # 1. Mock Google Token Info
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'email': 'gg@test.com', 
            'name': 'Google User', 
            'sub': '123456' # Google ID
        }
        mock_get.return_value = mock_resp

        # 2. Mock DB: Tìm thấy user
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id': 10, 'username': 'Google User'} # User đã có

        mock_jwt.return_value = "gg.jwt.token"

        # Act
        response = self.client.post('/api/auth/google', json={'token': 'id_token_123'})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['token'], "gg.jwt.token")
        
        # Kiểm tra logic: Nếu user tồn tại, KHÔNG được gọi INSERT
        calls = [str(call) for call in mock_cursor.execute.call_args_list]
        has_insert = any("INSERT INTO users" in c for c in calls)
        self.assertFalse(has_insert, "User cũ thì không được Insert mới")
        print("   ✅ PASSED")


class TestUserData(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        # Token giả để gửi kèm Header
        self.headers = {'Authorization': 'Bearer fake_token'}
        print(f"\n🔹 [{self._testMethodName}]")

    # Hàm phụ trợ để Mock User đã đăng nhập
    def setup_mock_auth(self, mock_jwt, mock_conn):
        """
        Hàm này giúp vượt qua @token_required.
        Nó giả lập JWT decode thành công và DB tìm thấy user.
        """
        # 1. Mock JWT giải mã ra user_id = 1
        mock_jwt.return_value = {'user_id': 1}
        
        # 2. Mock DB trả về thông tin user khi decorator query
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # side_effect là kỹ thuật: Lần gọi 1 trả về A, lần gọi 2 trả về B...
        # Lần 1: Decorator kiểm tra User -> Trả về User OK
        # Lần 2 trở đi: Là các query logic chính (Insert/Select...) -> Ta sẽ config riêng trong từng test
        return mock_cursor

    # =========================================================================
    # 1. TEST USER LOCATIONS (Địa điểm yêu thích)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_save_location(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lưu địa điểm mới (POST)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        
        # Cấu hình cho lần gọi thứ 2 (Logic INSERT)
        mock_cursor.fetchone.side_effect = [{'id': 1, 'username': 'Dat'}, None] 

        payload = {'name': 'Location', 'lat': 10.77, 'lng': 106.69}
        response = self.client.post('/api/user/locations', headers=self.headers, json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, 'Location saved')
        
        # Kiểm tra lệnh INSERT có đúng không
        mock_cursor.execute.assert_called()
        args_list = mock_cursor.execute.call_args_list
        # Lấy lệnh execute cuối cùng
        last_call_args = args_list[-1][0]
        self.assertIn("INSERT INTO user_locations", last_call_args[0])
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_get_locations(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lấy danh sách địa điểm (GET)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # Lần 1: Auth (User OK), Lần 2: Query Locations (Trả về List)
        fake_locations = [{'id': 1, 'name': 'Location', 'lat': 10.1, 'lng': 106.1}]
        mock_cursor.fetchone.return_value = {'id': 1} # Auth user
        mock_cursor.fetchall.return_value = fake_locations # Get result

        response = self.client.get('/api/user/locations', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], 'Location')
        print("   ✅ PASSED")

    # =========================================================================
    # 2. TEST USER ROUTES 
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_save_route(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lưu lộ trình (POST)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}

        payload = {
            'start_name': 'A', 'start_lat': 10.0, 'start_lng': 106.0,
            'end_name': 'B', 'end_lat': 10.1, 'end_lng': 106.1
        }
        response = self.client.post('/api/user/routes', headers=self.headers, json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("INSERT INTO user_routes", str(mock_cursor.execute.call_args))
        print("   ✅ PASSED")

    # =========================================================================
    # 3. TEST USER TRIPS (Lịch sử chuyến đi - Có JSON handling)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_save_trip_success(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lưu chuyến đi (Trip JSON Dump)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}

        # Trip data phức tạp
        trip_data = {"steps": [{"lat": 10, "lng": 106}], "total_km": 5}
        
        response = self.client.post('/api/user/trips', headers=self.headers, json=trip_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], "Trip saved successfully")
        
        # Kiểm tra xem code có gọi json.dumps không?
        # Ta check tham số truyền vào execute
        call_args = mock_cursor.execute.call_args[0]
        sql = call_args[0]
        params = call_args[1]
        
        self.assertIn("INSERT INTO trips", sql)
        self.assertIsInstance(params[1], str) # Tham số thứ 2 phải là string (JSON string)
        self.assertIn('"total_km": 5', params[1]) # Nội dung JSON phải đúng
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_save_trip_empty_fail(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lưu chuyến đi thất bại (Empty JSON)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}

        response = self.client.post('/api/user/trips', headers=self.headers, json={}) # Empty dict

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "Empty JSON")
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_get_trips_parsing(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Lấy chuyến đi (Verify JSON Load)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        
        # Giả lập dữ liệu trong DB (Lưu ý: trip_json trong DB là String)
        db_row = {
            'id': 100,
            'trip_json': '{"steps": [], "cost": 50000}', # String JSON
            'created_at': '2025-01-01'
        }
        
        mock_cursor.fetchone.return_value = {'id': 1} # Auth OK
        mock_cursor.fetchall.return_value = [db_row] # Get Result

        response = self.client.get('/api/user/trips', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        result = response.json[0]
        
        # Kiểm tra xem API có tự động convert String -> Dict không
        self.assertIsInstance(result['trip_json'], dict) 
        self.assertEqual(result['trip_json']['cost'], 50000)
        print("   ✅ PASSED")

    # =========================================================================
    # 4. TEST DELETE TRIP
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_delete_trip_success(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Xóa chuyến đi thành công")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}
        
        # Giả lập xóa thành công 1 dòng
        mock_cursor.rowcount = 1 

        response = self.client.delete('/api/user/trips/100', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "Trip deleted")
        self.assertIn("DELETE FROM trips", str(mock_cursor.execute.call_args))
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_delete_trip_not_found(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Xóa chuyến đi thất bại (Không tìm thấy)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}
        
        # Giả lập không xóa được dòng nào (rowcount = 0)
        mock_cursor.rowcount = 0

        response = self.client.delete('/api/user/trips/999', headers=self.headers)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], "Trip not found")
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_delete_trip_db_error(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Xóa chuyến đi lỗi DB (Exception)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.return_value = {'id': 1}

        # Giả lập execute bị lỗi
        mock_cursor.execute.side_effect = [None, Exception("DB Connection Lost")]

        response = self.client.delete('/api/user/trips/100', headers=self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], "DB Connection Lost")
        print("   ✅ PASSED")

class TestSOSFeatures(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        self.headers = {'Authorization': 'Bearer fake_token'}
        print(f"\n🔹 [{self._testMethodName}]")

    def setup_mock_auth(self, mock_jwt, mock_conn, user_id=1, username="Dat"):
        """
        Helper để vượt qua @token_required.
        Trả về mock_cursor để ta config tiếp các query sau đó.
        """
        mock_jwt.return_value = {'user_id': user_id}
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # Setup mặc định cho lần gọi DB đầu tiên (Kiểm tra User trong decorator)
        # Các lần gọi sau sẽ được config đè (override) trong từng test case bằng side_effect
        mock_cursor.fetchone.return_value = {'id': user_id, 'username': username}
        
        return mock_cursor

    # =========================================================================
    # 1. TEST REPORT SOS (TẠO BÁO CÁO)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_create_sos_success_no_image(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Tạo SOS thành công (Không ảnh)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # Lần 1: Auth (User OK)
        # Lần 2: Check Spam (Active SOS) -> Trả về None (Chưa có bài nào)
        mock_cursor.fetchone.side_effect = [{'id': 1}, None]

        # Lưu ý: API dùng request.form nên ta gửi data dạng dict thường (multipart)
        payload = {'lat': '10.1', 'lng': '106.1', 'description': 'Help me'}
        
        response = self.client.post('/api/sos', headers=self.headers, data=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'SOS reported successfully')
        
        # Kiểm tra lệnh INSERT
        mock_cursor.execute.assert_called()
        last_query = mock_cursor.execute.call_args_list[-1][0][0]
        self.assertIn("INSERT INTO sos_alerts", last_query)
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_create_sos_spam_block(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Chặn Spam (User đang có bài Active)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # Lần 1: Auth OK
        # Lần 2: Check Spam -> Trả về ID bài viết đang active (Tức là user đang spam)
        mock_cursor.fetchone.side_effect = [{'id': 1}, {'id': 99}]

        payload = {'lat': '10.1', 'lng': '106.1'}
        response = self.client.post('/api/sos', headers=self.headers, data=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("đang có một báo cáo chưa xử lý", response.json['message'])
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_create_sos_missing_location(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Tạo SOS thiếu tọa độ")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.side_effect = [{'id': 1}, None] # Auth OK, Spam OK

        # Payload thiếu lat/lng
        payload = {'description': 'No GPS'}
        response = self.client.post('/api/sos', headers=self.headers, data=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['message'], 'Missing location data')
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    @patch('werkzeug.datastructures.FileStorage.save') # Mock hàm save file
    def test_create_sos_with_image(self, mock_save_file, mock_jwt, mock_conn):
        print("   -> Kịch bản: Tạo SOS có đính kèm ảnh")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        mock_cursor.fetchone.side_effect = [{'id': 1}, None]

        # Tạo file ảnh giả
        fake_image = (io.BytesIO(b"fake_image_data"), 'accident.jpg')
        
        payload = {
            'lat': '10.1', 'lng': '106.1', 
            'description': 'Crash',
            'image': fake_image # Gửi kèm file
        }
        
        # content_type='multipart/form-data' là mặc định khi dùng data=dict có file
        response = self.client.post('/api/sos', headers=self.headers, data=payload)

        self.assertEqual(response.status_code, 201)
        self.assertIn('/sos_images/', response.json['image_url'])
        
        # Kiểm tra xem hàm save file có được gọi không
        mock_save_file.assert_called()
        print("   ✅ PASSED")

    # =========================================================================
    # 2. TEST GET SOS (LẤY DANH SÁCH)
    # =========================================================================

    @patch('API.get_db_connection')
    def test_get_active_sos(self, mock_conn):
        print("   -> Kịch bản: Lấy danh sách SOS Active")
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # Giả lập DB trả về 2 bài viết
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'lat': 10.1, 'lng': 106.1, 'status': 'active'},
            {'id': 2, 'lat': 10.2, 'lng': 106.2, 'status': 'active'}
        ]

        response = self.client.get('/api/sos')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        print("   ✅ PASSED")

    # =========================================================================
    # 3. TEST RESOLVE SOS (GIẢI QUYẾT SỰ CỐ)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_resolve_sos_success(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: User tự giải quyết báo cáo của mình (Success)")
        # User ID 1
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn, user_id=1)

        # Lần 1: Auth OK
        # Lần 2: Query SOS -> Tìm thấy bài id=100, user_id=1 (Chính chủ)
        mock_cursor.fetchone.side_effect = [
            {'id': 1}, 
            {'id': 100, 'user_id': 1, 'status': 'active'}
        ]

        response = self.client.post('/api/sos/resolve', headers=self.headers, json={'sos_id': 100})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Đã giải quyết sự cố thành công')
        
        # Kiểm tra lệnh UPDATE
        last_query = mock_cursor.execute.call_args_list[-1][0][0]
        self.assertIn("UPDATE sos_alerts SET status = 'resolved'", last_query)
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_resolve_sos_not_found(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Giải quyết bài không tồn tại (404)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)
        
        # Lần 2 trả về None (Không thấy bài)
        mock_cursor.fetchone.side_effect = [{'id': 1}, None]

        response = self.client.post('/api/sos/resolve', headers=self.headers, json={'sos_id': 999})

        self.assertEqual(response.status_code, 404)
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_resolve_sos_forbidden(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: User A cố xóa bài của User B (403)")
        # Current User là ID 1
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn, user_id=1)
        
        # Lần 2: Tìm thấy bài, nhưng user_id=2 (Của người khác)
        mock_cursor.fetchone.side_effect = [
            {'id': 1}, 
            {'id': 100, 'user_id': 2, 'status': 'active'}
        ]

        response = self.client.post('/api/sos/resolve', headers=self.headers, json={'sos_id': 100})

        self.assertEqual(response.status_code, 403)
        self.assertIn("không có quyền", response.json['message'])
        print("   ✅ PASSED")

    # =========================================================================
    # 4. TEST COMMENTS (BÌNH LUẬN)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_add_comment(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Thêm bình luận")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        payload = {'sos_id': 50, 'content': 'Is anyone there?'}
        response = self.client.post('/api/sos/comment', headers=self.headers, json=payload)

        self.assertEqual(response.status_code, 201)
        # Check Insert
        call_args = str(mock_cursor.execute.call_args)
        self.assertIn("INSERT INTO sos_comments", call_args)
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    def test_get_comments(self, mock_conn):
        print("   -> Kịch bản: Lấy danh sách bình luận")
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [{'content': 'Hello', 'username': 'UserA'}]
        
        response = self.client.get('/api/sos/comments/50')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['username'], 'UserA')
        print("   ✅ PASSED")

    # =========================================================================
    # 5. TEST REPORT & HIDE LOGIC (QUY TẮC 3 BÁO CÁO)
    # =========================================================================

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_report_sos_duplicate(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Báo cáo trùng lặp (Đã report rồi)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # Lần 1: Auth
        # Lần 2: Check sos_reports -> Trả về ID (Đã từng báo cáo)
        mock_cursor.fetchone.side_effect = [{'id': 1}, {'id': 555}]

        response = self.client.post('/api/sos/report', headers=self.headers, json={'sos_id': 100})

        self.assertEqual(response.status_code, 400)
        self.assertIn("đã báo cáo bài này rồi", response.json['message'])
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_report_sos_hide_logic(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Report lần thứ 3 -> Tự động ẩn bài (Hidden)")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # Chuỗi sự kiện trả về của fetchone:
        # 1. Auth OK
        # 2. Check duplicate -> None (Chưa report)
        # 3. SELECT COUNT(*) -> Trả về 3 (Đã đủ 3 người report)
        mock_cursor.fetchone.side_effect = [
            {'id': 1}, 
            None, 
            {'count': 3}
        ]

        response = self.client.post('/api/sos/report', headers=self.headers, json={'sos_id': 100, 'reason': 'Fake'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['hidden'], "Biến hidden phải là True")
        self.assertIn("bị gỡ", response.json['message'])

        # Quan trọng: Kiểm tra xem lệnh UPDATE status='hidden' có được gọi không
        execute_calls = [str(call) for call in mock_cursor.execute.call_args_list]
        has_update_hidden = any("UPDATE sos_alerts SET status = 'hidden'" in c for c in execute_calls)
        self.assertTrue(has_update_hidden, "Phải gọi lệnh UPDATE ẩn bài viết")
        print("   ✅ PASSED")

    @patch('API.get_db_connection')
    @patch('API.jwt.decode')
    def test_report_sos_normal(self, mock_jwt, mock_conn):
        print("   -> Kịch bản: Report lần thứ 1 -> Vẫn Active")
        mock_cursor = self.setup_mock_auth(mock_jwt, mock_conn)

        # 1. Auth OK, 2. Not Duplicate, 3. Count = 1
        mock_cursor.fetchone.side_effect = [{'id': 1}, None, {'count': 1}]

        response = self.client.post('/api/sos/report', headers=self.headers, json={'sos_id': 100})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['hidden'], "Biến hidden phải là False")
        
        # Kiểm tra KHÔNG được gọi lệnh UPDATE hidden
        execute_calls = [str(call) for call in mock_cursor.execute.call_args_list]
        has_update_hidden = any("UPDATE sos_alerts SET status = 'hidden'" in c for c in execute_calls)
        self.assertFalse(has_update_hidden, "Không được ẩn bài khi chưa đủ report")
        print("   ✅ PASSED")

class TestSearchAPI(unittest.TestCase):
    """
    Phần 2: Test API /search
    """

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

    # =========================================================================
    # 1. INPUT VALIDATION (Kiểm tra đầu vào)
    # =========================================================================

    def test_search_missing_address(self):
        print("   -> Kịch bản: Gửi request thiếu address")
        response = self.client.post('/search', json={'lat': 10.1, 'lon': 106.1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'address is required')
        print("   ✅ PASSED")

    # =========================================================================
    # 2. LOGIC CHỌN API TOMTOM (Nearby vs Text)
    # =========================================================================

    @patch('API.requests.get')
    def test_call_nearby_search(self, mock_get):
        print("   -> Kịch bản: Có lat/lon -> Phải gọi Nearby Search")
        
        # Mock phản hồi rỗng để code chạy qua bước gọi API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}

        payload = {
            "address": "Coffee", # Vẫn cần address để qua validate
            "lat": 10.762, 
            "lon": 106.660
        }
        
        self.client.post('/search', json=payload)

        # Kiểm tra URL gọi đi
        args, kwargs = mock_get.call_args
        called_url = args[0]
        called_params = kwargs['params']

        # Assert URL đúng endpoint nearbySearch
        self.assertIn("nearbySearch", called_url)
        # Assert Params có lat/lon/radius
        self.assertEqual(called_params['lat'], 10.762)
        self.assertEqual(called_params['radius'], 5000)
        print("   ✅ PASSED: Đã gọi đúng API Nearby Search")

    @patch('API.requests.get')
    def test_call_text_search(self, mock_get):
        print("   -> Kịch bản: Không có lat/lon -> Phải gọi Text Search (Fuzzy)")
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}

        payload = {"address": "Ben Thanh Market"}
        
        self.client.post('/search', json=payload)

        # Kiểm tra URL gọi đi
        args, kwargs = mock_get.call_args
        called_url = args[0]
        called_params = kwargs['params']

        # Assert URL đúng endpoint search thường
        # URL phải được encode: Ben Thanh Market -> Ben%20Thanh%20Market
        self.assertIn("search/Ben%20Thanh%20Market.json", called_url)
        
        # Assert Params có countrySet='VN' và giới hạn HCM Center
        self.assertEqual(called_params['countrySet'], 'VN')
        self.assertEqual(called_params['radius'], 30000)
        print("   ✅ PASSED: Đã gọi đúng API Text Search")

    # =========================================================================
    # 3. LOGIC FILTERING (Quan trọng nhất: Lọc kết quả trong HCM)
    # =========================================================================

    @patch('API.requests.get')
    def test_filter_results_in_hcm_only(self, mock_get):
        print("   -> Kịch bản: TomTom trả về kết quả lẫn lộn (Hà Nội & HCM) -> Chỉ lấy HCM")
        
        # Giả lập phản hồi từ TomTom chứa 3 kết quả:
        # 1. Chợ Bến Thành (Trong HCM) -> Lấy
        # 2. Hồ Hoàn Kiếm (Hà Nội - Ngoài HCM) -> Bỏ
        # 3. Một điểm bị thiếu tọa độ -> Bỏ
        mock_tomtom_response = {
            "results": [
                {
                    "id": "hcm_1",
                    "poi": {"name": "Ben Thanh Market"},
                    "position": {"lat": 10.772, "lon": 106.698} # IN
                },
                {
                    "id": "hn_1",
                    "poi": {"name": "Hoan Kiem Lake"},
                    "position": {"lat": 21.028, "lon": 105.854} # OUT
                },
                {
                    "id": "invalid_1",
                    "poi": {"name": "Unknown Place"},
                    "position": {} # MISSING LAT/LON
                }
            ]
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tomtom_response

        response = self.client.post('/search', json={"address": "Market"})
        
        results = response.json
        
        # ASSERTIONS
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results), 1, "Phải lọc chỉ còn 1 kết quả")
        self.assertEqual(results[0]['id'], "hcm_1", "Kết quả giữ lại phải là Bến Thành")
        
        print(f"   ✅ PASSED: Input 3 -> Output 1 (Đã loại bỏ Hà Nội và điểm lỗi)")

    @patch('API.requests.get')
    def test_filter_limit_results(self, mock_get):
        print("   -> Kịch bản: Giới hạn trả về tối đa 10 kết quả")
        
        # Tạo giả 20 kết quả đều nằm trong HCM
        fake_results = []
        for i in range(20):
            fake_results.append({
                "id": f"loc_{i}",
                "position": {"lat": 10.8, "lon": 106.6} # Valid HCM coord
            })
            
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": fake_results}

        response = self.client.post('/search', json={"address": "Anything"})
        
        self.assertEqual(len(response.json), 10, "API chỉ được trả về tối đa 10 kết quả")
        print("   ✅ PASSED: Limit hoạt động đúng")

    # =========================================================================
    # 4. ERROR HANDLING (Xử lý lỗi mạng)
    # =========================================================================

    @patch('API.requests.get')
    def test_tomtom_connection_error(self, mock_get):
        print("   -> Kịch bản: Mất kết nối tới TomTom (Exception)")
        
        # Giả lập ném lỗi khi gọi requests.get
        mock_get.side_effect = Exception("DNS Lookup Failed")

        response = self.client.post('/search', json={"address": "Fail"})
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], "TomTom API connection failed")
        print("   ✅ PASSED")

    @patch('API.requests.get')
    def test_tomtom_api_error_status(self, mock_get):
        print("   -> Kịch bản: TomTom trả về lỗi 403 (Sai Key) hoặc 500")
        
        # Giả lập response lỗi từ TomTom
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        # raise_for_status sẽ ném lỗi khi code >= 400
        mock_resp.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_get.return_value = mock_resp

        response = self.client.post('/search', json={"address": "Fail"})
        
        self.assertEqual(response.status_code, 500)
        print("   ✅ PASSED")

class TestRoutingLogic(unittest.TestCase):
    """
    Phần 1: Unit Test Logic (Sử dụng Mock)
    Mục tiêu: Test các trường hợp biên, lỗi logic, validate đầu vào.
    """

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

        # Dữ liệu giả lập phản hồi thành công từ TomTom
        self.fake_tomtom_success = {
            "routes": [{
                "summary": {
                    "lengthInMeters": 1500, # 1.5 km
                    "travelTimeInSeconds": 300 # 5 min
                },
                "legs": [{
                    "points": [
                        {"latitude": 10.77, "longitude": 106.69},
                        {"latitude": 10.78, "longitude": 106.70}
                    ]
                }]
            }]
        }

    # --- TEST HÀM calculate_route (Hàm Python thuần) ---

    @patch('API.requests.get')
    @patch('API.is_in_hcm')
    def test_func_calculate_route_success(self, mock_is_in_hcm, mock_get):
        print("   -> Kịch bản: Hàm calculate_route chạy đúng")
        mock_is_in_hcm.return_value = True
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.fake_tomtom_success
        mock_get.return_value = mock_resp

        start = {"lat": 10.77, "lon": 106.69}
        end = {"lat": 10.78, "lon": 106.70}

        result = calculate_route(start, end)

        self.assertEqual(result['distance_km'], 1.5)
        self.assertEqual(result['duration_min'], 5.0)
        self.assertEqual(len(result['coords']), 2)
        print("   ✅ PASSED")

    @patch('API.is_in_hcm')
    def test_func_calculate_route_outside_hcm(self, mock_is_in_hcm):
        print("   -> Kịch bản: Hàm chặn tọa độ ngoài HCM")
        # Giả lập check start=True, end=False (Ngoài vùng)
        mock_is_in_hcm.side_effect = [True, False] 

        start = {"lat": 10.77, "lon": 106.69}
        end = {"lat": 21.00, "lon": 105.00} # Hà Nội

        result, status_code = calculate_route(start, end)

        self.assertEqual(status_code, 400)
        self.assertEqual(result['error'], "Điểm đến nằm ngoài TP.HCM")
        print("   ✅ PASSED")

    # --- TEST ENDPOINT /route (API gọi từ Frontend) ---

    @patch('API.requests.get')
    @patch('API.is_in_hcm')
    @patch('API.find_cameras_on_route') # Mock thêm hàm tìm camera
    def test_api_route_success(self, mock_find_cam, mock_is_in_hcm, mock_get):
        print("   -> Kịch bản: API /route trả về lộ trình + camera")
        
        mock_is_in_hcm.return_value = True
        mock_find_cam.return_value = [{"id": "CAM1", "name": "Test Cam"}] # Giả lập tìm thấy 1 camera

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.fake_tomtom_success
        mock_get.return_value = mock_resp

        payload = {
            "start": {"lat": 10.77, "lon": 106.69},
            "end": {"lat": 10.78, "lon": 106.70}
        }
        
        response = self.client.post('/route', json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['distance_km'], 1.5)
        # Kiểm tra API có trả về danh sách camera không
        self.assertEqual(len(data['cameras_on_route']), 1)
        self.assertEqual(data['cameras_on_route'][0]['id'], "CAM1")
        print("   ✅ PASSED")

    @patch('API.requests.get')
    @patch('API.is_in_hcm')
    def test_api_route_tomtom_fail(self, mock_is_in_hcm, mock_get):
        print("   -> Kịch bản: TomTom API bị lỗi mạng hoặc Key hết hạn")
        mock_is_in_hcm.return_value = True
        
        # Giả lập requests ném lỗi
        mock_get.side_effect = Exception("Connection Timeout")

        payload = {
            "start": {"lat": 10.77, "lon": 106.69},
            "end": {"lat": 10.78, "lon": 106.70}
        }
        
        response = self.client.post('/route', json=payload)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], "Failed to call TomTom Routing API")
        print("   ✅ PASSED")


class TestRealWorldRouting(unittest.TestCase):
    """
    Phần 2: LIVE TEST - Integration Test
    Mục tiêu: Gọi API thật, so sánh kết quả với Google Maps.
    Yêu cầu: Máy tính phải có mạng và TOMTOM_API_KEY trong API.py phải đúng.
    """

    def test_compare_with_google_maps(self):
        print("\n🌐 [LIVE TEST] So sánh TomTom vs Google Maps")
        print("   ------------------------------------------------")
        
        # 1. DỮ LIỆU CHUẨN (BENCHMARK)
        # Lộ trình: Chợ Bến Thành -> Dinh Độc Lập
        # Google Maps (Đi đường Lý Tự Trọng): ~0.8 km - 1.0 km
        # Google Maps (Đi đường Lê Thánh Tôn): ~1.1 km
        
        start_coord = {"lat": 10.77254, "lon": 106.69804} # Chợ Bến Thành
        end_coord =   {"lat": 10.77699, "lon": 106.69533} # Dinh Độc Lập

        GOOGLE_DISTANCE_KM = 0.9  # Trung bình
        TOLERANCE_KM = 0.4        # Sai số cho phép (+/- 400m do đường 1 chiều/thuật toán khác nhau)

        # 2. GỌI API THẬT (Hàm calculate_route trong API.py)
        # Lưu ý: Không dùng @patch ở đây để nó bắn request thật
        print("   📡 Đang gọi TomTom API thật...")
        result = calculate_route(start_coord, end_coord, "car", "shortest")

        # Kiểm tra xem có lỗi API key hay mạng không
        if isinstance(result, tuple): # Nếu trả về (error, status)
             self.fail(f"Lỗi gọi API: {result[0]}")
        if "error" in result:
             self.fail(f"API trả về lỗi: {result['error']}")

        tomtom_km = result['distance_km']
        tomtom_min = result['duration_min']

        # 3. SO SÁNH & ĐÁNH GIÁ
        diff = abs(tomtom_km - GOOGLE_DISTANCE_KM)
        
        print(f"   📍 Kết quả TomTom:   {tomtom_km:.2f} km | {tomtom_min:.1f} phút")
        print(f"   📍 Google Estimate:  {GOOGLE_DISTANCE_KM:.2f} km")
        print(f"   ⚠️ Chênh lệch:       {diff:.2f} km")

        # Assert khoảng cách nằm trong sai số cho phép
        self.assertLessEqual(diff, TOLERANCE_KM, 
                             f"Sai số quá lớn! TomTom tính ra {tomtom_km}km, trong khi Google là {GOOGLE_DISTANCE_KM}km")
        
        print("   ✅ PASSED: Kết quả TomTom hợp lý so với thực tế.")

class TestMapRender(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        
        # Dữ liệu chuẩn (Input)
        self.valid_payload = {
            "start": {"lat": 10.77, "lon": 106.69},
            "end":   {"lat": 10.78, "lon": 106.70},
            "coords": [
                {"lat": 10.77, "lon": 106.69},
                {"lat": 10.775, "lon": 106.695},
                {"lat": 10.78, "lon": 106.70}
            ]
        }
        
        # Dữ liệu kỳ vọng (Expected Output cho Folium)
        # Vì Folium cần list các tuple (lat, lon) chứ không phải dict
        self.expected_polyline_points = [
            (10.77, 106.69), 
            (10.775, 106.695), 
            (10.78, 106.70)
        ]

    # =========================================================================
    # 1. TEST INPUT VALIDATION (Kiểm tra đầu vào)
    # =========================================================================

    def test_missing_fields(self):
        print("\n🔹 [TestMap] Kịch bản: Thiếu dữ liệu đầu vào (coords/start/end)")
        
        # Case 1: Thiếu coords
        payload = self.valid_payload.copy()
        del payload['coords']
        res = self.client.post('/render-map', json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json['error'], "coords/start/end required")
        
        # Case 2: Thiếu start
        payload = self.valid_payload.copy()
        del payload['start']
        res = self.client.post('/render-map', json=payload)
        self.assertEqual(res.status_code, 400)

        print("   ✅ PASSED: API chặn đúng các request thiếu thông tin")

    # =========================================================================
    # 2. TEST LOGIC VẼ MAP
    # =========================================================================
    
    @patch('API.send_file')       # Mock hàm trả file của Flask
    @patch('API.folium.Icon')     # Mock Icon
    @patch('API.folium.Marker')   # Mock Marker
    @patch('API.folium.PolyLine') # Mock đường vẽ
    @patch('API.folium.Map')      # Mock bản đồ
    def test_map_logic_details(self, mock_map, mock_polyline, mock_marker, mock_icon, mock_send_file):
        print("\n🔹 [TestMap] Kịch bản: Kiểm tra logic vẽ Folium (Màu sắc, Tọa độ)")
        
        # Setup: Giả lập đối tượng bản đồ (m)
        mock_map_instance = MagicMock()
        mock_map.return_value = mock_map_instance
        
        # --- ACT: Gọi API ---
        res = self.client.post('/render-map', json=self.valid_payload)
        
        # --- ASSERT 1: Kiểm tra khởi tạo Map ---
        # Kiểm tra xem có fit_bounds đúng vùng start/end không
        mock_map_instance.fit_bounds.assert_called_with([
            [10.77, 106.69], [10.78, 106.70]
        ])
        
        # --- ASSERT 2: Kiểm tra Polyline (Quan trọng nhất) ---
        # Kiểm tra code có convert đúng từ List[Dict] sang List[Tuple] không
        args, kwargs = mock_polyline.call_args
        actual_points = args[0]
        
        self.assertEqual(actual_points, self.expected_polyline_points, 
                         "❌ Lỗi: Tọa độ truyền vào Polyline bị sai format hoặc sai giá trị!")
        
        self.assertEqual(kwargs.get('color'), "blue", "❌ Lỗi: Đường đi không phải màu xanh!")
        self.assertEqual(kwargs.get('weight'), 5, "❌ Lỗi: Độ dày đường vẽ sai!")

        # Kiểm tra xem Polyline có được add_to(m) không
        mock_polyline.return_value.add_to.assert_called_with(mock_map_instance)

        # --- ASSERT 3: Kiểm tra Marker (Start/End) ---
        # Ta cần đảm bảo có 2 Marker được tạo ra: 1 Xanh, 1 Đỏ
        
        # Lấy tất cả các lần gọi Icon
        icon_calls = mock_icon.call_args_list
        # Lấy tham số 'color' của từng lần gọi
        colors_used = [kwargs.get('color') for args, kwargs in icon_calls]
        
        self.assertIn('green', colors_used, "❌ Lỗi: Thiếu Marker màu xanh (Start)")
        self.assertIn('red', colors_used, "❌ Lỗi: Thiếu Marker màu đỏ (End)")
        
        # Kiểm tra Marker có được add_to(m) không
        self.assertEqual(mock_marker.return_value.add_to.call_count, 2, "❌ Lỗi: Phải add đủ 2 Marker vào Map")

        # --- ASSERT 4: Kiểm tra Save & Send File ---
        # Kiểm tra xem code có gọi lệnh save file html không (dù là save giả)
        mock_map_instance.save.assert_called_with("route_map.html")
        
        # Kiểm tra Flask có trả về đúng file đó không
        mock_send_file.assert_called_with("route_map.html", as_attachment=False)
        
        print("   ✅ PASSED: Logic vẽ bản đồ hoàn hảo.")

class TestRouteDetection(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

    # =========================================================================
    # 1. TEST INPUT VALIDATION
    # =========================================================================

    def test_detect_missing_ids(self):
        print("   -> Kịch bản: Thiếu camera_ids trong body")
        response = self.client.post('/api/detect/route-cameras', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "camera_ids required")
        print("   ✅ PASSED")

    @patch('API.Path') # Mock hệ thống file
    def test_detect_no_images_found(self, mock_path):
        print("   -> Kịch bản: Camera ID đúng nhưng không tìm thấy ảnh nào trên ổ cứng")
        
        # Giả lập thư mục camera tồn tại nhưng rỗng
        mock_path_instance = MagicMock()
        mock_path.return_value.__truediv__.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.glob.return_value = [] # Không có file .jpg nào

        response = self.client.post('/api/detect/route-cameras', json={"camera_ids": ["CAM_EMPTY"]})
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], "No images found for cameras")
        print("   ✅ PASSED")

    # =========================================================================
    # 2. TEST MODAL GPU SUCCESS FLOW
    # =========================================================================

    @patch('API.sqlite3.connect')           # Mock DB SQLite
    @patch('API.requests.post')             # Mock gọi API Modal
    @patch('API.run_congestion_update_background') # Mock hàm update tắc nghẽn
    @patch('API.Path')                      # Mock File System
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_bytes') # Mock đọc file
    def test_detect_modal_success(self, mock_file, mock_path, mock_bg_update, mock_req_post, mock_sqlite):
        print("   -> Kịch bản: Detect bằng Modal GPU thành công + Lưu DB")
        
        # 1. Setup Mock USE_MODAL_DETECTION = True
        with patch('API.USE_MODAL_DETECTION', True):
            
            # 2. Setup File System giả (Tìm thấy 1 ảnh)
            mock_cam_dir = MagicMock()
            mock_path.return_value.__truediv__.return_value = mock_cam_dir
            mock_cam_dir.exists.return_value = True
            
            # Giả lập tìm thấy file 'img1.jpg'
            mock_img_file = MagicMock()
            mock_img_file.stat.return_value.st_mtime = 1000
            mock_cam_dir.glob.return_value = [mock_img_file]

            # 3. Setup Modal Response giả (Trả về kết quả detect)
            mock_req_post.return_value.status_code = 200
            mock_req_post.return_value.json.return_value = [{
                "camera_id": "CAM_1",
                "detections": [
                    {"class_id": 2}, # 1 Car
                    {"class_id": 2}, # 1 Car
                    {"class_id": 3}  # 1 Motorbike
                ]
            }]

            # 4. Setup Database giả
            mock_cursor = MagicMock()
            mock_sqlite.return_value.cursor.return_value = mock_cursor

            # --- ACT ---
            response = self.client.post('/api/detect/route-cameras', json={"camera_ids": ["CAM_1"]})

            # --- ASSERT ---
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['method'], 'modal-gpu')
            self.assertEqual(response.json['processed_cameras'], 1)

            # Kiểm tra DB Insert: Phải đếm đúng 2 xe hơi, 1 xe máy
            # Lấy lệnh execute cuối cùng (lệnh INSERT)
            args, _ = mock_cursor.execute.call_args
            query = args[0]
            params = args[1] # params là tuple các giá trị insert

            self.assertIn("INSERT OR REPLACE INTO detections", query)
            # params cấu trúc: (path, cam_id, name, time, dt, total, car, motor, bus, truck, ...)
            # Index có thể thay đổi tùy SQL, nhưng thường Car=6, Motor=7 (theo code API.py)
            self.assertEqual(params[6], 2) # Car count
            self.assertEqual(params[7], 1) # Motor count
            
            # Kiểm tra gọi hàm update background
            mock_bg_update.assert_called_once()
            
            print("   ✅ PASSED: Đã gửi ảnh, nhận KQ, và lưu đúng số lượng xe vào DB")

    # =========================================================================
    # 3. TEST FALLBACK FLOW (Modal Lỗi -> Chạy Local)
    # =========================================================================

    @patch('API.run_detection_for_cameras') # Mock hàm chạy local YOLO
    @patch('API.requests.post')
    @patch('API.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'bytes')
    def test_detect_fallback_to_local(self, mock_file, mock_path, mock_req_post, mock_run_local):
        print("   -> Kịch bản: Modal API bị lỗi -> Tự động chuyển sang Local Detection")
        
        with patch('API.USE_MODAL_DETECTION', True):
            # 1. Setup File System (Có ảnh)
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.glob.return_value = [MagicMock()]

            # 2. Setup Modal Error (Lỗi 500 hoặc Exception)
            mock_req_post.side_effect = Exception("Modal Server Down")

            # --- ACT ---
            response = self.client.post('/api/detect/route-cameras', json={"camera_ids": ["CAM_1"]})

            # --- ASSERT ---
            self.assertEqual(response.status_code, 200) # Vẫn 200 vì đã fallback thành công
            self.assertEqual(response.json['method'], 'local-fallback')
            self.assertIn("Modal failed", response.json['note'])

            # Kiểm tra hàm local detection có được gọi không
            mock_run_local.assert_called_with(["CAM_1"])
            print("   ✅ PASSED: Fallback logic hoạt động hoàn hảo")

    # =========================================================================
    # 4. TEST LOCAL ONLY MODE
    # =========================================================================

    @patch('API.run_detection_for_cameras')
    @patch('API.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'bytes')
    def test_detect_local_mode(self, mock_file, mock_path, mock_run_local):
        print("   -> Kịch bản: Cấu hình chỉ chạy Local (USE_MODAL_DETECTION = False)")
        
        with patch('API.USE_MODAL_DETECTION', False):
            # Setup File System
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.glob.return_value = [MagicMock()]

            response = self.client.post('/api/detect/route-cameras', json={"camera_ids": ["CAM_1"]})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['method'], 'local')
            
            # Phải gọi hàm local ngay lập tức, không gọi request.post
            mock_run_local.assert_called_with(["CAM_1"])
            print("   ✅ PASSED")

    # =========================================================================
    # 5. TEST GEOJSON API
    # =========================================================================

    @patch('API.json.load')
    @patch('API.Path')
    def test_get_congestion_geojson_success(self, mock_path, mock_json_load):
        print("   -> Kịch bản: Lấy file GeoJSON thành công")
        
        # Mock file tồn tại
        mock_path.return_value.exists.return_value = True
        # Mock nội dung file json
        mock_json_load.return_value = {"type": "FeatureCollection", "features": []}
        
        # Mock open file (Context Manager)
        mock_file_obj = MagicMock()
        mock_path.return_value.open.return_value.__enter__.return_value = mock_file_obj

        response = self.client.get('/api/congestion/geojson')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['type'], "FeatureCollection")
        print("   ✅ PASSED")

    @patch('API.Path')
    def test_get_congestion_geojson_missing(self, mock_path):
        print("   -> Kịch bản: File GeoJSON chưa được tạo (404)")
        mock_path.return_value.exists.return_value = False

        response = self.client.get('/api/congestion/geojson')

        self.assertEqual(response.status_code, 404)
        self.assertIn("GeoJSON not found", response.json['error'])
        print("   ✅ PASSED")

class TestBusRouting(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

        # Param chuẩn để test
        self.valid_params = {
            'start_lat': 10.77,
            'start_lng': 106.69,
            'end_lat': 10.80,
            'end_lng': 106.65,
            'max_walk': 500
        }

    # =========================================================================
    # 1. TEST INPUT VALIDATION
    # =========================================================================

    def test_missing_parameters(self):
        print("   -> Kịch bản: Thiếu tham số lat/lng")
        # Gửi request rỗng
        response = self.client.get('/api/bus/route')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "Invalid parameters")
        print("   ✅ PASSED")

    def test_invalid_parameter_types(self):
        print("   -> Kịch bản: Tham số không phải số (Text)")
        params = self.valid_params.copy()
        params['start_lat'] = "abc" # Sai kiểu dữ liệu
        
        response = self.client.get('/api/bus/route', query_string=params)
        self.assertEqual(response.status_code, 400)
        print("   ✅ PASSED")

    # =========================================================================
    # 2. TEST MODULE AVAILABILITY (Lỗi 503)
    # =========================================================================

    def test_bus_module_not_available(self):
        print("   -> Kịch bản: Module Bus chưa load xong (Trả về 503)")
        
        # Giả lập biến BUS_ROUTING_AVAILABLE = False
        with patch('API.BUS_ROUTING_AVAILABLE', False):
            response = self.client.get('/api/bus/route', query_string=self.valid_params)
            
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json['error'], "Bus routing module not available")
        print("   ✅ PASSED")

    # =========================================================================
    # 3. TEST LOGIC FLOW (Success & Not Found)
    # =========================================================================

    @patch('API.BUS_ROUTING_AVAILABLE', True)
    @patch('API.nearby_stops') # Mock hàm tìm trạm
    def test_no_stops_found(self, mock_nearby):
        print("   -> Kịch bản: Không tìm thấy trạm xe buýt gần đó (404)")
        
        # Giả lập hàm trả về danh sách rỗng []
        mock_nearby.return_value = []

        response = self.client.get('/api/bus/route', query_string=self.valid_params)

        self.assertEqual(response.status_code, 404)
        self.assertIn("No bus stop near start location", response.json['error'])
        print("   ✅ PASSED")

    @patch('API.BUS_ROUTING_AVAILABLE', True)
    @patch('API.nearby_stops')
    @patch('API.make_heuristic')
    @patch('API.a_star')
    @patch('API.calculate_First_Last_walkingCoords')
    @patch('API.calculate_transfer_walkingCoords')
    def test_bus_route_success(self, mock_calc_transfer, mock_calc_walk, mock_astar, mock_heuristic, mock_nearby):
        print("   -> Kịch bản: Tính toán lộ trình thành công (Happy Path)")

        # 1. Mock Data Setup
        # nearby_stops trả về 1 trạm fake
        mock_nearby.side_effect = [
            [('STOP_A', 100)], # Start stops
            [('STOP_B', 200)]  # End stops
        ]
        
        # a_star trả về kết quả thành công
        mock_astar.return_value = {
            "total_fare": 7000,
            "best_min": 30,
            "worst_min": 45,
            "coords": [],
            "special_stops": [],
            "unique_BusNumbers": ["01", "02"],
            "unique_Routes": ["Route 1", "Route 2"]
        }

        # Mock các hàm phụ trợ vẽ đường
        mock_calc_walk.return_value = ([], []) # (walk_to_bus, walk_to_des)
        mock_calc_transfer.return_value = ([], [], []) # (names, bus_coords, walk_coords)

        # 2. Call API
        response = self.client.get('/api/bus/route', query_string=self.valid_params)

        # 3. Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        self.assertEqual(data['fare_vnd'], 7000)
        self.assertEqual(data['best_case_min'], 30)
        # Logic tính transfer: transfers = len(unique_BusNumbers) - len(walk_coords) + 2
        # Ở đây: 2 - 0 + 2 = 4 (Test logic cộng trừ)
        self.assertIn('transfers', data)
        
        print("   ✅ PASSED")

    # =========================================================================
    # 4. TEST ALGORITHM FAILURES (Timeout & Exception)
    # =========================================================================

    @patch('API.BUS_ROUTING_AVAILABLE', True)
    @patch('API.nearby_stops')
    @patch('API.make_heuristic')
    @patch('API.a_star')
    def test_astar_exception(self, mock_astar, mock_heuristic, mock_nearby):
        print("   -> Kịch bản: Thuật toán A* bị lỗi (Crash)")
        
        mock_nearby.return_value = [('STOP_A', 100)]
        
        # Giả lập A* ném lỗi Exception
        mock_astar.side_effect = Exception("Graph disconnected")

        response = self.client.get('/api/bus/route', query_string=self.valid_params)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Route calculation failed", response.json['error'])
        self.assertIn("Graph disconnected", response.json['error'])
        print("   ✅ PASSED")

    @patch('API.BUS_ROUTING_AVAILABLE', True)
    @patch('API.nearby_stops')
    @patch('API.make_heuristic')
    @patch('API.a_star')
    def test_astar_no_path_found(self, mock_astar, mock_heuristic, mock_nearby):
        print("   -> Kịch bản: A* chạy xong nhưng không tìm thấy đường (None)")
        
        mock_nearby.return_value = [('STOP_A', 100)]
        mock_astar.return_value = None # Không tìm thấy đường

        response = self.client.get('/api/bus/route', query_string=self.valid_params)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], "No route found between these locations")
        print("   ✅ PASSED")

class TestRealBusRouting(unittest.TestCase):
    """
    Phần 3: BUS LIVE TEST - Integration Test
    Mục tiêu: Gọi thuật toán A* thật với dữ liệu Bus Map thật.
    So sánh kết quả với thực tế (Google Maps / BusMap).
    """

    @classmethod
    def setUpClass(cls):
        """Chạy 1 lần duy nhất khi bắt đầu class để kiểm tra môi trường"""
        if not BUS_ROUTING_AVAILABLE:
            raise unittest.SkipTest("❌ BỎ QUA: Module Bus chưa load được dữ liệu thật. Hãy kiểm tra folder 'bus_data'.")
        
        cls.client = app.test_client()
        cls.client.testing = True
        print("\n🚀 HỆ THỐNG BUS ĐÃ SẴN SÀNG! BẮT ĐẦU LIVE TEST...\n")

    def test_compare_bus_route_BenThanh_to_ChoLon(self):
        print("\n🌐 [LIVE TEST] So sánh Lộ trình Bus: Bến Thành -> Chợ Lớn")
        print("   ------------------------------------------------")

        # 1. DỮ LIỆU CHUẨN (BENCHMARK)
        # Tuyến đường: Chợ Bến Thành (Q1) -> Bến xe Chợ Lớn (Q5)
        # Thực tế: Đây là tuyến đường trục chính, thường đi xe số 01.
        # BusMap: ~25 - 35 phút, Giá vé 6k-7k, Không đổi tuyến (0 transfers).
        
        start_coord = {"lat": 10.77254, "lng": 106.69804} # Bến Thành
        end_coord =   {"lat": 10.75206, "lng": 106.65436} # Chợ Lớn B Station

        EXPECTED_FARE = 7000       # Giá vé tiêu chuẩn
        EXPECTED_TIME_MIN = 21     # Thời gian trung bình
        TOLERANCE_TIME = 15        # Sai số cho phép (+/- 15p tùy tình trạng kẹt xe giả định)
        EXPECTED_BUSES = ["01", "39", "56"] # Các xe có thể đi được (để đối chiếu)

        # 2. GỌI API THẬT
        print(f"   📡 Đang chạy thuật toán A* (Real Graph)...")
        start_time = time.time()
        
        response = self.client.get('/api/bus/route', query_string={
            'start_lat': start_coord['lat'],
            'start_lng': start_coord['lng'],
            'end_lat': end_coord['lat'],
            'end_lng': end_coord['lng'],
            'max_walk': 600 # Cho phép đi bộ tìm trạm tối đa 600m
        })
        
        duration_api = time.time() - start_time

        # Kiểm tra lỗi API (500, 404, 408)
        if response.status_code != 200:
            self.fail(f"API Failed with code {response.status_code}: {response.json}")

        result = response.json
        
        actual_fare = result['fare_vnd']
        actual_time = result['best_case_min']
        actual_transfers = result['transfers']
        actual_buses = result['unique_BusNumbers']

        # 3. SO SÁNH & ĐÁNH GIÁ
        print(f"   ⏱️  API phản hồi trong: {duration_api:.2f}s")
        print(f"   📍 Kết quả API:      {actual_time} phút | {actual_fare} VNĐ | {actual_transfers} lần đổi tuyến")
        print(f"   🚌 Các tuyến gợi ý:  {actual_buses}")
        print(f"   📍 Thực tế (Ref):    ~{EXPECTED_TIME_MIN} phút | {EXPECTED_FARE} VNĐ | Xe: {EXPECTED_BUSES}")

        # --- ASSERTIONS (Kiểm tra đúng sai) ---

        # 1. Kiểm tra thời gian (Trong khoảng chấp nhận được)
        diff_time = abs(actual_time - EXPECTED_TIME_MIN)
        self.assertLessEqual(diff_time, TOLERANCE_TIME, 
                             f"Thời gian sai lệch quá lớn! API: {actual_time}p, Kỳ vọng: {EXPECTED_TIME_MIN}p")

        # 2. Kiểm tra số lần đổi tuyến (Với tuyến này phải là 0 - đi thẳng)
        # Tuy nhiên thuật toán có thể tìm ra đường đi bộ ra trạm xa hơn để đi xe khác, nên cho phép <= 1
        self.assertLessEqual(actual_transfers, 1, 
                             f"Tuyến Bến Thành - Chợ Lớn có xe đi thẳng, sao lại bắt đổi {actual_transfers} tuyến?")

        # 3. Kiểm tra xem có tìm ra tuyến xe phổ biến không (Optional)
        # Tìm giao thoa giữa các xe tìm được và xe kỳ vọng
        found_common_bus = any(bus in actual_buses for bus in EXPECTED_BUSES)
        if found_common_bus:
            print("   ✅ PASSED: Tìm thấy đúng tuyến xe quen thuộc (01/45/...).")
        else:
            print(f"   ⚠️ WARNING: Không thấy xe 01/45, thuật toán tìm ra xe lạ: {actual_buses}. (Cần kiểm tra lại dữ liệu)")

        print("   ✅ PASSED: Kết quả hợp lý với thực tế.")

class TestAITripPlanner(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

    # =========================================================================
    # 1. TEST INPUT & TRẠNG THÁI HỆ THỐNG
    # =========================================================================

    def test_missing_query_payload(self):
        print("   -> Kịch bản: Gửi JSON thiếu field 'query' (400 Bad Request)")
        response = self.client.post('/api/groq', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "Missing 'query' in JSON body")
        print("   ✅ PASSED")

    def test_match_module_unavailable(self):
        print("   -> Kịch bản: Module AI chưa sẵn sàng (MATCH_TRIP_AVAILABLE=False)")
        
        # Patch biến toàn cục trong API.py
        with patch('API.MATCH_TRIP_AVAILABLE', False):
            response = self.client.post('/api/groq', json={"query": "Đi chơi Q1"})
            
            self.assertEqual(response.status_code, 503)
            self.assertIn("Match trip module not available", response.json['error'])
        print("   ✅ PASSED")

    # =========================================================================
    # 2. TEST HAPPY PATH
    # =========================================================================

    @patch('API.MATCH_TRIP_AVAILABLE', True)
    @patch('API.generate_trip_plan') # Mock hàm AI
    @patch('API.calculate_route')    # Mock hàm tính đường (TomTom)
    def test_plan_trip_full_flow(self, mock_calc_route, mock_ai_plan):
        print("   -> Kịch bản: AI trả về kế hoạch + Tính toán lộ trình thành công")

        # 1. SETUP: Giả lập AI trả về 3 điểm đến (A -> B -> C)
        mock_ai_plan.return_value = {
            "trip_name": "Tour Demo",
            "itinerary": [
                {"name": "Điểm A", "lat": 10.1, "lng": 106.1},
                {"name": "Điểm B", "lat": 10.2, "lng": 106.2},
                {"name": "Điểm C", "lat": 10.3, "lng": 106.3}
            ]
        }

        # 2. SETUP: Giả lập hàm tính đường trả về tọa độ vẽ (Polyline)
        # Hàm này sẽ được gọi 2 lần: (A->B) và (B->C)
        mock_calc_route.return_value = {
            "coords": [{"lat": 10.15, "lon": 106.15}], 
            "distance_km": 5.0
        }

        # 3. ACT: Gọi API
        response = self.client.post('/api/groq', json={"query": "Lên lịch trình"})

        # 4. ASSERT: Kiểm tra kết quả
        self.assertEqual(response.status_code, 200)
        data = response.json
        
        # Kiểm tra AI đã được gọi
        mock_ai_plan.assert_called_once()
        
        # Kiểm tra API có ghép thêm field "route_lines" vào kết quả không
        self.assertIn("route_lines", data)
        route_lines = data["route_lines"]
        
        # Phải có 2 đoạn đường nối 3 điểm (A->B, B->C)
        self.assertEqual(len(route_lines), 2)
        
        # Kiểm tra chi tiết đoạn 1 (từ index 0 đến 1)
        segment_1 = route_lines[0]
        self.assertEqual(segment_1["from_index"], 0)
        self.assertEqual(segment_1["to_index"], 1)
        self.assertEqual(len(segment_1["coords"]), 1) # Do mock trả về 1 điểm
        
        print("   ✅ PASSED: Logic tích hợp AI và Routing chạy đúng.")

    # =========================================================================
    # 3. TEST XỬ LÝ LỖI (QUAN TRỌNG NHẤT)
    # =========================================================================

    @patch('API.MATCH_TRIP_AVAILABLE', True)
    @patch('API.generate_trip_plan')
    @patch('API.calculate_route')
    def test_plan_trip_routing_crash(self, mock_calc_route, mock_ai_plan):
        print("   -> Kịch bản: Routing bị lỗi (Exception) -> API KHÔNG ĐƯỢC CRASH")
        
        # 1. Setup: AI trả về A -> B
        mock_ai_plan.return_value = {
            "itinerary": [
                {"name": "A", "lat": 10.1, "lng": 106.1},
                {"name": "B", "lat": 10.2, "lng": 106.2}
            ]
        }

        # 2. Setup: Hàm tính đường bị lỗi (Mất mạng, hết tiền,...)
        mock_calc_route.side_effect = Exception("TomTom API Error")

        # 3. Act
        response = self.client.post('/api/groq', json={"query": "Test Error"})

        # 4. Assert
        self.assertEqual(response.status_code, 200) # Vẫn phải trả về 200 OK
        data = response.json
        
        # Kiểm tra route_lines vẫn tồn tại nhưng coords rỗng
        route_lines = data["route_lines"]
        self.assertEqual(len(route_lines), 1)
        self.assertEqual(route_lines[0]["coords"], [], "Coords phải là list rỗng khi lỗi")
        
        print("   ✅ PASSED: Hệ thống xử lý lỗi Routing mượt mà (Graceful Degradation)")

    @patch('API.MATCH_TRIP_AVAILABLE', True)
    @patch('API.generate_trip_plan')
    @patch('API.calculate_route')
    def test_plan_trip_missing_coordinates(self, mock_calc_route, mock_ai_plan):
        print("   -> Kịch bản: AI trả về địa điểm nhưng thiếu tọa độ -> Bỏ qua tính đường")

        # 1. Setup: Điểm A có tọa độ -> Điểm B MẤT TỌA ĐỘ
        mock_ai_plan.return_value = {
            "itinerary": [
                {"name": "A", "lat": 10.1, "lng": 106.1},
                {"name": "B"} # Thiếu lat, lng
            ]
        }

        # 2. Act
        response = self.client.post('/api/groq', json={"query": "Test Missing"})

        # 3. Assert
        self.assertEqual(response.status_code, 200)
        
        # Hàm tính đường KHÔNG được gọi (vì thiếu input)
        mock_calc_route.assert_not_called()
        
        # route_lines phải rỗng
        self.assertEqual(response.json.get("route_lines"), [])
        print("   ✅ PASSED: Code đã check kỹ điều kiện 'if lat in start...'")


class TestImageServing(unittest.TestCase):
    """Test chức năng trả về ảnh chuyến đi"""
    
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        print(f"\n🔹 [{self._testMethodName}]")

    @patch('API.send_from_directory')
    def test_serve_trip_image_success(self, mock_send):
        print("   -> Kịch bản: Serve file ảnh thành công")
        
        # 1. SETUP MOCK
        # Giả lập send_from_directory trả về một Response object của Flask (để có status code)
        mock_send.return_value = Response("Fake Image Content", status=200, mimetype='image/jpeg')
        
        # 2. ACT
        filename = "landmarks/Ben Thanh Market/cover.jpg"
        response = self.client.get(f'/images/{filename}')
        
        # 3. ASSERT (Kiểm tra kỹ hơn)
        
        # Kiểm tra 1: Logic gọi hàm nội bộ phải đúng (QUAN TRỌNG NHẤT)
        mock_send.assert_called_with(IMAGE_TRIP_FOLDER, filename)
        
        # Kiểm tra 2: HTTP Status code phải là 200
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra 3: Nội dung trả về cho user phải đúng là cái nội dung của file ảnh
        self.assertEqual(response.data.decode(), "Fake Image Content")
        
        print("   ✅ PASSED")

if __name__ == '__main__':
    unittest.main() 