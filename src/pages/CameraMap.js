import React, { useState, useEffect } from 'react';
import { MapContainer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../css/CameraMap.css';
import MapLayerControl from '../MapLayerControl';

// Import camera locations
import cameraLocations from '../camera_locations.json';
import { fetchCameraImages } from "../api";

// Custom camera icon
const cameraSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#2196F3">
  <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
</svg>`;

const cameraIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(cameraSvg),
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

// Component to handle map centering
function MapCenter({ center, zoom = 16 }) {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.setView(center, zoom, { animate: true, duration: 0.5 });
    }
  }, [center, zoom, map]);

  return null;
}

// Component to handle marker with auto popup
function CameraMarker({ camera, icon, onCameraClick, shouldOpenPopup }) {
  const markerRef = React.useRef(null);

  useEffect(() => {
    if (shouldOpenPopup && markerRef.current) {
      markerRef.current.openPopup();
    }
  }, [shouldOpenPopup]);

  return (
    <Marker
      ref={markerRef}
      position={[camera.lat, camera.lon]}
      icon={icon}
      eventHandlers={{
        click: () => onCameraClick(camera)
      }}
    >
      <Popup maxWidth={400} minWidth={300}>
        <CameraPopup
          cameraId={camera.id}
          cameraName={camera.camera_name}
        />
      </Popup>
    </Marker>
  );
}

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


function CameraMap() {
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [mapCenter, setMapCenter] = useState([10.762622, 106.660172]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [triggerPopup, setTriggerPopup] = useState(null);

  const cameras = React.useMemo(() => {
    return Object.entries(cameraLocations)
      .filter(([id, data]) => data.lat !== null && data.lon !== null)
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
    setMapCenter([camera.lat, camera.lon]);
    
    setTriggerPopup(null);
    setTimeout(() => {
      setTriggerPopup(camera.id);
    }, 500);
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

      <div className="map-wrapper">
        <MapContainer
          center={mapCenter}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <MapLayerControl />

          <MapCenter center={mapCenter} zoom={16} />

          {filteredCameras.map((camera) => (
            camera.lat && camera.lon && (
              <CameraMarker
                key={camera.id}
                camera={camera}
                icon={cameraIcon}
                onCameraClick={handleCameraClick}
                shouldOpenPopup={triggerPopup === camera.id}
              />
            )
          ))}
        </MapContainer>
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
        </div>
      )}
    </div>
  );
}

export default CameraMap;
