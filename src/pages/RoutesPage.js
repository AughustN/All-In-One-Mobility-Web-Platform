import React, { useState, useCallback, useEffect } from 'react';
import {
    Box, Paper, IconButton, TextField, List,
    ListItem, ListItemIcon, ListItemText, Typography, Fab
} from '@material-ui/core';

import { makeStyles } from '@material-ui/core/styles';
import CloseIcon from '@material-ui/icons/Close';
import SearchIcon from '@material-ui/icons/Search';
import LocationOnIcon from '@material-ui/icons/LocationOn';
import MenuIcon from '@material-ui/icons/Menu';
import { useLocation } from 'react-router-dom';
import GoongMap from '../GoongMap';
import GoongMapStyleControl from '../GoongMapStyleControl';
import MyLocationControl from '../MyLocationControl';
import SearchBoxRoutes from '../SearchBoxRoutes';
import { saveLocation, saveRoute, getSavedLocations, getSavedRoutes, searchLocation, calculateRoute } from '../api';
import * as turf from '@turf/turf';
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
dayjs.extend(utc)
dayjs.extend(timezone)
const useStyles = makeStyles(theme => ({
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
    mapContainer: { width: '100%', height: '100%', position: 'relative', zIndex: 1 },
    searchBarContainer: {
        position: 'fixed',
        top: '70px',
        left: '100px',
        zIndex: 999,
        pointerEvents: 'none',
        [theme.breakpoints.down('sm')]: {
            left: '10px',
            right: '10px',
            top: '70px',
        },
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
    searchField: {
        width: '280px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '25px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        border: '2px solid rgba(33, 150, 243, 0.5)',
        backdropFilter: 'blur(12px)',
        pointerEvents: 'auto', // Input có thể click
        transition: 'all 0.3s ease',
        '& .MuiOutlinedInput-root': { 
            borderRadius: '25px',
            '&:hover': {
                borderColor: '#2196F3',
            },
            '&.Mui-focused': {
                backgroundColor: 'white',
                borderColor: '#2196F3',
                boxShadow: '0 6px 16px rgba(33, 150, 243, 0.3)',
                transform: 'translateY(-2px)',
            }
        },
        '& .MuiOutlinedInput-notchedOutline': {
            border: 'none',
        },
    },
    searchDropdown: {
        marginTop: '8px',
        backgroundColor: '#fff',
        borderRadius: '12px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
        maxHeight: '400px',
        overflow: 'auto',
        border: '2px solid rgba(33, 150, 243, 0.2)',
        pointerEvents: 'auto',
    },
    listItem: {
        cursor: 'pointer',
        borderBottom: '1px solid #f0f0f0',
        padding: '12px 16px',
        transition: 'background 0.2s ease',
        '&:hover': { backgroundColor: 'rgba(33, 150, 243, 0.08)' },
        '&:last-child': { borderBottom: 'none' },
    },
    sidebarContainer: {
        position: "fixed",
        top: 50,
        left: 0,
        height: "calc(100vh - 56px)",
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
    sidebarTitle: { fontSize: 18, fontWeight: "bold", color: "#0277BD" },
    sidebarContent: { 
        padding: "16px", 
        overflowY: "auto", 
        flexGrow: 1,
        maxHeight: 'calc(100vh - 70px)', // Fix scroll issue
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

function RoutesPage() {
    const classes = useStyles();
    const location = useLocation();

    const [filteredLocations, setFilteredLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [coords, setCoords] = useState([]);
    const [distance, setDistance] = useState(null);
    const [duration, setDuration] = useState(null);
    const [isNavigating, setIsNavigating] = useState(false);
    const [openModal, setOpenModal] = useState(window.innerWidth >= 960); // Open on desktop, closed on mobile
    const [showSearchDropdown, setShowSearchDropdown] = useState(false);
    const [searchInput, setSearchInput] = useState('');
    const [debounceText, setDebounceText] = useState('');
    const [selectPosition, setSelectPosition] = useState(null);
    const [travelMode, setTravelMode] = useState('car');
    const [routeType, setRouteType] = useState('fastest');
    const [errorMessage, setErrorMessage] = useState('');
    const [isSearchLocationSelected, setIsSearchLocationSelected] = useState(false);
    const [recentHistory, setRecentHistory] = useState({ locations: [], routes: [] });
    const [mapStyle, setMapStyle] = useState('goong_map_web');
    const [userLocation, setUserLocation] = useState(null);

    /** 🔍 Search input change with debounce */
    const handleSearchChange = (e) => {
        const value = e.target.value;
        setSearchInput(value);
        setDebounceText(value);
        setIsSearchLocationSelected(false); // Reset khi người dùng typing

        if (!value.trim()) {
            setShowSearchDropdown(false);
            setFilteredLocations([]);
        }
    };

    // Handle navigation from HistoryPage
    useEffect(() => {
        if (location.state?.location) {
            const loc = location.state.location;
            setSelectedLocation({
                name: loc.name,
                lat: loc.lat,
                lon: loc.lon
            });
            setSearchInput(loc.name);
            setOpenModal(true);
        } else if (location.state?.route) {
            const route = location.state.route;
            setSelectedLocation({
                name: route.start.name,
                lat: route.start.lat,
                lon: route.start.lon
            });
            setSearchInput(route.start.name);
            setSelectPosition({
                name: route.end.name,
                lat: route.end.lat,
                lon: route.end.lon
            });
            setOpenModal(true);
            
            // Auto calculate route
            setTimeout(async () => {
                try {
                    const data = await calculateRoute(
                        { lat: route.start.lat, lon: route.start.lon },
                        { lat: route.end.lat, lon: route.end.lon },
                        travelMode
                    );
                    setCoords(data.coords);
                    setDistance(data.distance_km);
                    setDuration(data.duration_min);
                } catch (err) {
                    console.error("Route error:", err);
                    setErrorMessage('Không thể tải tuyến đường');
                }
            }, 500);
        }
    }, [location.state, travelMode]);

    useEffect(() => {
        // Load history if logged in
        if (localStorage.getItem('token')) {
            Promise.all([getSavedLocations(), getSavedRoutes()])
                .then(([locs, routes]) => setRecentHistory({ locations: locs, routes: routes }))
                .catch(err => console.error("Failed to load history", err));
        }
    }, [openModal]); // Reload when sidebar opens

    // --- REAL-TIME NAVIGATION LOGIC ---
    useEffect(() => {
        if (!isNavigating || coords.length === 0) return;

        console.log("🚀 Bắt đầu chế độ dẫn đường Real-time...");
        const routeLine = turf.lineString(coords.map(c => [c.lon, c.lat]));

        const watchId = navigator.geolocation.watchPosition(
            (position) => {
                const rawLat = position.coords.latitude;
                const rawLng = position.coords.longitude;

                const rawPoint = turf.point([rawLng, rawLat]);
                const snapped = turf.nearestPointOnLine(routeLine, rawPoint);
                const distToRoute = turf.distance(rawPoint, snapped, { units: 'meters' });

                if (distToRoute > 40) {
                    // Lệch đường -> Hiển thị GPS thực
                    setUserLocation({ lat: rawLat, lon: rawLng });
                } else {
                    // Bám đường -> Hiển thị điểm Snap
                    const [snappedLng, snappedLat] = snapped.geometry.coordinates;
                    setUserLocation({ lat: snappedLat, lon: snappedLng });
                }
            },
            (err) => console.error("Lỗi GPS Navigation:", err),
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
        );

        return () => navigator.geolocation.clearWatch(watchId);
    }, [isNavigating, coords]);

    useEffect(() => {
        // Không tìm kiếm nếu đã chọn địa điểm
        if (isSearchLocationSelected) {
            return;
        }

        if (!debounceText.trim()) return;

        const timer = setTimeout(async () => {
            try {
                const data = await searchLocation(debounceText);
                setFilteredLocations(data);
                setShowSearchDropdown(true);

                // Hiển thị thông báo nếu không có kết quả
                if (data.length === 0) {
                    setErrorMessage('Không tìm thấy kết quả trong TP.HCM');
                } else {
                    setErrorMessage('');
                }
            } catch (err) {
                console.error("Search API Error:", err);
                setErrorMessage('Lỗi khi tìm kiếm');
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [debounceText, isSearchLocationSelected]);

    /** Khi chọn 1 địa điểm */
    const handleLocationSelect = (loc) => {
        const pos = loc.position;
        setSelectedLocation({
            name: loc.address.freeformAddress,
            lat: pos.lat,
            lon: pos.lon
        });
        setSearchInput(loc.address.freeformAddress);
        setShowSearchDropdown(false);
        setFilteredLocations([]); // Xóa kết quả
        setIsSearchLocationSelected(true); // Đánh dấu đã chọn
        setOpenModal(true);

        // Save location if logged in
        if (localStorage.getItem('token')) {
            saveLocation(loc.address.freeformAddress, pos.lat, pos.lon)
                .then(() => console.log("Location saved"))
                .catch(err => console.error("Failed to save location", err));
        }
    };

    /** 🛣 Tìm route bằng Flask /route */
    const handleSearch = useCallback(async (mode = 'car', type = 'fastest') => {
        if (!selectedLocation || !selectPosition) {
            console.log("Missing locations");
            return;
        }

        try {
            setErrorMessage('');
            const data = await calculateRoute(
                { lat: selectedLocation.lat, lon: selectedLocation.lon },
                { lat: selectPosition.lat, lon: selectPosition.lon },
                mode,
                type
            );

            setCoords(data.coords);
            setDistance(data.distance_km);
            setDuration(data.duration_min);

            // Logic bật/tắt dẫn đường
            if (selectedLocation.isGPS) {
                setIsNavigating(true);
                setUserLocation({
                    lat: selectedLocation.lat,
                    lon: selectedLocation.lon
                });
            } else {
                setIsNavigating(false);
                setUserLocation(null);
            }

            // Save route if logged in
            if (localStorage.getItem('token')) {
                saveRoute(
                    selectedLocation.name, selectedLocation.lat, selectedLocation.lon,
                    selectPosition.name, selectPosition.lat, selectPosition.lon
                ).then(() => console.log("Route saved"))
                    .catch(err => console.error("Failed to save route", err));
            }
        } catch (err) {
            console.error("Route API Error:", err);
            setErrorMessage('Không thể tìm đường đi');
        }
    }, [selectedLocation, selectPosition]);

    return (
        <Box className={classes.root}>
            {/* Open Sidebar Button (Mobile only, hidden when sidebar is open) */}
            {!openModal && (
                <Fab
                    className={classes.openSidebarButton}
                    onClick={() => setOpenModal(true)}
                    aria-label="open menu"
                >
                    <MenuIcon />
                </Fab>
            )}

            {/* Full Screen Map */}
            <Box className={classes.mapContainer}>
                <GoongMap
                    origin={selectedLocation}
                    destination={selectPosition}
                    coords={coords}
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
            </Box>

            {/* 🔍 Search Bar */}
            <Box className={classes.searchBarContainer}>
                <TextField
                    fullWidth
                    placeholder="Tìm kiếm địa điểm..."
                    variant="outlined"
                    size="small"
                    value={searchInput}
                    onChange={handleSearchChange}
                    onFocus={() => {
                        if (searchInput && !isSearchLocationSelected) {
                            setShowSearchDropdown(true);
                        }
                    }}
                    onBlur={() => {
                        // Đóng dropdown sau 200ms để có thời gian click vào item
                        setTimeout(() => {
                            setShowSearchDropdown(false);
                        }, 200);
                    }}
                    className={classes.searchField}
                    InputProps={{
                        startAdornment: <span style={{ marginRight: 8, fontSize: '18px' }}>🔍</span>
                    }}
                />

                {/* Dropdown Search */}
                {showSearchDropdown && filteredLocations.length > 0 && (
                    <Paper className={classes.searchDropdown}>
                        <List style={{ padding: 0 }}>
                            {filteredLocations.map((location, i) => (
                                <ListItem
                                    key={i}
                                    className={classes.listItem}
                                    onMouseDown={(e) => {
                                        e.preventDefault(); // Ngăn onBlur trigger
                                        handleLocationSelect(location);
                                    }}
                                >
                                    <ListItemIcon style={{ minWidth: 40 }}>
                                        <LocationOnIcon style={{ color: '#0277BD' }} />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={location.address.freeformAddress}
                                        secondary={location.poi?.name}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Paper>
                )}
            </Box>

            {/* Sidebar Routes */}
            <Box data-sidebar="container" className={`${classes.sidebarContainer} ${openModal ? "open" : "closed"}`}>
                <Box data-sidebar="header" className={classes.sidebarHeader}>
                    <Typography className={classes.sidebarTitle}>
                        {selectedLocation ? `Từ: ${selectedLocation.name}` : "Tìm đường"}
                    </Typography>
                    <IconButton
                        data-sidebar="toggle"
                        onClick={() => setOpenModal(!openModal)}
                        className={classes.toggleButton}
                    >
                        {openModal ? <CloseIcon /> : <SearchIcon />}
                    </IconButton>
                </Box>

                {openModal && (
                    <Box className={classes.sidebarContent}>
                        {/* Hiển thị thông báo lỗi */}
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

                        <SearchBoxRoutes
                            selectPosition={selectPosition}
                            setSelectPosition={setSelectPosition}
                            onSearch={handleSearch}
                            initialFrom={selectedLocation?.name || ""}
                            travelMode={travelMode}
                            setTravelMode={setTravelMode}
                            routeType={routeType}
                            setRouteType={setRouteType}
                            onFromLocationChange={(locationData) => {
                                setSelectedLocation(locationData);
                                setSearchInput(locationData.name);
                                if (!locationData.isGPS) setIsNavigating(false);
                            }}
                        />

                        {coords.length > 0 && distance !== null && duration !== null && (
                            <Paper style={{ marginTop: 16, padding: 12, backgroundColor: '#e3f2fd' }}>
                                <Typography><b>Khoảng cách:</b> {distance.toFixed(2)} km</Typography>
                                <Typography><b>Thời gian:</b> {duration.toFixed(1)} phút</Typography>
                            </Paper>
                        )}

                        {/* Recent History */}
                        {localStorage.getItem('token') && (
                            <Box style={{ marginTop: 24 }}>
                                <Typography variant="h6" style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8, color: '#0277BD' }}>
                                     Lịch sử gần đây
                                </Typography>

                                {recentHistory.locations.length > 0 && (
                                    <Box style={{ marginBottom: 16 }}>
                                        <Typography variant="subtitle2" style={{ fontWeight: 'bold', color: '#666' }}> Địa điểm</Typography>
                                        <List dense>
                                            {recentHistory.locations.slice(0, 3).map((loc, i) => (
                                                <ListItem key={i} button onClick={() => handleLocationSelect({
                                                    address: { freeformAddress: loc.name },
                                                    position: { lat: loc.lat, lon: loc.lng }
                                                })}>
                                                    <ListItemText primary={loc.name} secondary={dayjs.tz(loc.timestamp, "YYYY-MM-DD HH:mm:ss", "Asia/Ho_Chi_Minh")
                                                        .format("DD/MM/YYYY HH:mm:ss")} />
                                                </ListItem>
                                            ))}
                                        </List>
                                    </Box>
                                )}

                                {recentHistory.routes.length > 0 && (
                                    <Box>
                                        <Typography variant="subtitle2" style={{ fontWeight: 'bold', color: '#666' }}> Tuyến đường</Typography>
                                        <List dense>
                                            {recentHistory.routes.slice(0, 3).map((route, i) => (
                                                <ListItem 
                                                    key={i} 
                                                    button
                                                    onClick={async () => {
                                                        // Set start location
                                                        setSelectedLocation({
                                                            name: route.start_name,
                                                            lat: route.start_lat,
                                                            lon: route.start_lng
                                                        });
                                                        setSearchInput(route.start_name);
                                                        
                                                        // Set end location
                                                        setSelectPosition({
                                                            name: route.end_name,
                                                            lat: route.end_lat,
                                                            lon: route.end_lng
                                                        });
                                                        
                                                        // Calculate route
                                                        try {
                                                            const data = await calculateRoute(
                                                                { lat: route.start_lat, lon: route.start_lng },
                                                                { lat: route.end_lat, lon: route.end_lng },
                                                                travelMode
                                                            );
                                                            setCoords(data.coords);
                                                            setDistance(data.distance_km);
                                                            setDuration(data.duration_min);
                                                        } catch (err) {
                                                            console.error("Route error:", err);
                                                            setErrorMessage('Không thể tải lại tuyến đường');
                                                        }
                                                    }}
                                                >
                                                    <ListItemText
                                                        primary={`${route.start_name} ➝ ${route.end_name}`}
                                                        secondary={dayjs.tz(route.timestamp, "YYYY-MM-DD HH:mm:ss", "Asia/Ho_Chi_Minh")
                                                            .format("DD/MM/YYYY HH:mm:ss")}

                                                    />
                                                </ListItem>
                                            ))}
                                        </List>
                                    </Box>
                                )}
                            </Box>
                        )}
                    </Box>
                )}
            </Box>
        </Box>
    );
}

export default RoutesPage;