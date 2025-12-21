import React, { useState } from 'react';
import './css/MyLocationControl.css';

function MyLocationControl({ onLocationFound }) {
  const [loading, setLoading] = useState(false);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert('Trình duyệt không hỗ trợ định vị');
      return;
    }

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        
        if (onLocationFound) {
          onLocationFound({ lat: latitude, lon: longitude });
        }
        
        setLoading(false);
      },
      (error) => {
        console.error('Geolocation error:', error);
        alert('Không thể lấy vị trí. Vui lòng cho phép truy cập vị trí.');
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

  return (
    <div className="my-location-control">
      <button 
        className="my-location-button"
        onClick={handleGetLocation}
        disabled={loading}
        title="Vị trí của tôi"
      >
        {loading ? '⏳' : '📍'}
      </button>
    </div>
  );
}

export default MyLocationControl;
