// Simple API helper to centralize backend calls and make it easy to replace endpoints.
import { handleTokenExpiration } from './utils/tokenManager';

// export const BASE_URL = "https://api.hcmus.fit";
export const BASE_URL = "http://localhost:5000";

export function getAuthHeader() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Helper function to handle API responses and auto-logout on 401
async function handleResponse(response) {
  if (response.status === 401) {
    // Token expired or invalid
    handleTokenExpiration();
    throw new Error('Session expired. Please login again.');
  }
  return response;
}
// ============================
//  Camera API
// ============================
export async function fetchCameraImages(cameraId) {
  try {
    const response = await fetch(`${BASE_URL}/api/camera/${cameraId}/images`);

    if (!response.ok) {
      throw new Error("Failed to load images");
    }

    const data = await response.json();

    if (data.images && data.images.length > 0) {
      // Convert to full URLs
      return data.images.map(img => `${BASE_URL}${img.url}`);
    }

    return [];
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// ============================
//  AUTH API
// ============================
export async function login(username, password) {
  const resp = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.message || "Login failed");
  return data;
}

export async function register(username, password) {
  const resp = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.message || "Registration failed");
  return data;
}

// ============================
// 💾 USER DATA API
// ============================
export async function getSavedLocations() {
  const resp = await fetch(`${BASE_URL}/api/user/locations`, {
    headers: { ...getAuthHeader() }
  });
  await handleResponse(resp);
  if (!resp.ok) return [];
  return resp.json();
}

export async function saveLocation(name, lat, lng) {
  const resp = await fetch(`${BASE_URL}/api/user/locations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify({ name, lat, lng }),
  });
  await handleResponse(resp);
  return resp.ok;
}

export async function getSavedRoutes() {
  const resp = await fetch(`${BASE_URL}/api/user/routes`, {
    headers: { ...getAuthHeader() }
  });
  await handleResponse(resp);
  if (!resp.ok) return [];
  return resp.json();
}

export async function saveRoute(startName, startLat, startLng, endName, endLat, endLng) {
  const resp = await fetch(`${BASE_URL}/api/user/routes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify({
      start_name: startName, start_lat: startLat, start_lng: startLng,
      end_name: endName, end_lat: endLat, end_lng: endLng
    }),
  });
  await handleResponse(resp);
  return resp.ok;
}
export async function saveTrip(tripData) {
  const resp = await fetch(`${BASE_URL}/api/user/trips`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify(tripData),
  });
  await handleResponse(resp);
  return resp.ok;
}
export async function getSavesTrips() {
  const resp = await fetch(`${BASE_URL}/api/user/trips`, {
    method: "GET",
    headers: { ...getAuthHeader() }
  });
  await handleResponse(resp);
  if (!resp.ok) return [];
  return resp.json();
}

export async function deleteTrip(trip_id) {
  const resp = await fetch(`${BASE_URL}/api/user/trips/${trip_id}`, {
    method: "DELETE",
    headers: {
      ...getAuthHeader()
    },
  });
  await handleResponse(resp);
  return resp.ok;
}
// ============================
// 🗺 TOMTOM API
// ============================
export async function searchLocation(address, lat = null, lon = null) {
  const resp = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address, lat, lon }),
  });
  if (!resp.ok) throw new Error("Search failed");
  return resp.json();
}

export async function calculateRoute(start, end, travelMode = "car", routeType = "fastest") {
  const resp = await fetch(`${BASE_URL}/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start, end, travelMode, routeType }),
  });
  if (!resp.ok) throw new Error("Route calculation failed");
  return resp.json();
}


// ============================
// ROUTE CAMERA DETECTION API
// ============================

export async function detectRouteCameras(cameraIds) {
  const resp = await fetch(`${BASE_URL}/api/detect/route-cameras`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ camera_ids: cameraIds }),
  });

  // This handles 401 / token expiration
  await handleResponse(resp);

  let data = {};
  try {
    data = await resp.json();
  } catch (e) {
  }

  if (!resp.ok) {
    throw new Error(data.error || "Route camera detection failed");
  }

  return data;
}

// ============================
// CONGESTION GEOJSON API
// ============================

export async function getCongestionGeoJSON() {
  const resp = await fetch(`${BASE_URL}/api/congestion/geojson`);
  if (!resp.ok) {
    console.error("Failed to load congestion geojson");
    return null;
  }
  return resp.json();
}



// ============================
// 🚨 SOS API
// ============================

// Gửi báo cáo SOS (có hình ảnh)
export async function reportSOS(lat, lng, description, imageFile) {
  const formData = new FormData();
  formData.append('lat', lat);
  formData.append('lng', lng);
  formData.append('description', description);

  if (imageFile) {
    formData.append('image', imageFile);
  }

  const token = localStorage.getItem('token'); // Lấy token thủ công vì FormData xử lý header khác JSON

  const resp = await fetch(`${BASE_URL}/api/sos`, {
    method: "POST",
    headers: {
      'Authorization': `Bearer ${token}`
      // Không set Content-Type là application/json vì đây là FormData
    },
    body: formData,
  });

  await handleResponse(resp);

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.message || "Failed to report SOS");
  }
  return resp.json();
}

// Lấy danh sách SOS để vẽ lên bản đồ
export async function getSOSAlerts() {
  const resp = await fetch(`${BASE_URL}/api/sos`, {
    method: "GET"
  });

  if (!resp.ok) return [];
  return resp.json();
}

export async function resolveSOS(sosId) {
  const resp = await fetch(`${BASE_URL}/api/sos/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify({ sos_id: sosId }),
  });

  await handleResponse(resp);

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.message || "Lỗi khi cập nhật trạng thái");
  }
  return resp.json();
}

export async function getComments(sosId) {
  const resp = await fetch(`${BASE_URL}/api/sos/comments/${sosId}`);
  if (!resp.ok) return [];
  return resp.json();
}

// Gửi comment
export async function sendComment(sosId, content) {
  const resp = await fetch(`${BASE_URL}/api/sos/comment`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ sos_id: sosId, content }),
  });
  if (!resp.ok) throw new Error("Gửi bình luận thất bại");
  return resp.json();
}

// Báo cáo bài viết
export async function reportSOSPost(sosId, reason) {
  const resp = await fetch(`${BASE_URL}/api/sos/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ sos_id: sosId, reason: reason }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.message || "Lỗi báo cáo");
  return data;
}
export async function calculateBusRoute(origin, destination, maxWalk = 300) {
  const response = await fetch(
    `${BASE_URL}/api/bus/route?start_lat=${origin.lat}&start_lng=${origin.lon}&end_lat=${destination.lat}&end_lng=${destination.lon}&max_walk=${maxWalk}`
  );

  if (!response.ok) {
    throw new Error("Bus route calculation failed");
  }

  return response.json();
}
export async function getAITripPlan(user_query) {
  try {
    const response = await fetch(`${BASE_URL}/api/groq`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ query: user_query })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    return await response.json();

  } catch (err) {
    console.error("❌ Error fetching trip plan:", err);
    return null;
  }
}