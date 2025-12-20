import React, { useState, useEffect, useMemo } from 'react';
import GoongCameraMap from '../GoongCameraMap';
import GoongMapStyleControl from '../GoongMapStyleControl';
import MyLocationControl from '../MyLocationControl';
import cameraLocations from '../camera_locations.json';
import { fetchCameraImages } from "../api";
import '../css/CameraMap.css';

// Component to display camera images
function CameraPopup({ cameraId, cameraName }) {
  const [images, setImages] = useState([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadImages = async () => {
      try {
        setLoading(true);
        setError(null);
        const imageUrls = await fetchCameraImages(cameraId);
        setImages(imageUrls);
        setLoading(false);
      } catch (err) {
        setError("Không thể tải ảnh camera");
        setLoading(false);
      }
    };

    loadImages();
  }, [cameraId]);

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  return (
    <div className="camera-popup">
      <h3>{cameraName}</h3>
      <div className="camera-id">ID: {cameraId}</div>

      {loading && <div className="loading">Đang tải ảnh...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && images.length > 0 && (
        <div className="image-viewer">
          <img
            src={images[currentImageIndex]}
            alt={`Camera ${cameraName}`}
            className="camera-image"
          />

          {images.length > 1 && (
            <div className="image-controls">
              <button onClick={prevImage} className="nav-button">‹</button>
              <span className="image-counter">
                {currentImageIndex + 1} / {images.length}
              </span>
              <button onClick={nextImage} className="nav-button">›</button>
            </div>
          )}
        </div>
      )}

      {!loading && !error && images.length === 0 && (
        <div className="no-images">Không có ảnh cho camera này</div>
      )}
    </div>
  );
}

function CameraMapNew() {
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [mapStyle, setMapStyle] = useState('goong_map_web');
  const [userLocation, setUserLocation] = useState(null);

  // Convert camera locations to array
  const cameras = useMemo(() => {
    return Object.entries(cameraLocations)
      .filter(([, data]) => data.lat !== null && data.lon !== null)
      .map(([id, data]) => ({
        id,
        ...data
      }));
  }, []);

  const handleCameraClick = (camera) => {
    setSelectedCamera(camera);
  };

  return (
    <div className="camera-map-container">
      <div className="map-wrapper" style={{ position: 'relative' }}>
        <GoongCameraMap
          cameras={cameras}  // No filtering here, just show all cameras
          onCameraClick={handleCameraClick}
          selectedCamera={selectedCamera}
          style={mapStyle}
          userLocation={userLocation}
        />
        <MyLocationControl
          onLocationFound={(location) => {
            setUserLocation(location);
          }}
        />
        <GoongMapStyleControl
          currentStyle={mapStyle}
          onStyleChange={setMapStyle}
        />
      </div>

      {selectedCamera && (
        <div className="camera-info-panel">
          <button
            className="close-button"
            onClick={() => setSelectedCamera(null)}
          >
            ×
          </button>
          <h3>{selectedCamera.camera_name}</h3>
          <p><strong>Địa điểm:</strong> {selectedCamera.display_name}</p>
          <p><strong>Tọa độ:</strong> {selectedCamera.lat.toFixed(6)}, {selectedCamera.lon.toFixed(6)}</p>

          <CameraPopup
            cameraId={selectedCamera.id}
            cameraName={selectedCamera.camera_name}
          />
        </div>
      )}
    </div>
  );
}


export default CameraMapNew;
