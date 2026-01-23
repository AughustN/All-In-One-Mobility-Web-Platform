import React, { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';

const GOONG_MAPTILES_KEY = process.env.REACT_APP_GOONG_MAPTILES_KEY;

goongjs.accessToken = GOONG_MAPTILES_KEY;
// goongjs.accessToken = 'nwJPo6l2E909Xn7fEIoJrSilkGxVJQSjrKxfD2UQ';

function GoongMap({ origin, destination, coords, style = 'goong_map_web', userLocation, coloredRouteGeoJSON, routeCameras = [], onRouteCameraClick, selectedCamera, }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Markers refs
  const startMarker = useRef(null);
  const endMarker = useRef(null);
  const userMarker = useRef(null);
  const routeLayer = useRef(null);
  const routeCameraMarkers = useRef({});
  const routeCameraPopup = useRef(null);

  // Initialize map
  useEffect(() => {
    if (map.current) return; // Initialize map only once

    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: `https://tiles.goong.io/assets/${style}.json`,
      center: [106.6297, 10.8231], // HCM City
      zoom: 12
    });

    // Add navigation controls
    map.current.addControl(new goongjs.NavigationControl(), 'top-right');

    // Add scale control
    map.current.addControl(new goongjs.ScaleControl({
      maxWidth: 100,
      unit: 'metric'
    }), 'bottom-left');

    map.current.on('load', () => {
      setMapLoaded(true);
      console.log('✅ Goong Map loaded');
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [style]);

  // Update origin marker
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

  // Update destination marker
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

  // Update route + congestion overlay
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // ✅ always remove old layers/sources first
    ['route-base', 'route-colored'].forEach(id => {
      if (map.current.getLayer(id)) map.current.removeLayer(id);
    });
    if (map.current.getSource('route')) map.current.removeSource('route');
    if (map.current.getSource('route-colored')) map.current.removeSource('route-colored');

    // ✅ if no coords, stop AFTER cleanup
    if (!coords || coords.length === 0) return;

    const bounds = new goongjs.LngLatBounds();
    coords.forEach(c => bounds.extend([c.lon, c.lat]));
    map.current.fitBounds(bounds, { padding: 50 });

    if (coloredRouteGeoJSON && coloredRouteGeoJSON.features?.length) {
      map.current.addSource('route-colored', { type: 'geojson', data: coloredRouteGeoJSON });

      map.current.addLayer({
        id: 'route-colored',
        type: 'line',
        source: 'route-colored',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-width': 6,
          'line-opacity': 0.9,
          'line-color': ['get', 'color'],
        },
      });
    } else {
      map.current.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: { type: 'LineString', coordinates: coords.map(c => [c.lon, c.lat]) },
        },
      });

      map.current.addLayer({
        id: 'route-base',
        type: 'line',
        source: 'route',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#0277BD', 'line-width': 5, 'line-opacity': 0.7 },
      });
    }
  }, [mapLoaded, coords, coloredRouteGeoJSON]);

  // Adjust camera to fit markers if no route is drawn
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // If a route is drawn, let the route effect control camera
    if (coords && coords.length > 0) return;

    if (origin && destination) {
      const bounds = new goongjs.LngLatBounds();
      bounds.extend([origin.lon, origin.lat]);
      bounds.extend([destination.lon, destination.lat]);
      map.current.fitBounds(bounds, { padding: 50, duration: 1200 });
    } else if (origin) {
      map.current.flyTo({ center: [origin.lon, origin.lat], zoom: 14, duration: 1200 });
    } else if (destination) {
      map.current.flyTo({ center: [destination.lon, destination.lat], zoom: 14, duration: 1200 });
    }
  }, [mapLoaded, origin, destination, coords]);

  // Handle user location
  useEffect(() => {
    if (!mapLoaded || !map.current || !userLocation) return;

    // Remove old user marker
    if (userMarker.current) {
      userMarker.current.remove();
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

    userMarker.current = marker;

    // Fly to user location
    map.current.flyTo({
      center: [userLocation.lon, userLocation.lat],
      zoom: 15,
      duration: 1500
    });

  }, [mapLoaded, userLocation]);

  // Handle route cameras
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // remove old popup
    if (routeCameraPopup.current) {
      routeCameraPopup.current.remove();
      routeCameraPopup.current = null;
    }

    // remove old markers
    Object.values(routeCameraMarkers.current).forEach(marker => {
      try { marker.remove(); } catch (e) { }
    });
    routeCameraMarkers.current = {};

    // stop if none
    if (!routeCameras || routeCameras.length === 0) return;

    // add markers for cameras on route
    routeCameras.forEach((camera) => {
      if (!camera || camera.lat == null || camera.lon == null) return;

      const el = document.createElement('div');
      el.className = 'camera-marker';
      el.innerHTML = '📹';
      el.style.fontSize = '24px';
      el.style.cursor = 'pointer';

      const marker = new goongjs.Marker({ element: el })
        .setLngLat([camera.lon, camera.lat])
        .addTo(map.current);

      el.addEventListener('click', () => {
        // close existing popup
        if (routeCameraPopup.current) routeCameraPopup.current.remove();

        // open popup on map
        const popup = new goongjs.Popup({
          offset: 25,
          closeButton: true,
          closeOnClick: true,
        })
          .setLngLat([camera.lon, camera.lat])
          .setHTML(
            `<div style="padding: 8px;">
            <strong style="font-size: 14px;">${camera.camera_name || 'Camera'}</strong><br/>
            <small style="color:#666;">${camera.display_name || ''}</small>
          </div>`
          )
          .addTo(map.current);

        routeCameraPopup.current = popup;

        // notify parent (RoutesPage) to show side panel images/info
        if (onRouteCameraClick) onRouteCameraClick(camera);
      });

      // choose a stable key
      const key = camera.id != null ? String(camera.id) : `${camera.lon},${camera.lat}`;
      routeCameraMarkers.current[key] = marker;
    });
  }, [mapLoaded, routeCameras, onRouteCameraClick]);

  // Fly to selected camera
  useEffect(() => {
    if (!mapLoaded || !map.current || !selectedCamera) return;
    if (selectedCamera.lat == null || selectedCamera.lon == null) return;

    map.current.flyTo({
      center: [selectedCamera.lon, selectedCamera.lat],
      zoom: 16,
      duration: 900,
    });
  }, [mapLoaded, selectedCamera]);

  return (
    <div
      ref={mapContainer}
      style={{ width: '100%', height: '100%' }}
    />
  );
}

export default GoongMap;
