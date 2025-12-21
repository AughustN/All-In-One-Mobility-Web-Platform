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
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
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

  const [filteredCameras, setFilteredCameras] = useState(cameras);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredCameras(cameras);
      setShowDropdown(false);
    } else {
      const filtered = cameras.filter(camera => {
        const cameraName = camera.camera_name || '';
        const displayName = camera.display_name || '';
        const searchLower = searchTerm.toLowerCase();

        return cameraName.toLowerCase().includes(searchLower) ||
          displayName.toLowerCase().includes(searchLower);
      });
      setFilteredCameras(filtered);
      setShowDropdown(true);
    }
  }, [searchTerm, cameras]);

  const handleCameraClick = (camera) => {
    setSelectedCamera(camera);
  };

  return (
    <div className="camera-map-container">
      <div className="search-container">
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Tìm camera, địa điểm..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => searchTerm && setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
            className="search-input"
          />
          
          {showDropdown && filteredCameras.length > 0 && (
            <div className="search-dropdown">
              {filteredCameras.slice(0, 8).map((camera) => (
                <div
                  key={camera.id}
                  className="search-result-item"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleCameraClick(camera);
                    setSearchTerm('');
                    setShowDropdown(false);
                  }}
                >
                  <div className="result-icon">📹</div>
                  <div className="result-info">
                    <div className="result-name">{camera.camera_name}</div>
                    <div className="result-location">{camera.display_name}</div>
                  </div>
                </div>
              ))}
              {filteredCameras.length > 8 && (
                <div className="search-result-more">
                  +{filteredCameras.length - 8} camera khác
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="camera-count">
          {filteredCameras.length} / {cameras.length}
        </div>
      </div>

      <div className="map-wrapper" style={{ position: 'relative' }}>
        <GoongCameraMap
          cameras={filteredCameras}
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
