import React, { useEffect } from "react";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  Polyline,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const icon = L.icon({
  iconUrl: "./placeholder.png",
  iconSize: [38, 38],
});

const startIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const endIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function Maps({ origin, destination, coords }) {
  const Recenter = ({ origin, destination, coords }) => {
    const map = useMap();
    
    useEffect(() => {
      if (coords && coords.length > 0) {
        // Fit bounds to show entire route
        const bounds = coords.map(c => [c.lat, c.lon]);
        map.fitBounds(bounds, { padding: [50, 50] });
      } else if (origin && destination) {
        // Fit bounds to show both markers
        map.fitBounds([
          [origin.lat, origin.lon],
          [destination.lat, destination.lon]
        ], { padding: [50, 50] });
      } else if (origin) {
        map.setView([origin.lat, origin.lon], 14);
      } else if (destination) {
        map.setView([destination.lat, destination.lon], 14);
      }
    }, [origin, destination, coords, map]);
    
    return null;
  };

  return (
    <MapContainer
      center={[10.8231, 106.6297]} // default: HCM
      zoom={12}
      style={{ width: "100%", height: "100%" }}
    >
      <TileLayer 
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />

      {/* Marker điểm bắt đầu */}
      {origin && (
        <Marker position={[origin.lat, origin.lon]} icon={startIcon}>
          <Popup>
            <strong>Điểm bắt đầu</strong>
            <br />
            {origin.name || "Vị trí xuất phát"}
          </Popup>
        </Marker>
      )}

      {/* Marker điểm đến */}
      {destination && (
        <Marker position={[destination.lat, destination.lon]} icon={endIcon}>
          <Popup>
            <strong>Điểm đến</strong>
            <br />
            {destination.name || "Đích đến"}
          </Popup>
        </Marker>
      )}

      {/* Vẽ đường đi từ backend */}
      {coords && coords.length > 0 && (
        <Polyline 
          positions={coords.map(c => [c.lat, c.lon])} 
          color="#0277BD"
          weight={5}
          opacity={0.7}
        />
      )}

      <Recenter origin={origin} destination={destination} coords={coords} />
    </MapContainer>
  );
}