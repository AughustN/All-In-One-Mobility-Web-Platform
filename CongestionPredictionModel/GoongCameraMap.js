import { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';

const GOONG_MAPTILES_KEY = 'w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY';

goongjs.accessToken = GOONG_MAPTILES_KEY;

function GoongCameraMap({ cameras, onCameraClick, selectedCamera, style = 'goong_map_web', userLocation }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markers = useRef({});
  const currentPopup = useRef(null);
  const userMarker = useRef(null);
  
  // Convert style ID to URL
  const getStyleUrl = (styleId) => {
    return `https://tiles.goong.io/assets/${styleId}.json`;
  };

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: getStyleUrl(style),
      center: [106.660172, 10.762622],
      zoom: 13
    });

    map.current.addControl(new goongjs.NavigationControl(), 'top-right');
    map.current.addControl(new goongjs.ScaleControl({
      maxWidth: 100,
      unit: 'metric'
    }), 'bottom-left');

    map.current.on('load', () => {
      setMapLoaded(true);
      console.log('✅ Goong Camera Map loaded');
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update map style
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    
    // Close popup
    if (currentPopup.current) {
      currentPopup.current.remove();
      currentPopup.current = null;
    }
    
    // Remove markers
    Object.values(markers.current).forEach(marker => {
      try {
        marker.remove();
      } catch (e) {
        // ignore
      }
    });
    markers.current = {};
    
    map.current.setStyle(getStyleUrl(style));
  }, [style, mapLoaded]);

  // Update camera markers
  useEffect(() => {
    if (!mapLoaded || !map.current || !cameras) return;

    // Remove old markers
    Object.values(markers.current).forEach(marker => {
      try {
        marker.remove();
      } catch (e) {
        // ignore
      }
    });
    markers.current = {};

    // Add new markers
    cameras.forEach(camera => {
      if (!camera.lat || !camera.lon) return;

      const el = document.createElement('div');
      el.className = 'camera-marker';
      el.innerHTML = '📹';
      el.style.fontSize = '24px';
      el.style.cursor = 'pointer';

      const marker = new goongjs.Marker({ element: el })
        .setLngLat([camera.lon, camera.lat])
        .addTo(map.current);

      // Click handler - create popup dynamically
      el.addEventListener('click', () => {
        // Close existing popup
        if (currentPopup.current) {
          currentPopup.current.remove();
        }

        // Create new popup
        const popup = new goongjs.Popup({ 
          offset: 25,
          closeButton: true,
          closeOnClick: true
        })
          .setLngLat([camera.lon, camera.lat])
          .setHTML(
            `<div style="padding: 8px;">
              <strong style="font-size: 14px;">${camera.camera_name}</strong><br/>
              <small style="color: #666;">${camera.display_name || ''}</small>
            </div>`
          )
          .addTo(map.current);

        currentPopup.current = popup;

        // Call parent handler
        if (onCameraClick) {
          onCameraClick(camera);
        }
      });

      markers.current[camera.id] = marker;
    });

  }, [mapLoaded, cameras, onCameraClick]);

  // Zoom to selected camera
  useEffect(() => {
    if (!mapLoaded || !map.current || !selectedCamera) return;

    map.current.flyTo({
      center: [selectedCamera.lon, selectedCamera.lat],
      zoom: 16,
      duration: 1000
    });

    // Open popup after animation
    setTimeout(() => {
      if (!map.current) return;

      // Close existing popup
      if (currentPopup.current) {
        currentPopup.current.remove();
      }

      // Create new popup
      const popup = new goongjs.Popup({ 
        offset: 25,
        closeButton: true,
        closeOnClick: true
      })
        .setLngLat([selectedCamera.lon, selectedCamera.lat])
        .setHTML(
          `<div style="padding: 8px;">
            <strong style="font-size: 14px;">${selectedCamera.camera_name}</strong><br/>
            <small style="color: #666;">${selectedCamera.display_name || ''}</small>
          </div>`
        )
        .addTo(map.current);

      currentPopup.current = popup;
    }, 1100);

  }, [mapLoaded, selectedCamera]);

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

  return (
    <div 
      ref={mapContainer} 
      style={{ width: '100%', height: '100%' }}
    />
  );
}

export default GoongCameraMap;
