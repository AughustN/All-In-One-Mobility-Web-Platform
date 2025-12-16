import { useState, useEffect, useCallback } from 'react';
import {
  Box, Paper, IconButton, TextField, List, ListItem, ListItemIcon, 
  ListItemText, Typography, Button, InputAdornment, Fab
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import LocationOnIcon from '@material-ui/icons/LocationOn';
import MyLocationIcon from '@material-ui/icons/MyLocation';
import DirectionsBusIcon from '@material-ui/icons/DirectionsBus';
import CloseIcon from '@material-ui/icons/Close';
import MenuIcon from '@material-ui/icons/Menu';
import GoongBusMap from '../GoongBusMap';
import {colorPalette} from '../GoongBusMap';
import { searchLocation, calculateBusRoute } from '../api';
import { useLocation } from 'react-router-dom';
import MyLocationControl from '../MyLocationControl';
import GoongMapStyleControl from '../GoongMapStyleControl'

const useStyles = makeStyles((theme) => ({
  root: {
    display: 'flex',
    height: 'calc(100vh - 50px)',
    overflow: 'hidden',
    backgroundColor: '#f5f5f5',
    position: 'relative',
    [theme.breakpoints.down('sm')]: {
      height: 'calc(100vh - 56px)',
    },
  },
  mapContainer: { 
    width: '100%', 
    height: '100%', 
    position: 'relative', 
    zIndex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f8fbff',
  },
  openSidebarButton: {
    position: 'fixed',
    top: 140,
    left: 20,
    zIndex: 998,
    backgroundColor: '#6ac5faff',
    color: 'white',
    '&:hover': {
      backgroundColor: '#01579B',
    },
    [theme.breakpoints.up('md')]: {
      display: 'none',
    },
  },
  sidebarContainer: {
    position: "fixed",
    top: 50,
    left: 0,
    height: "calc(100vh - 50px)",
    width: 400,
    background: "#fff",
    zIndex: 999,
    boxShadow: "2px 0 16px rgba(0,0,0,0.2)",
    display: "flex",
    flexDirection: "column",
    transition: "transform 0.35s ease",
    [theme.breakpoints.down('sm')]: {
      width: '100%',
      maxWidth: '320px',
      height: "calc(100vh - 56px)",
      transform: 'translateX(-100%)',
      '&.open': {
        transform: 'translateX(0)',
      },
    },
  },
  sidebarHeader: {
    padding: "14px 16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #e0e0e0",
  },
  toggleButton: { 
    background: "#f2f5f7", 
    borderRadius: 8,
  },
  sidebarTitle: { 
    fontSize: 18, 
    fontWeight: "bold", 
    color: "#0277BD" 
  },
  sidebarContent: { 
    padding: "16px", 
    overflowY: "auto", 
    flexGrow: 1,
    maxHeight: 'calc(100vh - 70px)',
    '&::-webkit-scrollbar': {
      width: '8px',
    },
    '&::-webkit-scrollbar-track': {
      background: '#f1f1f1',
    },
    '&::-webkit-scrollbar-thumb': {
      background: '#888',
      borderRadius: '4px',
    },
    '&::-webkit-scrollbar-thumb:hover': {
      background: '#555',
    },
  },
  searchBox: {
    position: 'relative',
    marginBottom: theme.spacing(2),
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
    maxHeight: '300px',
    overflow: 'auto',
    zIndex: 10,
    border: '1px solid rgba(33,150,243,0.2)',
  },
  listItem: {
    cursor: 'pointer',
    padding: '12px 16px',
    borderBottom: '1px solid #f0f0f0',
    '&:hover': { backgroundColor: 'rgba(33,150,243,0.08)' },
  },
  "@global": {
    ".open": { 
      transform: "translateX(0)",
      [theme.breakpoints.up('md')]: {
        transform: "translateX(0)",
      },
    },
    ".closed": { 
      transform: "translateX(-85%)",
      [theme.breakpoints.down('sm')]: {
        transform: "translateX(-100%)",
      },
    },
  },
}));

export default function BusMapPage() {
  const classes = useStyles();

  // UI States
  const [openModal, setOpenModal] = useState(window.innerWidth >= 960);
  
  // Search states
  const [originSearchInput, setOriginSearchInput] = useState('');
  const [destinationSearchInput, setDestinationSearchInput] = useState('');

  const [selectedOrigin, setSelectedOrigin] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(null);

  const [debounceOrigin, setDebounceOrigin] = useState('');
  const [debounceDestination, setDebounceDestination] = useState('');

  const [filteredOrigins, setFilteredOrigins] = useState([]);
  const [filteredDestinations, setFilteredDestinations] = useState([]);

  const [showOriginDropdown, setShowOriginDropdown] = useState(false);
  const [showDestinationDropdown, setShowDestinationDropdown] = useState(false);

  const [isSearchingOrigin, setIsSearchingOrigin] = useState(false);
  const [isSearchingDestination, setIsSearchingDestination] = useState(false);
  const [isSearchingRoute, setIsSearchingRoute] = useState(false);
  
  // Route states
  const [bus_coords, setBus_coords] = useState([]);
  const [walk_coords, setWalk_coords] = useState([]);
  const [totalFare, setTotalFare] = useState(null);
  const [WorstCaseDuration, setWorstCaseDuration] = useState(null);
  const [BestCaseDuration, setBestCaseDuration] = useState(null);
  const [transfers, setTransfers] = useState(null);
  const [specialStopsName, setSpectialStopsName] = useState([]);
  const [unique_nameRoutes, setUnique_nameRoutes] = useState([]);
  const [unique_busNumbers, setUnique_busNumbers] = useState([]);
  const [maxWalkingDistance, setMaxWalkingDistance] = useState("400");

  const [errorMessage, setErrorMessage] = useState('');
  const [mapStyle, setMapStyle] = useState('goong_map_web');
  const [userLocation, setUserLocation] = useState(null);
  

  // Handle origin input change
  const handleOriginChange = (e) => {
    const value = e.target.value;
    setOriginSearchInput(value);
    setDebounceOrigin(value);
    setIsSearchingOrigin(false);

    if (!value.trim()) {
      setShowOriginDropdown(false);
      setFilteredOrigins([]);
    }
  };

  // Handle destination input change
  const handleDestinationChange = (e) => {
    const value = e.target.value;
    setDestinationSearchInput(value);
    setDebounceDestination(value);
    setIsSearchingDestination(false);

    if (!value.trim()) {
      setShowDestinationDropdown(false);
      setFilteredDestinations([]);
    }
  };


  useEffect(() => {
    if (userLocation) {
      const nameCoord = `${userLocation.lat}, ${userLocation.lon}`;
      setSelectedOrigin({
        name: nameCoord,
        lat: userLocation.lat,
        lon: userLocation.lon
      });
      setOriginSearchInput(nameCoord);
      setIsSearchingOrigin(true);
      setOpenModal(true);
    }
    
  }, [userLocation]);

  // Debounce search for origin
  useEffect(() => {
    if (isSearchingOrigin || !debounceOrigin.trim()) return;

    const timer = setTimeout(async () => {
      try {
        const data = await searchLocation(debounceOrigin);
        setFilteredOrigins(data);
        setShowOriginDropdown(true);
        setErrorMessage(data.length === 0 ? 'Không tìm thấy kết quả' : '');
      } catch (err) {
        console.error("Search API Error:", err);
        setErrorMessage('Lỗi khi tìm kiếm');
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [debounceOrigin, isSearchingOrigin]);

  // Debounce search for destination
  useEffect(() => {
    if (isSearchingDestination || !debounceDestination.trim()) return;

    const timer = setTimeout(async () => {
      try {
        const data = await searchLocation(debounceDestination);
        setFilteredDestinations(data);
        setShowDestinationDropdown(true);
        setErrorMessage(data.length === 0 ? 'Không tìm thấy kết quả' : '');
      } catch (err) {
        console.error("Search API Error:", err);
        setErrorMessage('Lỗi khi tìm kiếm');
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [debounceDestination, isSearchingDestination]);

  // Handle origin selection
  const handleOriginSelect = (loc) => {
    const pos = loc.position;
    setSelectedOrigin({
      name: loc.address.freeformAddress,
      lat: pos.lat,
      lon: pos.lon
    });
    setOriginSearchInput(loc.address.freeformAddress);
    setShowOriginDropdown(false);
    setFilteredOrigins([]);
    setIsSearchingOrigin(true);

    setTotalFare(null);
    setBestCaseDuration(null);
    setWorstCaseDuration(null);
    setTransfers(null);  
    setSpectialStopsName([])
    setUnique_nameRoutes([]);
    setUnique_busNumbers([]);
    setWalk_coords([]);;
    setBus_coords([]);
  };

  // Handle destination selection
  const handleDestinationSelect = (loc) => {
    const pos = loc.position;
    setSelectedDestination({
      name: loc.address.freeformAddress,
      lat: pos.lat,
      lon: pos.lon
    });
    setDestinationSearchInput(loc.address.freeformAddress);
    setShowDestinationDropdown(false);
    setFilteredDestinations([]);
    setIsSearchingDestination(true);

    setTotalFare(null);
    setBestCaseDuration(null);
    setWorstCaseDuration(null);
    setTransfers(null);  
    setSpectialStopsName([])
    setUnique_nameRoutes([]);
    setUnique_busNumbers([]);
    setWalk_coords([]);;
    setBus_coords([]);
  };

  // Handle walking distance change
  const handleWalkingDistanceChange = (e) => {
    setMaxWalkingDistance(e.target.value);
  };

  // Search bus route
  const handleSearch = useCallback(async () => {
    if (!selectedOrigin || !selectedDestination) {
      setErrorMessage('Vui lòng chọn điểm đi và điểm đến');
      return;
    }

    try {

      setIsSearchingRoute(true);

      setErrorMessage('');
      setTotalFare(null);
      setBestCaseDuration(null);
      setWorstCaseDuration(null);
      setTransfers(null);  
      setSpectialStopsName([])
      setUnique_nameRoutes([]);
      setUnique_busNumbers([]);
      setWalk_coords([]);;
      setBus_coords([]);
      
      const walkingDistance = maxWalkingDistance === "" ? null : Number(maxWalkingDistance);

      const data = await calculateBusRoute(
        { lat: selectedOrigin.lat, lon: selectedOrigin.lon },
        { lat: selectedDestination.lat, lon: selectedDestination.lon },
        walkingDistance
      );

      setTotalFare(data.fare_vnd);
      setBestCaseDuration(data.best_case_min);
      setWorstCaseDuration(data.worst_case_min);
      setTransfers(data.transfers);  
      setSpectialStopsName(data.specialStopsName || []);
      setUnique_nameRoutes(data.unique_nameRoutes || []);
      setUnique_busNumbers(data.unique_BusNumbers || []);
      setWalk_coords(data.walk_coords);
      setBus_coords(data.BusRoute_coords || []);

      console.log("best case: ", BestCaseDuration)
      console.log("worst case: ", WorstCaseDuration)

      setIsSearchingRoute(false);
    } catch (err) {
      console.error("Route API Error:", err);
      setErrorMessage('Không thể tìm tuyến xe buýt');
      setIsSearchingRoute(false);
    }
  }, [selectedOrigin, selectedDestination, maxWalkingDistance]);

  return (
    <Box className={classes.root}>
      {/* Open Sidebar Button (Mobile only) */}
      {!openModal && (
        <Fab
          className={classes.openSidebarButton}
          onClick={() => setOpenModal(true)}
          aria-label="open menu"
        >
          <MenuIcon />
        </Fab>
      )}

      {/* Map Container */}
      <Box className={classes.mapContainer}>
          <GoongBusMap
            origin={selectedOrigin}
            destination={selectedDestination}
            walk_coords={walk_coords}
            bus_coords={bus_coords}
              style={mapStyle}
            userLocation={userLocation}
          />
          <MyLocationControl
            onLocationFound={(location) => {
            console.log('MyLocationControl -> onLocationFound', location);
            setUserLocation(location);
            }}
          />
          <GoongMapStyleControl
            currentStyle={mapStyle}
            onStyleChange={setMapStyle}
          />
      </Box>

      {/* Sidebar */}
      <Box data-sidebar="container" className={`${classes.sidebarContainer} ${openModal ? "open" : "closed"}`}>
        <Box data-sidebar="header" className={classes.sidebarHeader}>
          <Typography className={classes.sidebarTitle}>
            Tìm Tuyến Xe Buýt
          </Typography>
          <IconButton
            data-sidebar="toggle"
            onClick={() => setOpenModal(!openModal)}
            className={classes.toggleButton}
          >
            {openModal ? <CloseIcon /> : <DirectionsBusIcon />}
          </IconButton>
        </Box>

        {openModal && (
          <Box className={classes.sidebarContent}>
            {/* Error Message */}
            {errorMessage && (
              <Paper style={{
                marginBottom: 16,
                padding: 12,
                backgroundColor: '#ffebee',
                border: '1px solid #ef5350'
              }}>
                <Typography style={{ color: '#c62828', fontSize: 14 }}>
                  ⚠️ {errorMessage}
                </Typography>
              </Paper>
            )}

            {/* Origin Input */}
            <div className={classes.searchBox}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Bạn đang ở đâu?"
                value={originSearchInput}
                onChange={handleOriginChange}
                onFocus={() => {
                  if (originSearchInput && !isSearchingOrigin) {
                    setShowOriginDropdown(true);
                  }
                }}
                onBlur={() => {
                  setTimeout(() => setShowOriginDropdown(false), 200);
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <MyLocationIcon color="primary" />
                    </InputAdornment>
                  ),
                }}
              />
              {showOriginDropdown && filteredOrigins.length > 0 && (
                <Paper className={classes.dropdown}>
                  <List>
                    {filteredOrigins.map((loc, i) => (
                      <ListItem
                        key={i}
                        button
                        className={classes.listItem}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          handleOriginSelect(loc);
                        }}
                      >
                        <ListItemIcon>
                          <LocationOnIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={loc.address.freeformAddress}
                          secondary={loc.poi?.name || 'Địa điểm'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              )}
            </div>

            {/* Destination Input */}
            <div className={classes.searchBox}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Bạn muốn đi đâu?"
                value={destinationSearchInput}
                onChange={handleDestinationChange}
                onFocus={() => {
                  if (destinationSearchInput && !isSearchingDestination) {
                    setShowDestinationDropdown(true);
                  }
                }}
                onBlur={() => {
                  setTimeout(() => setShowDestinationDropdown(false), 200);
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LocationOnIcon style={{ color: '#f44336' }} />
                    </InputAdornment>
                  ),
                }}
              />
              {showDestinationDropdown && filteredDestinations.length > 0 && (
                <Paper className={classes.dropdown}>
                  <List>
                    {filteredDestinations.map((loc, i) => (
                      <ListItem
                        key={i}
                        button
                        className={classes.listItem}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          handleDestinationSelect(loc);
                        }}
                      >
                        <ListItemIcon>
                          <LocationOnIcon color="error" />
                        </ListItemIcon>
                        <ListItemText
                          primary={loc.address.freeformAddress}
                          secondary={loc.poi?.name || 'Địa điểm'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              )}
            </div>

            {/* Max Walking Distance */}
            <TextField
              fullWidth
              label="Khoảng cách đi bộ tối đa"
              type="number"
              value={maxWalkingDistance}
              onChange={handleWalkingDistanceChange}
              InputProps={{
                endAdornment: <InputAdornment position="end">m</InputAdornment>,
                inputProps: { min: 50, max: 2000, step: 50 },
              }}
              style={{ marginBottom: 16 }}
            />

            {/* Search Button */}
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              startIcon={<DirectionsBusIcon />}
              disabled={!isSearchingDestination || !isSearchingOrigin || isSearchingRoute}
              onClick={handleSearch}
              style={{
                borderRadius: 12,
                padding: '12px',
                fontSize: 16,
                fontWeight: 'bold',
                marginBottom: 16,
              }}
            >
              {isSearchingRoute ? 'Đang tìm...' : 'Tìm Tuyến Xe Buýt'}
            </Button>

            {/* Results */}
            {(BestCaseDuration && WorstCaseDuration) && (
              <Paper style={{ padding: 16, backgroundColor: '#e3f2fd', marginTop: 16 }}>
                <Typography variant="h6" style={{ marginBottom: 12, fontWeight: 'bold', color: '#0277BD' }}>
                  Kết quả tốt nhất
                </Typography>
                <Typography><strong>Thời gian:</strong> {BestCaseDuration} - {WorstCaseDuration} phút</Typography>
                <Typography><strong>Tổng tiền:</strong> {totalFare?.toLocaleString()}₫</Typography>
                <Typography><strong>Số tuyến:</strong> {transfers}</Typography>

                {specialStopsName && specialStopsName.length > 0 && (
                  <>
                    <Typography style={{ marginTop: 12, fontWeight: 'bold' }}>Các trạm dừng đặc biệt lưu ý:</Typography>
                    {specialStopsName.map((name, idx) => (
                      <Typography key={idx} style={{ marginLeft: 12 }}>
                        • {name}
                      </Typography>
                    ))}
                  </>
                )}
                {/* Beautiful Bus Route Legend – matches the map exactly */}
                {unique_busNumbers.length > 0 && unique_busNumbers.length > 0 && (
                  <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #bbdefb' }}>
                    <Typography style={{ fontWeight: 'bold', marginBottom: 10, color: '#01579b' }}>
                      Tuyến xe buýt:
                    </Typography>
                    {(() => {
                      let k = 0; // ← counter for NON-walk routes only

                      return unique_busNumbers.map((busNum, i) => {
                        if (busNum !== "walk") {
                          const color = colorPalette[k % colorPalette.length];
                          k++; // increment only for real bus routes

                          const routeName = unique_nameRoutes[i] || '';

                          return (
                            <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', mb: 1.5 }}>
                              {/* Colored square */}
                              <Box
                                sx={{
                                  width: 18,
                                  height: 18,
                                  backgroundColor: color,
                                  borderRadius: '6px',
                                  mr: 1.5,
                                  mt: 0.4,
                                  flexShrink: 0,
                                  border: '2px solid white',
                                  boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                                }}
                              />

                              {/* Bus number + route name */}
                              <Box>
                                <Typography
                                  style={{
                                    fontWeight: 700,
                                    fontSize: '15px',
                                    color: color,
                                  }}
                                >
                                  Bus {busNum}
                                </Typography>

                                <Typography
                                  style={{
                                    fontSize: '13.5px',
                                    color: '#333',
                                    lineHeight: 1.4,
                                  }}
                                >
                                  {routeName.replace(/ - /g, ' → ').replace(/ -> /g, ' → ')}
                                </Typography>
                              </Box>
                            </Box>
                          );
                        }

                        // If it's "walk", return nothing
                        return null;
                      });
                    })()}
                  </Box>
                )}
              </Paper>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
}
