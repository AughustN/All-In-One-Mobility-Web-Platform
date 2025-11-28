import React, { useState } from 'react';
import { Button, Box } from '@material-ui/core';
import EarthGlobe from '../components/EarthGlobe';

export default function EarthTestPage() {
  const [showEarth, setShowEarth] = useState(false);

  return (
    <Box style={{ padding: 20 }}>
      <h1>Earth Globe Test Page</h1>
      
      <Button 
        variant="contained" 
        color="primary"
        onClick={() => setShowEarth(!showEarth)}
        style={{ marginBottom: 20 }}
      >
        {showEarth ? 'Hide Earth' : 'Show Earth'}
      </Button>

      <p>Current state: {showEarth ? 'Visible' : 'Hidden'}</p>

      <EarthGlobe 
        visible={showEarth} 
        onClose={() => setShowEarth(false)}
      />
    </Box>
  );
}
