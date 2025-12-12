import React, { useEffect, useRef, useState, useCallback } from 'react';
import ReactDOM from 'react-dom';
import goongjs from '@goongmaps/goong-js';
import '@goongmaps/goong-js/dist/goong-js.css';
import {
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
  Button, Snackbar, Typography, Box, TextField
} from '@material-ui/core';

import {
  Warning, ErrorOutline, Info, CheckCircle,
  DirectionsWalk, DirectionsBike, DriveEta
} from '@material-ui/icons';
import { BASE_URL, calculateRoute, resolveSOS, getComments, sendComment, reportSOSPost } from './api';

// --- 1. IMPORT TURF ĐỂ TÍNH TOÁN BÁM ĐƯỜNG ---
import * as turf from '@turf/turf';

// --- 2. IMPORT MAP CONTEXT ---
import { useMapContext } from './contexts/MapContext';

const GOONG_MAPTILES_KEY = 'nwJPo6l2E909Xn7fEIoJrSilkGxVJQSjrKxfD2UQ';
goongjs.accessToken = GOONG_MAPTILES_KEY;

const sosStyles = `
  .sos-pin-container { width: 0; height: 0; display: flex; justify-content: center; align-items: center; }
  .sos-pin-visible { position: absolute; top: 0; left: 0; transform: translate(-50%, -50%); z-index: 10; cursor: pointer; width: 40px; height: 40px; background-color: #fff; border: 2px solid #d32f2f; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); display: flex; justify-content: center; align-items: center; font-size: 22px; transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
  .sos-pin-visible:hover { transform: translate(-50%, -50%) scale(1.2); z-index: 20; border-color: #b71c1c; }
  .sos-pin-ripple { position: absolute; top: 0; left: 0; transform: translate(-50%, -50%); width: 20px; height: 20px; background-color: rgba(211, 47, 47, 0.6); border-radius: 50%; z-index: 1; animation: ripple-effect 2s infinite ease-out; }
  @keyframes ripple-effect { 0% { width: 20px; height: 20px; opacity: 0.8; } 100% { width: 90px; height: 90px; opacity: 0; } }
  .goongjs-popup-content { padding: 0; border-radius: 12px; border: none; min-width: 300px; max-width: 300px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
  .goongjs-popup-close-button { color: #333; font-size: 24px; top: 2px; right: 5px; padding: 5px; z-index: 10; outline: none; opacity: 0.6; }
  .goongjs-popup-close-button:hover { opacity: 1; background: transparent; }
  .popup-header { background: #FFB300; padding: 10px 15px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #FFB300; }
  .header-time { font-size: 15px; font-weight: 800; color: #212121; display: flex; align-items: center; gap: 6px; }
  .report-box { display: flex; align-items: center; margin-right: 25px; }
  .btn-report-clean { background: transparent !important; border: none !important; outline: none !important; padding: 0; font-size: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 2px 2px rgba(211, 47, 47, 0.3)); }
  .popup-body { padding: 12px 15px; background: #fff; }
  .popup-desc { font-size: 14px; color: #333; line-height: 1.4; margin: 0 0 10px 0; font-weight: 500; }
  .popup-image-box { position: relative; border-radius: 8px; overflow: hidden; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
  .popup-image { width: 100%; height: 120px; object-fit: cover; display: block; }
  .meta-info { display: flex; justify-content: space-between; font-size: 11px; color: #666; padding-bottom: 8px; border-bottom: 1px dashed #eee; margin-bottom: 8px; }
  .action-buttons { display: flex; gap: 8px; }
  .btn-action { flex: 1; padding: 8px 0; border: none; border-radius: 6px; color: white; font-weight: 700; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 5px; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.15); text-transform: uppercase; outline: none;}
  .btn-action:active { transform: translateY(1px); }
  .btn-blue { background: #1976D2; } .btn-blue:hover { background: #1565C0; }
  .btn-gray { background: #757575; } .btn-gray:hover { background: #616161; }
  .comment-wrapper { background: #f8f9fa; padding: 0; border-top: 1px solid #eee; }
  .comment-list { max-height: 100px; overflow-y: auto; padding: 8px 15px; scrollbar-width: thin; }
  .comment-list::-webkit-scrollbar { width: 3px; } .comment-list::-webkit-scrollbar-thumb { background-color: #ccc; border-radius: 10px; }
  .comment-row { margin-bottom: 6px; font-size: 12px; line-height: 1.3; display: flex; gap: 6px; }
  .comment-avatar { width: 20px; height: 20px; background: #e0e0e0; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 9px; font-weight: bold; color: #555; flex-shrink: 0; }
  .comment-bubble { background: #fff; padding: 4px 8px; border-radius: 0 8px 8px 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); max-width: 90%; }
  .user-name { font-weight: 700; color: #1565C0; margin-right: 4px; }
  .input-box { display: flex; padding: 8px 15px; background: #fff; border-top: 1px solid #eee; gap: 6px; align-items: center; }
  .input-field { flex: 1; padding: 6px 10px; border: 1px solid #e0e0e0; border-radius: 16px; font-size: 12px; outline: none; background: #f5f5f5; }
  .input-field:focus { background: #fff; border-color: #1976D2; }
  .btn-send { background: none; border: none; color: #1976D2; font-weight: 700; font-size: 12px; cursor: pointer; padding: 4px 8px; outline: none;}
  .btn-send:hover { background: #e3f2fd; border-radius: 12px; }
`;

if (!document.getElementById('sos-map-styles')) {
  const styleSheet = document.createElement("style");
  styleSheet.id = 'sos-map-styles';
  styleSheet.innerText = sosStyles;
  document.head.appendChild(styleSheet);
}

const formatSafeTime = (inputTime) => {
  if (!inputTime) return '';
  try {
    let dateObj = new Date(new Date(inputTime).getTime() - 7 * 60 * 60 * 1000);
    if (isNaN(dateObj.getTime())) dateObj = new Date(inputTime);
    return dateObj.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });
  } catch { return String(inputTime); }
};

function GoongSOSMap({ sosAlerts, style = 'goong_map_web', userLocation }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markersRef = useRef({});
  const userMarker = useRef(null);

  // --- 2. THÊM STATE CHO NAVIGATION ---
  const [isNavigating, setIsNavigating] = useState(false); // Cờ bật chế độ dẫn đường
  const [navCoords, setNavCoords] = useState([]); // Lưu toạ độ tuyến đường để Snap

  const currentUsername = localStorage.getItem('username');
  const getStyleUrl = (styleId) => `https://tiles.goong.io/assets/${styleId}.json`;

  const [notify, setNotify] = useState({ open: false, message: '', type: 'success' });
  const [dialogConfig, setDialogConfig] = useState({ open: false, type: 'info', title: '', content: '', onConfirm: null });
  const [reportDialog, setReportDialog] = useState({ open: false, sosId: null, reason: '' });
  const [routeConfig, setRouteConfig] = useState({ open: false, destLat: null, destLng: null, vehicle: 'car', routeType: 'fastest' });

  // ... (Giữ nguyên các hàm showDialog, closeDialog, handleDialogConfirm, useEffect init map)
  const showDialog = useCallback((type, title, content, onConfirm = null) => {
    setDialogConfig({ open: true, type, title, content, onConfirm });
  }, []);
  const closeDialog = useCallback(() => setDialogConfig(prev => ({ ...prev, open: false })), []);
  const handleDialogConfirm = useCallback(() => { dialogConfig.onConfirm && dialogConfig.onConfirm(); closeDialog(); }, [dialogConfig, closeDialog]);

  // Get registerMap from context (optional)
  const mapContext = useMapContext();
  const registerMap = mapContext?.registerMap || (() => {
    console.warn('registerMap not available');
  });

  useEffect(() => {
    if (map.current) return;
    console.log('🗺️ Initializing GoongSOSMap...');
    map.current = new goongjs.Map({ container: mapContainer.current, style: getStyleUrl(style), center: [106.660172, 10.762622], zoom: 12 });
    map.current.addControl(new goongjs.NavigationControl(), 'top-right');
    map.current.on('load', () => {
      console.log('🗺️ GoongSOSMap loaded!');
      setMapLoaded(true);
      if (registerMap) {
        registerMap(map.current); // Register map for Earth Globe
      }
    });
    return () => map.current && map.current.remove();
  }, []);

  useEffect(() => { if (map.current && mapLoaded) map.current.setStyle(getStyleUrl(style)); }, [style, mapLoaded]);

  // --- API HANDLERS (ReportPost, Resolve, Comments - Giữ nguyên) ---
  const handleReportPost = useCallback(async (sosId) => {
    const targetAlert = sosAlerts.find(a => a.id === sosId);
    if (targetAlert && targetAlert.username === currentUsername) {
      showDialog('warning', 'Không thể thực hiện', 'Bạn không thể báo cáo bài viết của chính mình.');
      return;
    }
    showDialog('warning', 'Báo cáo vi phạm?', 'Bạn có chắc muốn báo cáo bài viết này là sai sự thật?', async () => {
      try {
        const res = await reportSOSPost(sosId);
        setNotify({ open: true, message: res.message, type: 'info' });
        if (res.hidden && markersRef.current[sosId]) { markersRef.current[sosId].remove(); delete markersRef.current[sosId]; }
      } catch (e) { showDialog('error', 'Lỗi báo cáo', e.message); }
    });
  }, [showDialog]);

  const handleResolveClick = useCallback((sosId) => {
    showDialog('confirm', 'Hoàn tất?', 'Đánh dấu sự cố này đã được giải quyết?', async () => {
      try {
        await resolveSOS(sosId);
        setNotify({ open: true, message: "Đã cập nhật!", type: 'success' });
        if (markersRef.current[sosId]) { markersRef.current[sosId].remove(); delete markersRef.current[sosId]; }
      } catch (e) { showDialog('error', 'Lỗi', e.message); }
    });
  }, [showDialog]);

  const loadComments = useCallback(async (sosId, container) => {
    const listDiv = container.querySelector(`#comments-list-${sosId}`);
    if (!listDiv) return;
    try {
      const comments = await getComments(sosId);
      if (comments.length === 0) return;
      let html = '';
      comments.forEach(c => {
        const initial = (c.username || 'A').charAt(0).toUpperCase();
        html += `<div class="comment-row"><div class="comment-avatar">${initial}</div><div class="comment-bubble"><span class="user-name">${c.username}:</span><span class="user-text">${c.content}</span></div></div>`;
      });
      listDiv.innerHTML = html; listDiv.scrollTop = listDiv.scrollHeight;
    } catch (e) { listDiv.innerHTML = '<div style="color:red; font-size:10px; text-align:center;">Lỗi tải.</div>'; }
  }, []);

  const handleSubmitComment = useCallback(async (sosId, content, container) => {
    if (!localStorage.getItem('token')) { setNotify({ open: true, message: "Vui lòng đăng nhập!", type: 'warning' }); return; }
    try {
      await sendComment(sosId, content);
      const input = container.querySelector(`#input-comment-${sosId}`); if (input) input.value = '';
      const listDiv = container.querySelector(`#comments-list-${sosId}`);
      if (listDiv) {
        const initial = (currentUsername || 'M').charAt(0).toUpperCase();
        const tempHtml = `<div class="comment-row" style="opacity:0.7"><div class="comment-avatar">${initial}</div><div class="comment-bubble"><span class="user-name">${currentUsername}:</span><span class="user-text">${content}</span></div></div>`;
        if (listDiv.innerHTML.includes('Chưa có')) listDiv.innerHTML = tempHtml; else listDiv.innerHTML += tempHtml;
        listDiv.scrollTop = listDiv.scrollHeight;
      }
      setTimeout(() => loadComments(sosId, container), 500);
    } catch (e) { showDialog('error', 'Gửi thất bại', e.message); }
  }, [currentUsername, loadComments, showDialog]);

  const handleOpenReportDialog = useCallback((sosId) => {
    setReportDialog({ open: true, sosId: sosId, reason: '' });
  }, []);

  const handleSubmitReport = async () => {
    if (!reportDialog.reason.trim()) {
      setNotify({ open: true, message: "Vui lòng nhập lý do báo cáo!", type: 'warning' });
      return;
    }
    try {
      // Gọi API với tham số reason
      const res = await reportSOSPost(reportDialog.sosId, reportDialog.reason);
      setNotify({ open: true, message: res.message, type: 'info' });

      // Nếu bài bị ẩn, xóa marker
      if (res.hidden && markersRef.current[reportDialog.sosId]) {
        markersRef.current[reportDialog.sosId].remove();
        delete markersRef.current[reportDialog.sosId];
      }
      setReportDialog({ open: false, sosId: null, reason: '' }); // Đóng dialog
    } catch (e) {
      setReportDialog({ ...reportDialog, open: false });
      showDialog('error', 'Lỗi báo cáo', e.message);
    }
  };


  // --- 3. THUẬT TOÁN NAVIGATION (BÁM ĐƯỜNG) ---
  // Effect này sẽ chạy khi biến isNavigating = true
  useEffect(() => {
    if (!isNavigating || navCoords.length === 0 || !map.current) return;

    console.log("🚀 Chế độ dẫn đường cứu trợ ĐÃ BẬT");

    // Tạo LineString từ tuyến đường để tính toán
    const routeLine = turf.lineString(navCoords.map(c => [c.lon, c.lat]));

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const rawLat = position.coords.latitude;
        const rawLng = position.coords.longitude;
        const rawPoint = turf.point([rawLng, rawLat]);

        // A. Thuật toán Snap: Tìm điểm trên đường gần nhất
        const snapped = turf.nearestPointOnLine(routeLine, rawPoint);
        const dist = turf.distance(rawPoint, snapped, { units: 'meters' });

        let finalLat = rawLat;
        let finalLng = rawLng;

        // Nếu lệch < 40m thì hút vào đường, ngược lại dùng GPS thật
        if (dist < 40) {
          const [snapLng, snapLat] = snapped.geometry.coordinates;
          finalLat = snapLat;
          finalLng = snapLng;
        }

        // B. Cập nhật Marker Người Dùng
        if (userMarker.current) {
          userMarker.current.setLngLat([finalLng, finalLat]);
        } else {
          const el = document.createElement('div');
          el.innerHTML = '<div style="width:20px; height:20px; background:#2196F3; border:3px solid #fff; border-radius:50%; box-shadow:0 2px 5px rgba(0,0,0,0.4);"></div>';
          userMarker.current = new goongjs.Marker({ element: el })
            .setLngLat([finalLng, finalLat])
            .addTo(map.current);
        }

        // C. Di chuyển Camera (Chế độ Navigation)
        map.current.easeTo({
          center: [finalLng, finalLat],
          zoom: 17,
          bearing: 0,
          pitch: 0,
          duration: 1000
        });
      },
      (err) => console.error("Nav Error:", err),
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );

    // Cleanup: Tắt theo dõi khi tắt chế độ dẫn đường
    return () => {
      console.log("🛑 Kết thúc dẫn đường");
      navigator.geolocation.clearWatch(watchId);
    };
  }, [isNavigating, navCoords]);


  // --- 4. CẬP NHẬT HÀM VẼ ĐƯỜNG ĐỂ KÍCH HOẠT NAVIGATION ---
  const handleOpenRouteDialog = useCallback((lat, lng) => {
    setRouteConfig({ open: true, destLat: lat, destLng: lng, vehicle: 'car', routeType: 'fastest' });
  }, []);

  const handleDrawRoute = useCallback(() => {
    const { destLat, destLng, vehicle, routeType } = routeConfig;

    setRouteConfig(prev => ({ ...prev, open: false }));
    setNotify({ open: true, message: "Đang tính toán lộ trình cứu trợ...", type: 'info' });

    if (!navigator.geolocation) {
      setNotify({ open: true, message: "Lỗi: Không có GPS!", type: 'error' });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const currentLat = position.coords.latitude;
        const currentLng = position.coords.longitude;

        try {
          const data = await calculateRoute(
            { lat: currentLat, lon: currentLng },
            { lat: destLat, lon: destLng },
            vehicle, routeType
          );

          // Vẽ đường lên map
          if (map.current.getLayer('sos-route')) map.current.removeLayer('sos-route');
          if (map.current.getSource('sos-route')) map.current.removeSource('sos-route');

          const geojson = {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: data.coords.map(c => [c.lon, c.lat]) }
          };

          map.current.addSource('sos-route', { type: 'geojson', data: geojson });
          map.current.addLayer({
            id: 'sos-route', type: 'line', source: 'sos-route',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': vehicle === 'car' ? '#2196F3' : '#FF9800',
              'line-width': 7,
              'line-opacity': 0.8
            }
          });

          // Zoom fit
          const bounds = new goongjs.LngLatBounds();
          data.coords.forEach(c => bounds.extend([c.lon, c.lat]));
          bounds.extend([currentLng, currentLat]);
          map.current.fitBounds(bounds, { padding: 80 });

          // --- KÍCH HOẠT CHẾ ĐỘ NAVIGATION ---
          setNavCoords(data.coords); // Lưu toạ độ để Snap
          setIsNavigating(true);     // Bật cờ theo dõi

          setNotify({ open: true, message: "Bắt đầu dẫn đường!", type: 'success' });

        } catch (e) {
          showDialog('error', 'Lỗi tìm đường', e.message);
        }
      },
      (error) => setNotify({ open: true, message: "Không lấy được vị trí!", type: 'error' }),
      { enableHighAccuracy: true }
    );
  }, [routeConfig, showDialog]);


  // RENDER MARKERS & MAP (Phần này giữ nguyên logic hiển thị, chỉ lưu ý phần userMarker)
  useEffect(() => {
    if (!mapLoaded || !map.current || !sosAlerts) return;
    const activeIds = sosAlerts.map(a => a.id);
    Object.keys(markersRef.current).forEach(id => { if (!activeIds.includes(parseInt(id))) { markersRef.current[id].remove(); delete markersRef.current[id]; } });

    sosAlerts.forEach(alert => {
      // ... (Giữ nguyên logic tạo marker SOS và Popup như file cũ) ...
      if (markersRef.current[alert.id]) return;
      const el = document.createElement('div'); el.className = 'sos-pin-container'; el.innerHTML = `<div class="sos-pin-ripple"></div><div class="sos-pin-visible">🚨</div>`;

      // ... (Tạo nội dung Popup - Giữ nguyên) ...
      const popupDiv = document.createElement('div');
      // Copy lại toàn bộ logic tạo HTML popup từ file cũ vào đây (rất dài nên tôi rút gọn trong comment)
      // Chú ý: Các nút bấm trong popup gọi handleOpenRouteDialog, handleReportPost, v.v. vẫn hoạt động đúng.

      // CODE POPUP CŨ CỦA BẠN (Đã copy lại để đảm bảo không mất)
      const timeDisplay = formatSafeTime(alert.timestamp);
      const isOwnPost = currentUsername === alert.username;
      let htmlContent = `
        <div class="popup-wrapper">
          <div class="popup-header">
             <div class="header-time">🕒 ${timeDisplay}</div>
             ${!isOwnPost ? `<div class="report-box" id="btn-report-${alert.id}"><button class="btn-report-clean">⚠️</button></div>` : ''}
          </div>
          <div class="popup-body">
      `;
      if (alert.description) htmlContent += `<div class="popup-desc">${alert.description}</div>`;
      if (alert.image_url) htmlContent += `<div class="popup-image-box"><img src="${BASE_URL}${alert.image_url}" class="popup-image" /></div>`;
      htmlContent += `
            <div class="meta-info"><div class="meta-item">📍 ${Number(alert.lat).toFixed(4)}, ${Number(alert.lng).toFixed(4)}</div><div class="meta-item">👤 <b>${alert.username || 'Ẩn danh'}</b></div></div>
            <div class="action-buttons">
      `;
      if (currentUsername && alert.username === currentUsername) htmlContent += `<button class="btn-action btn-gray" id="btn-resolve-${alert.id}">✅ Đã xong</button>`;
      else htmlContent += `<button class="btn-action btn-blue" id="btn-route-${alert.id}">🚙 Đến giúp</button>`;
      htmlContent += `</div></div>
            <div class="comment-wrapper">
                <div class="comment-list" id="comments-list-${alert.id}"><div style="text-align:center; color:#999; font-size:10px; padding:5px;">Chưa có bình luận.</div></div>
                <div class="input-box"><input type="text" class="input-field" id="input-comment-${alert.id}" placeholder="Bình luận..." autocomplete="off"/><button class="btn-send" id="btn-comment-${alert.id}">Gửi</button></div></div></div>
      `;
      popupDiv.innerHTML = htmlContent;
      // ... (Gán sự kiện click cho popup - Giữ nguyên) ...
      const btnReport = popupDiv.querySelector(`#btn-report-${alert.id}`); if (btnReport) { btnReport.onclick = () => handleOpenReportDialog(alert.id); }
      const btnRoute = popupDiv.querySelector(`#btn-route-${alert.id}`); if (btnRoute) btnRoute.onclick = () => handleOpenRouteDialog(alert.lat, alert.lng);
      const btnResolve = popupDiv.querySelector(`#btn-resolve-${alert.id}`); if (btnResolve) btnResolve.onclick = () => handleResolveClick(alert.id);
      const btnSendComment = popupDiv.querySelector(`#btn-comment-${alert.id}`); const inputComment = popupDiv.querySelector(`#input-comment-${alert.id}`);
      const doSendComment = () => { const txt = inputComment.value.trim(); if (txt) handleSubmitComment(alert.id, txt, popupDiv); };
      if (btnSendComment) { btnSendComment.onclick = doSendComment; inputComment.addEventListener("keypress", (e) => { if (e.key === "Enter") doSendComment(); }); }

      const popup = new goongjs.Popup({ offset: 25, maxWidth: '300px', closeButton: true }).setDOMContent(popupDiv);
      popup.on('open', () => loadComments(alert.id, popupDiv));
      const marker = new goongjs.Marker({ element: el }).setLngLat([alert.lng, alert.lat]).setPopup(popup).addTo(map.current);
      markersRef.current[alert.id] = marker;

    });
  }, [mapLoaded, sosAlerts, currentUsername, handleReportPost, handleDrawRoute, handleResolveClick, handleSubmitComment, loadComments, handleOpenReportDialog]); // Thêm dependencies

  // --- XỬ LÝ USER LOCATION (Khi chưa bật Navigation) ---
  // Nếu đang Navigating thì Effect Navigation ở trên sẽ lo việc vẽ User Marker
  useEffect(() => {
    if (!mapLoaded || !map.current || !userLocation || isNavigating) return; // Nếu đang Navigating thì bỏ qua effect này

    if (userMarker.current) userMarker.current.remove();
    const el = document.createElement('div');
    el.innerHTML = '<div style="width:16px; height:16px; background:#2196F3; border:3px solid #fff; border-radius:50%; box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>';

    userMarker.current = new goongjs.Marker({ element: el })
      .setLngLat([userLocation.lon, userLocation.lat])
      .addTo(map.current);

    map.current.flyTo({ center: [userLocation.lon, userLocation.lat], zoom: 14, essential: true });
  }, [mapLoaded, userLocation, isNavigating]); // Thêm isNavigating vào dependency

  const getDialogHeaderStyle = (type) => {
    switch (type) {
      case 'error': return { color: '#d32f2f', icon: <ErrorOutline style={{ fontSize: 40, color: '#d32f2f' }} /> };
      case 'warning': return { color: '#ed6c02', icon: <Warning style={{ fontSize: 40, color: '#ed6c02' }} /> };
      case 'confirm': return { color: '#2e7d32', icon: <CheckCircle style={{ fontSize: 40, color: '#2e7d32' }} /> };
      default: return { color: '#0288d1', icon: <Info style={{ fontSize: 40, color: '#0288d1' }} /> };
    }
  };
  const dialogStyle = getDialogHeaderStyle(dialogConfig.type);

  return (
    <>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      {/* ... Các Dialog (Info, Report, Route) giữ nguyên như file gốc ... */}

      <Dialog open={dialogConfig.open} onClose={closeDialog} PaperProps={{ style: { borderRadius: 12, padding: '10px' } }}>
        <DialogTitle disableTypography><Box display="flex" flexDirection="column" alignItems="center" justifyContent="center"><Info style={{ fontSize: 40, color: '#0288d1' }} /><Typography variant="h6" style={{ color: '#0288d1', fontWeight: 700, marginTop: 10 }}>{dialogConfig.title}</Typography></Box></DialogTitle>
        <DialogContent><DialogContentText style={{ textAlign: 'center', color: '#555' }}>{dialogConfig.content}</DialogContentText></DialogContent>
        <DialogActions style={{ justifyContent: 'center', paddingBottom: 20 }}>{dialogConfig.onConfirm ? (<><Button onClick={closeDialog} style={{ color: '#888', fontWeight: 600 }}>Hủy bỏ</Button><Button onClick={handleDialogConfirm} variant="contained" style={{ backgroundColor: '#0288d1', color: 'white', fontWeight: 600, borderRadius: 20, padding: '6px 24px' }}>Đồng ý</Button></>) : (<Button onClick={closeDialog} variant="outlined" style={{ color: '#0288d1', borderColor: '#0288d1', fontWeight: 600, borderRadius: 20, padding: '6px 24px' }}>Đóng</Button>)}</DialogActions>
      </Dialog>

      <Dialog open={reportDialog.open} onClose={() => setReportDialog({ ...reportDialog, open: false })} maxWidth="xs" fullWidth PaperProps={{ style: { borderRadius: 12 } }}>
        <DialogTitle style={{ color: '#ed6c02', fontWeight: 'bold' }}>Báo cáo vi phạm</DialogTitle>
        <DialogContent>
          <DialogContentText>Vui lòng cho biết lý do bạn báo cáo bài viết này?</DialogContentText>
          <TextField autoFocus margin="dense" label="Lý do" fullWidth variant="outlined" value={reportDialog.reason} onChange={(e) => setReportDialog({ ...reportDialog, reason: e.target.value })} />
        </DialogContent>
        <DialogActions style={{ padding: 20 }}><Button onClick={() => setReportDialog({ ...reportDialog, open: false })}>Hủy</Button><Button onClick={handleSubmitReport} variant="contained" style={{ backgroundColor: '#ed6c02', color: 'white' }}>Gửi báo cáo</Button></DialogActions>
      </Dialog>

      <Dialog open={routeConfig.open} onClose={() => setRouteConfig({ ...routeConfig, open: false })} fullWidth maxWidth="xs" PaperProps={{ style: { borderRadius: 12, padding: '8px' } }}>
        <DialogTitle style={{ paddingBottom: 5 }}><Typography variant="h6" style={{ fontWeight: 'bold' }}>Tùy chọn di chuyển</Typography></DialogTitle>
        <DialogContent>
          <Typography variant="subtitle2" style={{ fontWeight: 'bold', marginBottom: '10px', color: '#333' }}>Tuyến đường ưu tiên</Typography>
          <Box display="flex" justifyContent="space-between" mb={3}>
            <Button variant={routeConfig.routeType === 'fastest' ? "contained" : "outlined"} color="primary" onClick={() => setRouteConfig({ ...routeConfig, routeType: 'fastest' })} style={{ width: '48%' }}>NHANH NHẤT</Button>
            <Button variant={routeConfig.routeType === 'shortest' ? "contained" : "outlined"} color="primary" onClick={() => setRouteConfig({ ...routeConfig, routeType: 'shortest' })} style={{ width: '48%' }}>NGẮN NHẤT</Button>
          </Box>
          <Typography variant="subtitle2" style={{ fontWeight: 'bold', marginBottom: '10px', color: '#333' }}>Phương tiện</Typography>
          <Box display="flex" justifyContent="space-between">
            {[{ value: 'pedestrian', icon: <DirectionsWalk /> }, { value: 'bicycle', icon: <DirectionsBike /> }, { value: 'car', icon: <DriveEta /> }].map((item) => {
              const isSelected = routeConfig.vehicle === item.value;
              return (<Box key={item.value} onClick={() => setRouteConfig({ ...routeConfig, vehicle: item.value })} style={{ cursor: 'pointer', width: '30%', height: '50px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: isSelected ? '2px solid #0277BD' : '1px solid #e0e0e0', backgroundColor: isSelected ? '#E3F2FD' : '#fff', color: '#0277BD' }}>{item.icon}</Box>)
            })}
          </Box>
        </DialogContent>
        <DialogActions style={{ padding: '10px 24px 20px' }}>
          <Button onClick={() => setRouteConfig({ ...routeConfig, open: false })} style={{ color: '#666' }}>Hủy</Button>
          <Button onClick={handleDrawRoute} variant="contained" color="primary" startIcon={<CheckCircle />} style={{ borderRadius: 20 }}>Bắt đầu đi</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={notify.open} autoHideDuration={3000} onClose={() => setNotify({ ...notify, open: false })} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}><div style={{ padding: '12px 24px', borderRadius: '8px', color: 'white', fontWeight: '600', backgroundColor: notify.type === 'error' ? '#d32f2f' : notify.type === 'warning' ? '#ed6c02' : '#2e7d32' }}>{notify.message}</div></Snackbar>
    </>
  );
}

export default GoongSOSMap;