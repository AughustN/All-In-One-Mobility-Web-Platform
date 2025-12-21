import React from 'react';
import './css/GoongMapStyleControl.css';

const STYLES = [
  { id: 'goong_map_web', name: ' Goong Map', icon: '' },
  { id: 'goong_light_v2', name: ' Light', icon: '' },
  { id: 'goong_map_dark', name: ' Dark', icon: '' },
  { id: 'navigation_day', name: ' Nav Day', icon: '' },
  { id: 'navigation_night', name: ' Nav Night', icon: '' },
];

function GoongMapStyleControl({ currentStyle, onStyleChange }) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="goong-style-control">
      <button 
        className="goong-style-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="Change map style"
      >
        <span className="layers-icon">🗺️</span>
      </button>

      {isOpen && (
        <div className="goong-style-menu">
          <div className="goong-style-header">Map Styles</div>
          {STYLES.map(style => (
            <button
              key={style.id}
              className={`goong-style-item ${currentStyle === style.id ? 'active' : ''}`}
              onClick={() => {
                onStyleChange(style.id);
                setIsOpen(false);
              }}
            >
              <span className="style-icon">{style.icon}</span>
              <span className="style-name">{style.name}</span>
              {currentStyle === style.id && <span className="check-icon">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default GoongMapStyleControl;
