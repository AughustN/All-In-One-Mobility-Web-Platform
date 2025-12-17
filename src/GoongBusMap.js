import React, { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';
import { useMapContext } from './contexts/MapContext';
const GOONG_MAPTILES_KEY = process.env.REACT_APP_GOONG_MAPTILES_KEY;

goongjs.accessToken = GOONG_MAPTILES_KEY;

// COLOR PALETTE FOR BUS ROUTES
export const colorPalette = [
  "#e41a1c",
  "#377eb8",
  "#4daf4a",
  "#984ea3",
  "#ff7f00",
  "#ffff33",
  "#a65628",
  "#f781bf",
  "#999999",
];



export default function GoongBusMap({
  origin,
  destination,
  walk_coords,
  bus_coords,
  style = "goong_map_web",
  userLocation
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const routeLayers = useRef([]); // store all route layer names
  const [mapLoaded, setMapLoaded] = useState(false);
  const startMarker = useRef(null);
  const endMarker = useRef(null)
  const mapContext = useMapContext();
  const registerMap = mapContext?.registerMap || (() => { });

  // ---------- 1. Initialize Map ----------
  useEffect(() => {
    if (map.current) return;

    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: `https://tiles.goong.io/assets/${style}.json`,
      center: [106.6297, 10.8231], // HCM City
      zoom: 12
    });

    map.current.addControl(new goongjs.NavigationControl(), 'top-right');
    map.current.addControl(new goongjs.ScaleControl({
      maxWidth: 100,
      unit: 'metric'
    }), 'bottom-left');

    map.current.on("load", () => {
      setMapLoaded(true);
      registerMap(map.current);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [style]);

  // Handle user location
  useEffect(() => {
    if (!mapLoaded || !map.current || !userLocation) return;

    // Remove old user marker
    if (startMarker.current) {
      startMarker.current.remove();
    }

    // Add marker with default style (blue color for user location)
    const marker = new goongjs.Marker({ color: '#4285F4' })
      .setLngLat([userLocation.lon, userLocation.lat])
      .setPopup(
        new goongjs.Popup({ offset: 25 }).setHTML(
          '<div style="padding: 8px;"><strong>Vị trí của bạn</strong></div>'
        )
      )
      .addTo(map.current);

    startMarker.current = marker;

    // Fly to user location
    map.current.flyTo({
      center: [userLocation.lon, userLocation.lat],
      zoom: 15,
      duration: 1500
    });

  }, [mapLoaded, userLocation]);

  // origin Marker
  useEffect(() => {
    if (!mapLoaded || !map.current || !origin) return;

    // Remove old marker
    if (startMarker.current) {
      startMarker.current.remove();
    }

    // Add new marker
    startMarker.current = new goongjs.Marker({ color: '#4CAF50' })
      .setLngLat([origin.lon, origin.lat])
      .setPopup(
        new goongjs.Popup().setHTML(
          `<strong>Điểm bắt đầu</strong><br/>${origin.name || 'Vị trí xuất phát'}`
        )
      )
      .addTo(map.current);

  }, [mapLoaded, origin]);

  // Des marker 
  useEffect(() => {
    if (!mapLoaded || !map.current || !destination) return;

    // Remove old marker
    if (endMarker.current) {
      endMarker.current.remove();
    }

    // Add new marker
    endMarker.current = new goongjs.Marker({ color: '#F44336' })
      .setLngLat([destination.lon, destination.lat])
      .setPopup(
        new goongjs.Popup().setHTML(
          `<strong>Điểm đến</strong><br/>${destination.name || 'Đích đến'}`
        )
      )
      .addTo(map.current);

  }, [mapLoaded, destination]);

  // ---------- Helper: Remove all previous routes ----------
  const removeAllRouteLayers = () => {
    if (!map.current) return;

    routeLayers.current.forEach((layerId) => {
      if (map.current.getLayer(layerId)) map.current.removeLayer(layerId);
      if (map.current.getSource(layerId)) map.current.removeSource(layerId);
    });

    routeLayers.current = [];
  };

  // ---------- Helper: Add a route layer ----------
  const addRouteLayer = (coords, color, layerId, dashed = false) => {
    if (!coords || coords.length < 2) return;
    if (!map.current || !mapLoaded) return;

    map.current.addSource(layerId, {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: coords.map((c) => [c.lon, c.lat]),
        },
      },
    });

    map.current.addLayer({
      id: layerId,
      type: "line",
      source: layerId,
      paint: {
        "line-color": color,
        "line-width": 5,
        "line-opacity": 0.9,
        ...(dashed
          ? { "line-dasharray": [1, 2] }
          : {}),
      },
    });

    routeLayers.current.push(layerId);
  };

  // ---------- 2. Draw routes ----------
  useEffect(() => {
    if (!mapLoaded) return;

    removeAllRouteLayers();

    // Walking → dashed gray
    for (let i = 0; i < walk_coords.length; i++) {
      addRouteLayer(walk_coords[i], "#666", `walk_coords_${i}`, true);
    }

    // Bus Routes → each with different color
    if (bus_coords) console.log("bus_coords =", bus_coords);
    bus_coords.forEach((route, idx) => {
      const color = colorPalette[idx % colorPalette.length];

      addRouteLayer(route, color, `bus_route_${idx}`, false);
    });

  }, [walk_coords, bus_coords, mapLoaded]);

  // Fit bounds when origin/destination change
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    if (origin && destination) {
      const bounds = new goongjs.LngLatBounds();
      bounds.extend([origin.lon, origin.lat]);
      bounds.extend([destination.lon, destination.lat]);
      map.current.fitBounds(bounds, { padding: 50 });
    } else if (origin) {
      map.current.flyTo({ center: [origin.lon, origin.lat], zoom: 14 });
    } else if (destination) {
      map.current.flyTo({ center: [destination.lon, destination.lat], zoom: 14 });
    }
  }, [mapLoaded, origin, destination]);


  return (
    <div
      ref={mapContainer}
      style={{ width: "100%", height: "100%" }}
    />
  );
}
