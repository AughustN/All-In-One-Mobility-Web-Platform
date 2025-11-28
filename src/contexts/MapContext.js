import React, { createContext, useContext, useState, useEffect } from 'react';
import EarthGlobe from '../components/EarthGlobe';

const MapContext = createContext();

export const useMapContext = () => {
  const context = useContext(MapContext);
  if (!context) {
    console.warn('useMapContext used outside MapProvider - Earth Globe will not work');
    return { map: null, registerMap: () => {}, showEarth: false };
  }
  return context;
};

export const MapProvider = ({ children, zoomThreshold = 3 }) => {
  const [map, setMap] = useState(null);
  const [showEarth, setShowEarth] = useState(false);

  useEffect(() => {
    if (!map) return;

    const handleZoom = () => {
      const currentZoom = map.getZoom();
    //   console.log('🔍 Current zoom:', currentZoom, 'Threshold:', zoomThreshold);
      
      if (currentZoom <= zoomThreshold && !showEarth) {
        // console.log('🌍 Showing Earth!');
        setShowEarth(true);
      } else if (currentZoom > zoomThreshold && showEarth) {
        // console.log('🗺️ Hiding Earth!');
        setShowEarth(false);
      }
    };

    map.on('zoom', handleZoom);
    map.on('zoomend', handleZoom);
    handleZoom(); // Check initial zoom

    return () => {
      map.off('zoom', handleZoom);
      map.off('zoomend', handleZoom);
    };
  }, [map, zoomThreshold, showEarth]);

  const handleCloseEarth = () => {
    if (map) {
      console.log('🗺️ Flying to Ho Chi Minh City...');
      map.flyTo({ 
        center: [106.660172, 10.762622], // Ho Chi Minh City coordinates
        zoom: 3, 
        duration: 2000,
        easing: (t) => t * (2 - t)
      });
    }
  };

  const registerMap = (mapInstance) => {
    console.log('🗺️ Map registered:', mapInstance);
    setMap(mapInstance);
  };

  return (
    <MapContext.Provider value={{ map, registerMap, showEarth }}>
      {children}
      <EarthGlobe visible={showEarth} onClose={handleCloseEarth} />
    </MapContext.Provider>
  );
};

export default MapContext;
