import { useState, useEffect } from 'react';

/**
 * Hook to detect when map is zoomed out enough to show Earth view
 * @param {object} map - Goong Map instance
 * @param {number} zoomThreshold - Zoom level threshold (default: 3)
 * @returns {boolean} showEarth - Whether to show Earth view
 */
export const useEarthView = (map, zoomThreshold = 3) => {
  const [showEarth, setShowEarth] = useState(false);

  useEffect(() => {
    if (!map) return;

    const handleZoom = () => {
      const currentZoom = map.getZoom();
      
      // Show Earth when zoom level is below threshold
      if (currentZoom <= zoomThreshold && !showEarth) {
        setShowEarth(true);
      } else if (currentZoom > zoomThreshold && showEarth) {
        setShowEarth(false);
      }
    };

    // Listen to zoom events
    map.on('zoom', handleZoom);
    map.on('zoomend', handleZoom);

    // Check initial zoom
    handleZoom();

    return () => {
      map.off('zoom', handleZoom);
      map.off('zoomend', handleZoom);
    };
  }, [map, zoomThreshold, showEarth]);

  return showEarth;
};

export default useEarthView;
