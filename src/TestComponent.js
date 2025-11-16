import React from 'react';

function TestComponent() {
  return (
    <div style={{ 
      padding: '40px', 
      textAlign: 'center',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <h1 style={{ color: '#0277BD', fontSize: '48px', marginBottom: '20px' }}>
        🗺️ Unified Mobility
      </h1>
      
      <p style={{ fontSize: '18px', color: '#666', marginBottom: '30px' }}>
        App is loading... If you see this, React is working!
      </p>

      <div style={{ 
        backgroundColor: '#fff', 
        padding: '20px', 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        maxWidth: '400px'
      }}>
        <h3 style={{ color: '#333', marginBottom: '15px' }}>Debug Info:</h3>
        <p style={{ textAlign: 'left', fontSize: '14px', color: '#555', lineHeight: '1.8' }}>
          ✅ React component rendering<br/>
          ✅ Router should be initializing<br/>
          ✅ Check browser console for errors (F12)<br/>
          <br/>
          If stuck: Possible issues:<br/>
          • Missing Router setup<br/>
          • Import path error<br/>
          • Circular dependency<br/>
          • Memory/performance issue
        </p>
      </div>

      <div style={{ marginTop: '40px', fontSize: '14px', color: '#999' }}>
        <p>Check console (F12 → Console tab) for detailed errors</p>
      </div>
    </div>
  );
}

export default TestComponent;
