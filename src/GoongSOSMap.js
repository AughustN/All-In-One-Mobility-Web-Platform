import React, { useEffect, useRef, useState } from 'react';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';
import {
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
  Button, Snackbar
} from '@material-ui/core';
import { BASE_URL, calculateRoute, resolveSOS } from './api';

const GOONG_MAPTILES_KEY = 'w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY';
goongjs.accessToken = GOONG_MAPTILES_KEY;

// ==========================================
// 🎨 CSS: GIỮ NGUYÊN FIX LỆCH TÂM + THÊM STYLE NÚT BẤM
// ==========================================
const sosStyles = `
  /* 1. Container chính: Căn giữa tuyệt đối bằng transform (Code cũ của bạn) */
  .sos-pin-container {
    width: 0;
    height: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0;
    margin: 0;
  }

  /* 2. Phần Icon hiển thị */
  .sos-pin-visible {
    position: absolute;
    /* Căn giữa tâm vào đúng tọa độ */
    top: 0;
    left: 0;
    transform: translate(-50%, -50%); 
    z-index: 10;
    cursor: pointer;
    
    /* Giao diện icon */
    width: 36px;
    height: 36px;
    background-color: #fff;
    border: 2px solid #d32f2f;
    border-radius: 8px;
    box-shadow: 0 3px 6px rgba(0,0,0,0.4);
    
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 20px;
    transition: transform 0.2s;
  }

  .sos-pin-visible:hover {
    transform: translate(-50%, -50%) scale(1.15);
    z-index: 20;
    border-color: #b71c1c;
  }

  /* 3. Hiệu ứng sóng (Pulse) */
  .sos-pin-ripple {
    position: absolute;
    top: 0;
    left: 0;
    transform: translate(-50%, -50%); /* Căn giữa tâm */
    width: 20px;
    height: 20px;
    background-color: rgba(211, 47, 47, 0.6);
    border-radius: 50%;
    z-index: 1;
    animation: ripple-effect 2s infinite ease-out;
  }

  @keyframes ripple-effect {
    0% { width: 20px; height: 20px; opacity: 0.8; }
    100% { width: 80px; height: 80px; opacity: 0; }
  }

  /* Style Popup */
  .goongjs-popup-content {
    padding: 0;
    border-radius: 8px;
    border: 1px solid #d32f2f;
    min-width: 280px; /* Rộng hơn chút để chứa nút */
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  }

  /* --- CSS MỚI: Style cho các nút bấm --- */
  .sos-btn-group {
    display: flex;
    gap: 8px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #eee;
  }
  
  .sos-btn {
    flex: 1;
    padding: 8px;
    border: none;
    border-radius: 4px;
    color: white;
    font-weight: 600;
    font-size: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    transition: background 0.2s;
  }

  .btn-route { background-color: #2196F3; } /* Màu xanh */
  .btn-route:hover { background-color: #1976D2; }

  .btn-resolve { background-color: #9E9E9E; } /* Màu xám */
  .btn-resolve:hover { background-color: #757575; }
`;

// Inject CSS
const styleSheet = document.createElement("style");
styleSheet.innerText = sosStyles;
document.head.appendChild(styleSheet);

function GoongSOSMap({ sosAlerts, style = 'goong_map_web', userLocation }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markers = useRef([]);
  const userMarker = useRef(null);

  // --- STATE MỚI ĐỂ QUẢN LÝ DIALOG & THÔNG BÁO ---
  const [confirmDialog, setConfirmDialog] = useState({ open: false, sosId: null });
  const [notify, setNotify] = useState({ open: false, message: '', type: 'success' });

  const currentUsername = localStorage.getItem('username');
  const getStyleUrl = (styleId) => `https://tiles.goong.io/assets/${styleId}.json`;

  useEffect(() => {
    if (map.current) return;
    map.current = new goongjs.Map({
      container: mapContainer.current,
      style: getStyleUrl(style),
      center: [106.660172, 10.762622],
      zoom: 12
    });
    map.current.addControl(new goongjs.NavigationControl(), 'top-right');
    map.current.on('load', () => setMapLoaded(true));
    return () => map.current && map.current.remove();
  }, []);

  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    map.current.setStyle(getStyleUrl(style));
  }, [style, mapLoaded]);

  // Xử lý vẽ Marker (Giữ nguyên logic cũ, chỉ thay đổi hàm gọi onclick)
  useEffect(() => {
    if (!mapLoaded || !map.current || !sosAlerts) return;

    markers.current.forEach(m => m.remove());
    markers.current = [];

    sosAlerts.forEach(alert => {
      const el = document.createElement('div');
      el.className = 'sos-pin-container';
      el.innerHTML = `<div class="sos-pin-ripple"></div><div class="sos-pin-visible">🚨</div>`;

      const popupDiv = document.createElement('div');

      // Trừ đi 6 tiếng (6 * 60 * 60 * 1000 = 21600000 ms)
      const timeString = new Date(new Date(alert.timestamp).getTime() - 7 * 60 * 60 * 1000).toLocaleString('vi-VN', {
        hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
      });

      let htmlContent = `
        <div>
          <div style="background:#d32f2f; color:white; padding:10px; font-weight:bold; display:flex; justify-content:space-between; align-items:center;">
             <span>🆘 CẢNH BÁO</span>
             <span style="font-size:0.8em; background:rgba(255,255,255,0.2); padding:2px 6px; border-radius:4px;">${timeString}</span>
          </div>
       <p style="
                margin: 0 0 10px 0; 
                font-weight: 600; 
                font-size: 14px; 
                color: #333; 
                line-height: 1.5;
                word-wrap: break-word;  /* Tự xuống dòng */
                white-space: pre-wrap;  /* Giữ nguyên định dạng xuống dòng của user */
                max-height: 80px;       /* Giới hạn chiều cao */
                overflow-y: auto;       /* Hiện thanh cuộn nếu dài quá */
            ">
              ${alert.description}
            </p>
      `;

      if (alert.image_url) {
        htmlContent += `<div style="margin-bottom:10px; border-radius:6px; overflow:hidden; border:1px solid #eee; background:#f5f5f5;"><img src="${BASE_URL}${alert.image_url}" style="width:100%; height:130px; object-fit:cover; display:block;" /></div>`;
      }

      htmlContent += `
            <div style="font-size:12px; color:#666; border-top:1px solid #eee; padding-top:8px;">
              <div style="margin-bottom:4px;">📍 <b>Vị trí:</b> ${Number(alert.lat).toFixed(5)}, ${Number(alert.lng).toFixed(5)}</div>
              <div>👤 <b>Người báo:</b> ${alert.username || 'Ẩn danh'}</div>
            </div>
            <div class="sos-btn-group">
      `;

      if (currentUsername && alert.username === currentUsername) {
        htmlContent += `<button class="sos-btn btn-resolve" id="btn-resolve-${alert.id}">✅ ĐÃ XONG</button>`;
      } else {
        htmlContent += `<button class="sos-btn btn-route" id="btn-route-${alert.id}">🚙 ĐẾN GIÚP</button>`;
      }

      htmlContent += `</div></div></div>`;
      popupDiv.innerHTML = htmlContent;

      const btnRoute = popupDiv.querySelector(`#btn-route-${alert.id}`);
      if (btnRoute) btnRoute.onclick = () => handleDrawRoute(alert.lat, alert.lng);

      const btnResolve = popupDiv.querySelector(`#btn-resolve-${alert.id}`);
      if (btnResolve) {
        // Thay vì gọi window.confirm, ta mở Dialog React
        btnResolve.onclick = () => setConfirmDialog({ open: true, sosId: alert.id });
      }

      const popup = new goongjs.Popup({ offset: 25, maxWidth: '300px', closeButton: false }).setDOMContent(popupDiv);
      const marker = new goongjs.Marker({ element: el }).setLngLat([alert.lng, alert.lat]).setPopup(popup).addTo(map.current);
      markers.current.push(marker);
    });
  }, [mapLoaded, sosAlerts]);

  // --- HÀM 1: VẼ ĐƯỜNG ---
  const handleDrawRoute = async (destLat, destLng) => {
    if (!userLocation) {
      setNotify({ open: true, message: "Vui lòng bật định vị để tìm đường!", type: 'warning' });
      return;
    }
    try {
      const start = { lat: userLocation.lat, lon: userLocation.lon };
      const end = { lat: destLat, lon: destLng };
      const data = await calculateRoute(start, end, "car");
      drawRouteOnMap(data.coords);
    } catch (e) {
      setNotify({ open: true, message: "Lỗi tìm đường: " + e.message, type: 'error' });
    }
  };

  const drawRouteOnMap = (coords) => {
    if (!map.current) return;
    if (map.current.getLayer('sos-route')) map.current.removeLayer('sos-route');
    if (map.current.getSource('sos-route')) map.current.removeSource('sos-route');

    const geojson = { type: 'Feature', geometry: { type: 'LineString', coordinates: coords.map(c => [c.lon, c.lat]) } };
    map.current.addSource('sos-route', { type: 'geojson', data: geojson });
    map.current.addLayer({ id: 'sos-route', type: 'line', source: 'sos-route', layout: { 'line-join': 'round', 'line-cap': 'round' }, paint: { 'line-color': '#2196F3', 'line-width': 6, 'line-opacity': 0.8 } });

    const bounds = new goongjs.LngLatBounds();
    coords.forEach(c => bounds.extend([c.lon, c.lat]));
    map.current.fitBounds(bounds, { padding: 50 });
  };

  // --- HÀM 2: XỬ LÝ KHI BẤM "ĐỒNG Ý" TRONG DIALOG ---
  const handleConfirmResolve = async () => {
    const sosId = confirmDialog.sosId;
    if (!sosId) return;

    try {
      await resolveSOS(sosId);

      setNotify({ open: true, message: "Đã cập nhật trạng thái thành công!", type: 'success' });

      // Ẩn marker
      const marker = markers.current.find(m => m.getPopup()._content.innerHTML.includes(`id="btn-resolve-${sosId}"`));
      if (marker) marker.remove();

      // Đóng dialog
      setConfirmDialog({ open: false, sosId: null });

    } catch (e) {
      setNotify({ open: true, message: "Lỗi: " + e.message, type: 'error' });
      setConfirmDialog({ open: false, sosId: null });
    }
  };

  // Marker User
  useEffect(() => {
    if (!mapLoaded || !map.current || !userLocation) return;
    if (userMarker.current) userMarker.current.remove();
    const el = document.createElement('div');
    el.innerHTML = '<div style="width:16px; height:16px; background:#2196F3; border:3px solid #fff; border-radius:50%; box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>';
    userMarker.current = new goongjs.Marker({ element: el }).setLngLat([userLocation.lon, userLocation.lat]).addTo(map.current);
    map.current.flyTo({ center: [userLocation.lon, userLocation.lat], zoom: 14, essential: true });
  }, [mapLoaded, userLocation]);

  return (
    <>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {/* --- DIALOG XÁC NHẬN (Thay thế window.confirm) --- */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, sosId: null })}
      >
        <DialogTitle style={{ color: '#d32f2f' }}>Xác nhận hoàn tất?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Bạn có chắc chắn muốn đánh dấu sự cố này đã được giải quyết? Báo cáo sẽ được ẩn khỏi bản đồ của mọi người.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, sosId: null })} color="default">
            Hủy bỏ
          </Button>
          <Button onClick={handleConfirmResolve} color="primary" variant="contained" style={{ backgroundColor: '#2196F3' }}>
            Đồng ý
          </Button>
        </DialogActions>
      </Dialog>

      {/* --- THÔNG BÁO ĐẸP (SNACKBAR) --- */}
      <Snackbar
        open={notify.open}
        autoHideDuration={4000}
        onClose={() => setNotify({ ...notify, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <div style={{
          padding: '12px 24px',
          borderRadius: '4px',
          color: 'white',
          fontWeight: '500',
          boxShadow: '0 3px 5px rgba(0,0,0,0.2)',
          backgroundColor:
            notify.type === 'error' ? '#f44336' :
              notify.type === 'warning' ? '#ff9800' :
                '#4caf50'
        }}>
          {notify.message}
        </div>
      </Snackbar>
    </>
  );
}

export default GoongSOSMap;