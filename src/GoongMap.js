import React, { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';
import { useMapContext } from './contexts/MapContext';

const GOONG_MAPTILES_KEY = 'w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY';

goongjs.accessToken = GOONG_MAPTILES_KEY;

function GoongMap({ origin, destination, coords, style = 'goong_map_web', userLocation }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const mapContext = useMapContext();
  const registerMap = mapContext?.registerMap || (() => {});
  
  // Markers refs
  const startMarker = useRef(null);
  const endMarker = useRef(null);
  const userMarker = useRef(null);

  // 1. KHỞI TẠO MAP
  useEffect(() => {
    if (map.current) return;

    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: `https://tiles.goong.io/assets/${style}.json`,
      center: [106.6297, 10.8231], // HCM City
      zoom: 12
    });

    map.current.addControl(new goongjs.NavigationControl(), 'top-right');
    map.current.addControl(new goongjs.ScaleControl({ maxWidth: 100, unit: 'metric' }), 'bottom-left');

    map.current.on('load', () => {
      setMapLoaded(true);
      registerMap(map.current);
      console.log('✅ Goong Map loaded');
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [style]);

  // 2. VẼ TUYẾN ĐƯỜNG (POLYLINE)
  useEffect(() => {
    if (!mapLoaded || !map.current || !coords || coords.length === 0) return;

    const sourceId = 'route-source';
    const layerId = 'route-layer';

    // Remove old route if exists
    if (map.current.getLayer(layerId)) map.current.removeLayer(layerId);
    if (map.current.getSource(sourceId)) map.current.removeSource(sourceId);

    const geojson = {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: coords.map(c => [c.lon, c.lat])
      }
    };

    map.current.addSource(sourceId, { type: 'geojson', data: geojson });

    map.current.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: {
        'line-color': '#0277BD',
        'line-width': 6,
        'line-opacity': 0.8
      }
    });

    // Nếu KHÔNG PHẢI chế độ GPS (userLocation null) thì zoom toàn bộ tuyến đường
    if (!userLocation) {
        const bounds = new goongjs.LngLatBounds();
        coords.forEach(c => bounds.extend([c.lon, c.lat]));
        map.current.fitBounds(bounds, { padding: 50 });
    }

  }, [mapLoaded, coords, userLocation]);

  // 3. XỬ LÝ MARKER (ĐIỂM ĐẦU, ĐIỂM CUỐI, VÀ NGƯỜI DÙNG)
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // --- A. MARKER ĐIỂM ĐẾN (Luôn hiển thị nếu có) ---
    if (destination) {
        if (!endMarker.current) {
            endMarker.current = new goongjs.Marker({ color: '#F44336' }) // Màu Đỏ
                .setLngLat([destination.lon, destination.lat])
                .setPopup(new goongjs.Popup().setHTML(`<strong>Đến:</strong> ${destination.name}`))
                .addTo(map.current);
        } else {
            endMarker.current.setLngLat([destination.lon, destination.lat]);
        }
    } else {
        if (endMarker.current) endMarker.current.remove();
        endMarker.current = null;
    }

    // --- B. MARKER ĐIỂM ĐI (Chỉ hiển thị khi KHÔNG CÓ GPS User) ---
    // Logic: Nếu đang dẫn đường bằng GPS, vị trí Start chính là icon User di chuyển, nên ta ẩn Marker Start tĩnh đi cho đỡ rối.
    if (origin && !userLocation) {
        if (!startMarker.current) {
            startMarker.current = new goongjs.Marker({ color: '#4CAF50' }) // Màu Xanh
                .setLngLat([origin.lon, origin.lat])
                .setPopup(new goongjs.Popup().setHTML(`<strong>Đi:</strong> ${origin.name}`))
                .addTo(map.current);
        } else {
            startMarker.current.setLngLat([origin.lon, origin.lat]);
            startMarker.current.addTo(map.current); // Đảm bảo thêm lại nếu bị remove
        }
    } else {
        // Nếu có userLocation hoặc không có origin -> Xóa marker Start
        if (startMarker.current) startMarker.current.remove();
        startMarker.current = null;
    }

    // --- C. MARKER NGƯỜI DÙNG (Chỉ hiển thị khi CÓ GPS) ---
    if (userLocation) {
        if (!userMarker.current) {
            const el = document.createElement('div');
            el.innerHTML = '<div style="width:20px; height:20px; background:#2196F3; border:3px solid #fff; border-radius:50%; box-shadow:0 2px 5px rgba(0,0,0,0.4);"></div>';


            userMarker.current = new goongjs.Marker(el)
                .setLngLat([userLocation.lon, userLocation.lat])
                .setPopup(new goongjs.Popup({ offset: 25 }).setHTML('<div>Bạn đang ở đây</div>'))
                .addTo(map.current);
        } else {
            userMarker.current.setLngLat([userLocation.lon, userLocation.lat]);
        }

        // CAMERA FOLLOW USER (Chế độ 2D, không xoay/nghiêng)
        map.current.easeTo({
            center: [userLocation.lon, userLocation.lat],
            zoom: 16,
            bearing: 0, 
            pitch: 0,
            duration: 1000
        });

    } else {
        if (userMarker.current) userMarker.current.remove();
        userMarker.current = null;
    }

  }, [mapLoaded, origin, destination, userLocation]);

  return <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />;
}

export default GoongMap;