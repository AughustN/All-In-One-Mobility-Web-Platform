import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Paper,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  InputAdornment,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import LocationOnIcon from '@material-ui/icons/LocationOn';
import MyLocationIcon from '@material-ui/icons/MyLocation';
import DirectionsBusIcon from '@material-ui/icons/DirectionsBus';
import GoongBusMap from '../GoongBusMap';
import { searchLocation, calculateBusRoute } from '../api';

const useStyles = makeStyles((theme) => ({
  root: {
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
    backgroundColor: '#f5f5f5',
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  mapContainer: {
    position: 'relative',
    zIndex: 1,
    [theme.breakpoints.down('sm')]: { height: '60%' },
    [theme.breakpoints.up('md')]: { height: '100%' },
  },
  panelContainer: {
    height: '40%',
    [theme.breakpoints.up('md')]: { height: '100%' },
    overflow: 'auto',
    backgroundColor: '#fff',
    borderLeft: `1px solid ${theme.palette.divider}`,
  },
  contentPaper: {
    marginBottom: theme.spacing(2),
    padding: theme.spacing(2),
  },
  title: {
    marginBottom: theme.spacing(2),
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#0277BD',
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
  walkingInput: {
    '& .MuiOutlinedInput-input': {
      padding: '12px 14px',
    },
  },
  findButton: {
    marginTop: theme.spacing(2),
    borderRadius: '12px',
    padding: theme.spacing(1.5),
    fontSize: '16px',
    fontWeight: 'bold',
  },
}));

export default function BusMapPage() {
  const classes = useStyles();

  // Search states
  const [origin_Search_input, setOrigin_Search_input] = useState('');
  const [destination_Search_input, setDestination_Search_input] = useState('');

  const [selectedOrigin, setSelectedOrigin] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(null);

  const [debounceOrigin, setDebounceOrigin] = useState('');
  const [debounceDestination, setDebounceDestination] = useState('');

  const [errorMessage, setErrorMessage] = useState('');
  const [filteredOrigins, setFilteredOrigins] = useState([]);
  const [filteredDestinations, setFilteredDestinations] = useState([]);
  
  const [bus_coords, setBus_coords] = useState([]);
  const [walkToBus_coords, setWalkToBus_coords] = useState(null);
  const [walkToDes_coords, setWalkToDes_coords] = useState(null);
  const [totalFare, setTotalFare] = useState(null);
  const [WorstCaseDuration, setWorstCaseDuration] = useState(null);
  const [BestCaseDuration, setBestCaseDuration] = useState(null);
  const [transfers, setTransfers] = useState(null);
  const [specialStopsName, setSpectialStopsName] = useState([]);
  const [unique_nameRoutes, setUnique_nameRoutes] = useState([]);
  const [unique_busNumbers, setUnique_busNumbers] = useState([]);

  const [showSearch_origin_Dropdown, setShowSearch_origin_Dropdown] = useState(false);
  const [showSearch_destination_Dropdown, setShowSearch_destination_Dropdown] = useState(false);

  const [isSearchingOrigin, setIsSearchingOrigin] = useState(false);
  const [isSearchingDestination, setIsSearchingDestination] = useState(false);
  const [isSearchingRoute, setIsSearchingRoute] = useState(false);
  const [maxWalkingDistance, setMaxWalkingDistance] = useState(400);

  // Debounce effect for origin

  const handleWalkingDistanceChange = (e) => {
    const value = e.target.value;
    setMaxWalkingDistance(value);
  };

  const handleOrginChange = (e) => {
    const value = e.target.value;
    setOrigin_Search_input(value);
    setDebounceOrigin(value);
    setIsSearchingOrigin(false); // reset when user typing

    if(!value.trim())
    {
      setShowSearch_origin_Dropdown(false);
      setFilteredOrigins([]);
    }
  };

  const handleDestinationChange = (e) => {
    const value = e.target.value;
    setDestination_Search_input(value);
    setDebounceDestination(value);
    setIsSearchingDestination(false); // reset when user typing

    if(!value.trim())
    {
      setShowSearch_destination_Dropdown(false);
      setFilteredDestinations([]);
    }
  };

  useEffect(() => {
    if(isSearchingOrigin) {
      return;
    } 

    if(!debounceOrigin.trim()) return;

    const timer = setTimeout(async() => {
      try {
        const data = await searchLocation(debounceOrigin);
        setFilteredOrigins(data);
        setShowSearch_origin_Dropdown(true);

        if (data.length === 0) {
          setErrorMessage('Không tìm thấy kết quả trong TP.HCM');
        } else {
          setErrorMessage('');
        }
      }
      catch (err)
      {
        console.error("Search API Error:", err);
        setErrorMessage('Lỗi khi tìm kiếm');
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [debounceOrigin, isSearchingOrigin]);

  useEffect(() => {
    if(isSearchingDestination) {
      return;
    } 

    if(!debounceDestination.trim()) return;

    const timer = setTimeout(async() => {
      try {
        const data = await searchLocation(debounceDestination);
        setFilteredDestinations(data);
        setShowSearch_destination_Dropdown(true);

        if (data.length === 0) {
          setErrorMessage('Không tìm thấy kết quả trong TP.HCM');
        } else {
          setErrorMessage('');
        }
      }
      catch (err)
      {
        console.error("Search API Error:", err);
        setErrorMessage('Lỗi khi tìm kiếm');
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [debounceDestination, isSearchingDestination]);

  const handleOriginSelect = (loc) => {
    const pos = loc.position;
    setSelectedOrigin({
      name: loc.address.freeformAddress,
      lat: pos.lat,
      lon: pos.lon
    });

    setOrigin_Search_input(loc.address.freeformAddress);
    setShowSearch_origin_Dropdown(false);
    setFilteredOrigins([]);
    setIsSearchingOrigin(true);
  }

  const handleDestinationSelect = (loc) => {
    const pos = loc.position;
    setSelectedDestination({
      name: loc.address.freeformAddress,
      lat: pos.lat,
      lon: pos.lon
    });

    setDestination_Search_input(loc.address.freeformAddress);
    setShowSearch_destination_Dropdown(false);
    setFilteredDestinations([]);
    setIsSearchingDestination(true);
  }

  // Searching busMap
  const handleSearch = useCallback(async() => {
    if(!selectedOrigin || !selectedDestination) {
      console.log("Missing locations");
      return;
    }

    try {
      setErrorMessage('');
      setTotalFare(null);
      setBestCaseDuration(null);
      setWorstCaseDuration(null);
      setTransfers(null);  
      setSpectialStopsName([])
      setUnique_nameRoutes([]);
      setUnique_busNumbers([]);
      setWalkToBus_coords(null);
      setWalkToDes_coords(null);
      setBus_coords([]);
      
      setIsSearchingRoute(true);

      const data = await calculateBusRoute(
        { lat: selectedOrigin.lat, lon: selectedOrigin.lon },
        { lat: selectedDestination.lat, lon: selectedDestination.lon },
        Number(maxWalkingDistance)
      );

      setTotalFare(data.fare_vnd);
      setBestCaseDuration(data.best_case_min);
      setWorstCaseDuration(data.worst_case_min);
      setTransfers(data.transfers);  
      setSpectialStopsName(data.specialStopsName || []);
      setUnique_nameRoutes(data.unique_nameRoutes || []);
      setUnique_busNumbers(data.unique_busNumbers || []);
      setWalkToBus_coords(data.walk_to_bus);
      setWalkToDes_coords(data.walkToDes_coords);
      setBus_coords(data.BusRoute_coords || []);

      setIsSearchingRoute(false);

      // save route if logged in
    } catch (err) {
      console.error("Route API Error:", err);
      setErrorMessage('Không thể tìm đường đi');
      setIsSearchingRoute(false);
    }

  }, [selectedOrigin, selectedDestination, maxWalkingDistance]);

  return (
    <Box className={classes.root}>
      <Box className={classes.mainContent}>
        <Grid container style={{ height: '100%' }} spacing={0}>
          {/* LEFT: Map section*/}
            <Grid item xs={12} md={7} className={classes.mapContainer}>
              {specialStopsName ? (
                <div style={{ width: "100%", height: "100vh" }}>
                  <GoongBusMap
                    origin={selectedOrigin}
                    destination={selectedDestination}
                    walkToBus_coords={walkToBus_coords}
                    walkToDes_coords={walkToDes_coords}
                    bus_coords={bus_coords}
                    unique_nameRoutes={unique_nameRoutes}
                    unique_busNumbers={unique_busNumbers}
                  />
                </div>   
              ) : (
                <Box
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  height="100%"
                  bgcolor="#f8fbff"
                  p={4}
                >
                  <DirectionsBusIcon style={{ fontSize: 80, color: '#0277BD', marginBottom: 16 }} />
                  <Typography variant="h5" align="center" color="textSecondary">
                    Nhập điểm đi và điểm đến để xem tuyến xe buýt
                  </Typography>
                  <Typography variant="body2" align="center" color="textSecondary" style={{ marginTop: 8 }}>
                    Chúng tôi sẽ gợi ý lộ trình nhanh nhất, rẻ nhất và ít chuyển tuyến nhất
                  </Typography>
                </Box>
              )}
            </Grid>

          {/* Right Panel */}
          <Grid item xs={12} md={5} className={classes.panelContainer}>
            <Paper style={{ height: '100%', overflow: 'auto' }}>
              <Box style={{ padding: 16 }}>
                <Box className={classes.title}>Bus Routes</Box>

                {/* Search Section */}
                <Paper className={classes.contentPaper} elevation={2}>
                  <Typography variant="h6" style={{ marginBottom: 16, fontWeight: 'bold' }}>
                    Tìm tuyến xe buýt
                  </Typography>

                  {/* Origin Input */}
                  <div className={classes.searchBox}>
                    <TextField
                      fullWidth
                      variant="outlined"
                      placeholder="Bạn đang ở đâu?"
                      value={origin_Search_input}
                      onChange={handleOrginChange}
                      onFocus={() => {
                        if(origin_Search_input && !isSearchingOrigin)
                        {
                          setShowSearch_origin_Dropdown(true);
                          // setShowSearch_destination_Dropdown(false); // not sure
                        }
                      }}
                      onBlur={() => {
                        // Đóng dropdown sau 200ms để có thời gian click vào item
                        setTimeout(() => {
                            setShowSearch_origin_Dropdown(false);
                        }, 200);
                      }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <MyLocationIcon color="primary" />
                          </InputAdornment>
                        ),
                      }}
                    />
                    {showSearch_origin_Dropdown && filteredOrigins.length > 0 && (
                      <Paper className={classes.dropdown}>
                        <List>
                          {filteredOrigins.map((loc, i) => (
                            <ListItem
                              key={i}
                              button
                              className={classes.listItem}
                              onMouseDown={(e) =>{
                                e.preventDefault();
                                handleOriginSelect(loc)
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
                      value={destination_Search_input}
                      onChange={handleDestinationChange}
                      onFocus={() => {
                        if(destination_Search_input && !isSearchingDestination)
                        {
                          setShowSearch_destination_Dropdown(true);
                          // setShowSearch_origin_Dropdown(false); // not sure
                        }
                      }}
                      onBlur={() => {
                        // Đóng dropdown sau 200ms để có thời gian click vào item
                        setTimeout(() => {
                            setShowSearch_destination_Dropdown(false);
                        }, 200);
                    }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <LocationOnIcon style={{ color: '#f44336' }} />
                          </InputAdornment>
                        ),
                      }}
                    />
                    {showSearch_destination_Dropdown && filteredDestinations.length > 0 && (
                      <Paper className={classes.dropdown}>
                        <List>
                          {filteredDestinations.map((loc, i) => (
                            <ListItem
                              key={i}
                              button
                              className={classes.listItem}
                              onMouseDown={(e) => {
                                e.preventDefault();
                                handleDestinationSelect(loc)
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
                    className={classes.walkingInput}
                    style={{ marginTop: 16 }}
                  />

                  {/* { {errorMessage && (
                    <Alert severity="warning" style={{ marginTop: 12 }}>
                      {errorMessage}
                    </Alert>
                  )}} */}

                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    size="large"
                    startIcon={<DirectionsBusIcon />}
                    className={classes.findButton}
                    disabled={!isSearchingDestination || !isSearchingOrigin || isSearchingRoute}
                    onClick={handleSearch}
                  >
                    Tìm Tuyến Xe Buýt
                  </Button>
                </Paper>

                {(BestCaseDuration && WorstCaseDuration) && (
                  <Paper className={classes.contentPaper} elevation={2}>
                    <Typography variant="h6" style={{ marginBottom: 12, fontWeight: 'bold', color: '#0277BD' }}>
                      Kết quả tốt nhất
                    </Typography>

                    <Typography><strong>Thời gian:</strong> {BestCaseDuration} - {WorstCaseDuration} phút</Typography>
                    <Typography><strong>Tổng tiền:</strong> {totalFare?.toLocaleString()}₫</Typography>
                    <Typography><strong>Số tuyến:</strong> {transfers?.toLocaleString()}</Typography>

                    {/* NEW: Print special stops */}
                    {specialStopsName && specialStopsName.length > 0 && (
                      <>
                        <Typography style={{ marginTop: 12, fontWeight: 'bold' }}>Các điểm đặc biệt:</Typography>
                        {specialStopsName.map((name, idx) => (
                          <Typography key={idx} style={{ marginLeft: 12 }}>
                            • {name}
                          </Typography>
                        ))}
                      </>
                    )}
                  </Paper>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}



