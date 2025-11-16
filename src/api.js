// Simple API helper to centralize backend calls and make it easy to replace endpoints.
export async function nominatimSearch(q) {
  const BASE = "https://nominatim.openstreetmap.org/search?";
  const params = { q, format: "json", addressdetails: 1, polygon_geojson: 0 };
  const query = new URLSearchParams(params).toString();
  const resp = await fetch(`${BASE}${query}`, { method: "GET", redirect: "follow" });
  if (!resp.ok) throw new Error(`Nominatim error ${resp.status}`);
  return resp.json();
}

// Placeholder for backend routing/recommender endpoints. Replace `BASE_URL` with your API.
const BASE_URL = "";
export async function getItineraries(payload) {
  if (!BASE_URL) {
    // In absence of backend, return null to let UI use mock data.
    return null;
  }
  const resp = await fetch(`${BASE_URL}/itineraries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(`Itineraries error ${resp.status}`);
  return resp.json();
}

export async function getRecommendations(payload) {
  if (!BASE_URL) return null;
  const resp = await fetch(`${BASE_URL}/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(`Recommendations error ${resp.status}`);
  return resp.json();
}
