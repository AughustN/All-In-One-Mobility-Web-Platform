// Simple API helper to centralize backend calls and make it easy to replace endpoints.
const BASE_URL = "https://api.hcmus.fit";

export function getAuthHeader() {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
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
  return resp.ok;
}

export async function getSavedRoutes() {
  const resp = await fetch(`${BASE_URL}/api/user/routes`, {
    headers: { ...getAuthHeader() }
  });
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

export async function calculateRoute(start, end, travelMode = "car") {
  const resp = await fetch(`${BASE_URL}/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start, end, travelMode }),
  });
  if (!resp.ok) throw new Error("Route calculation failed");
  return resp.json();
}
