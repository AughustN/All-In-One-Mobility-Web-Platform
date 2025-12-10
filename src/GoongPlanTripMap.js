import React, { useEffect, useRef, useState } from "react";
import goongjs from "@goongmaps/goong-js";
import "@goongmaps/goong-js/dist/goong-js.css";
import { BASE_URL, calculateRoute } from './api';

const GOONG_MAPTILES_KEY = "w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY";
goongjs.accessToken = GOONG_MAPTILES_KEY;

export default function GoongPlanTripMap({
  plan,
  style = "goong_map_web",
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // store marker refs
  const markersRef = useRef([]);

  const itinerary = plan?.itinerary || [];

  // -------- 1. Initialize Map --------
  useEffect(() => {
    if (map.current) return;

    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: `https://tiles.goong.io/assets/${style}.json`,
      center: [106.6297, 10.8231],
      zoom: 12,
    });

    map.current.addControl(new goongjs.NavigationControl(), "top-right");

    map.current.on("load", () => {
      setMapLoaded(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [style]);

  // -------- 2. Add Markers After Map Loaded --------
  useEffect(() => {
    if (!mapLoaded || !map.current || itinerary.length === 0) return;

    // Remove old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Fit bounds
    const bounds = new goongjs.LngLatBounds();

    itinerary.forEach((item) => {
      if(!item.lat || !item.lng) return;
      
      const marker = new goongjs.Marker({ color: "#ff5252" })
        .setLngLat([item.lng, item.lat])
        .setPopup(
          new goongjs.Popup({ offset: 25 }).setHTML(`
            <div style="width:200px">
              ${item.image_url
                ? `<img src="${BASE_URL}/${item.image_url}" style="width:100%; height:100px; object-fit:cover; border-radius:6px;" />`
                : ``
                }

              <h3 style="margin:8px 0 4px 0; font-size:16px;">${item.place}</h3>
              <p style="margin:0;"><b>Activity:</b> ${item.activity}</p>
              <p style="margin:0;"><b>Time:</b> ${item.time}</p>
              <p style="margin:0;"><b>Address:</b> ${item.address}</p>
              <p style="margin:0;"><b>Cost:</b> ${item.cost}</p>
            </div>
          `)
        )
        .addTo(map.current);

      markersRef.current.push(marker);
      bounds.extend([item.lng, item.lat]);
    });

    // auto fit map to show all points
    if (itinerary.length > 1) {
      map.current.fitBounds(bounds, { padding: 50 });
    } else {
      map.current.flyTo({
        center: [itinerary[0].lng, itinerary[0].lat],
        zoom: 15,
      });
    }
  }, [mapLoaded, itinerary]);

  return (
    <div
      ref={mapContainer}
      style={{ width: "100%", height: "100%" }}
    ></div>
  );
}
