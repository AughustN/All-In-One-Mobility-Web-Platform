import React, { useState } from 'react';
import EarthGlobe from './EarthGlobe';
import { useEarthView } from '../hooks/useEarthView';

/**
 * Higher-Order Component to add Earth Globe to any map component
 * @param {Component} WrappedComponent - Map component to wrap
 * @param {number} zoomThreshold - Zoom level to trigger Earth view (default: 3)
 */
const withEarthGlobe = (WrappedComponent, zoomThreshold = 3) => {
  return function WithEarthGlobeComponent(props) {
    const [map, setMap] = useState(null);
    const showEarth = useEarthView(map, zoomThreshold);

    const handleMapReady = (mapInstance) => {
      setMap(mapInstance);
      // Call original onMapReady if exists
      if (props.onMapReady) {
        props.onMapReady(mapInstance);
      }
    };

    const handleCloseEarth = () => {
      if (map) {
        map.flyTo({ 
          zoom: 12, 
          duration: 2000,
          easing: (t) => t * (2 - t) // Ease out
        });
      }
    };

    return (
      <>
        <WrappedComponent 
          {...props} 
          onMapReady={handleMapReady}
          mapInstance={map}
        />
        <EarthGlobe 
          visible={showEarth} 
          onClose={handleCloseEarth}
        />
      </>
    );
  };
};

export default withEarthGlobe;
