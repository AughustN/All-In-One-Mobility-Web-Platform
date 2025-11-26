import React, { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';

const GOONG_MAPTILES_KEY = 'w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY';

goongjs.accessToken = GOONG_MAPTILES_KEY;

export default function GoongBusMap({
  origin,
  destination,
  walkToBus_coords,
  walkToDes_coords,
  bus_coords,              
  unique_nameRoutes = [],
  unique_busNumbers = [],
  style = "goong_map_web",
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const routeLayers = useRef([]); // store all route layer names
  const [mapLoaded, setMapLoaded] = useState(false);
  const startMarker = useRef(null);
  const endMarker = useRef(null)


  // COLOR PALETTE FOR BUS ROUTES
  const colorPalette = [
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

    map.current.on("load", () => setMapLoaded(true));

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [style]);

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
    addRouteLayer(walkToBus_coords, "#666", "walkToBus", true);
    addRouteLayer(walkToDes_coords, "#666", "walkToDes", true);

    // Bus Routes → each with different color
    bus_coords.forEach((route, idx) => {
      const color = colorPalette[idx % colorPalette.length];
      addRouteLayer(route, color, `bus_route_${idx}`, false);
    });
  }, [walkToBus_coords, walkToDes_coords, bus_coords, mapLoaded]);

  // ---------- 3. Add info box UI ----------
useEffect(() => {
  if (!mapLoaded) return;

  const infoDiv = document.createElement("div");
  infoDiv.className = "goong-route-info";
  infoDiv.style.cssText = `
    background: white;
    padding: 12px;
    border-radius: 12px;
    width: 260px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    font-size: 13px;
    line-height: 1.4;
  `;

  let html = `<h4 style="margin-top:0;margin-bottom:8px;">Route Information</h4>`;

  // For each bus route: show color + busNumber + nameRoute
  html += unique_busNumbers
    .map((busNum, i) => {
      const color = colorPalette[i % colorPalette.length];
      return `
        <div style="display:flex;align-items:center;margin-bottom:6px;">
          <div style="
            width: 16px;
            height: 16px;
            background:${color};
            border-radius:3px;
            margin-right:8px;
          "></div>
          <b>${busNum}</b>: ${unique_nameRoutes[i]}
        </div>
      `;
    })
    .join("");

  infoDiv.innerHTML = html;

    // Custom control object
    const infoControl = {
      onAdd: () => infoDiv,
      onRemove: () => {},
    };

    map.current.addControl(infoControl, "top-left");

    return () => map.current.removeControl(infoControl);
  }, [unique_nameRoutes, unique_busNumbers, mapLoaded]);

  return (
    <div
      ref={mapContainer}
      style={{ width: "100%", height: "100%" }}
    />
  );
}
