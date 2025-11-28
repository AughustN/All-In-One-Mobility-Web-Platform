import React, { useState, useCallback, useEffect } from 'react';
import {
    Box, Paper, IconButton, Typography, Fab
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
import {saveRoute, getSavedLocations, getSavedRoutes, searchLocation, calculateRoute } from '../api';
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
        pointerEvents: 'auto',
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
    toggleButton: { background: "#f2f5f7", borderRadius: 8 },
    sidebarTitle: { fontSize: 18, fontWeight: "bold", color: "#0277BD" },
    sidebarContent: { 
        padding: "16px", 
        overflowY: "auto", 
        flexGrow: 1,
        maxHeight: 'calc(100vh - 70px)',
    },
    "@global": {
        ".open": { 
            transform: "translateX(0)",
            [theme.breakpoints.up('md')]: { transform: "translateX(0)" },
        },
        ".closed": { 
            transform: "translateX(-85%)",
            [theme.breakpoints.down('sm')]: { transform: "translateX(-100%)" },
        },
    },
}));

function RoutesPage() {
    const classes = useStyles();
    const location = useLocation();

    // State
    const [filteredLocations, setFilteredLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null); // Điểm ĐI
    const [selectPosition, setSelectPosition] = useState(null);     // Điểm ĐẾN (Search Bar sẽ update cái này)
    
    const [coords, setCoords] = useState([]);
    const [distance, setDistance] = useState(null);
    const [duration, setDuration] = useState(null);
    const [isNavigating, setIsNavigating] = useState(false);
    const [userLocation, setUserLocation] = useState(null);

    const [openModal, setOpenModal] = useState(window.innerWidth >= 960);
    const [showSearchDropdown, setShowSearchDropdown] = useState(false);
    const [searchInput, setSearchInput] = useState('');
    const [debounceText, setDebounceText] = useState('');
    const [travelMode, setTravelMode] = useState('car');
    const [routeType, setRouteType] = useState('fastest');
    const [errorMessage, setErrorMessage] = useState('');
    const [isSearchLocationSelected, setIsSearchLocationSelected] = useState(false);
    const [recentHistory, setRecentHistory] = useState({ locations: [], routes: [] });
    const [mapStyle, setMapStyle] = useState('goong_map_web');

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

    // --- NAVIGATION LOGIC ---
    useEffect(() => {
        if (!isNavigating || coords.length === 0) return;

        console.log("🚀 Bắt đầu chế độ dẫn đường Real-time...");
        const routeLine = turf.lineString(coords.map(c => [c.lon, c.lat]));

        const watchId = navigator.geolocation.watchPosition(
            (position) => {
                const rawLat = position.coords.latitude;
                const rawLng = position.coords.longitude;
                // Bỏ lấy heading vì bạn không muốn xoay map
                // const rawHeading = position.coords.heading; 

                const rawPoint = turf.point([rawLng, rawLat]);
                const snapped = turf.nearestPointOnLine(routeLine, rawPoint);
                const distToRoute = turf.distance(rawPoint, snapped, { units: 'meters' });

                if (distToRoute > 40) { 
                    // Lệch đường -> Hiện GPS thô
                    setUserLocation({ lat: rawLat, lon: rawLng });
                } else {
                    // Bám đường -> Hiện điểm Snap
                    const [snappedLng, snappedLat] = snapped.geometry.coordinates;
                    setUserLocation({ lat: snappedLat, lon: snappedLng });
                }
            },
            (err) => console.error("Lỗi GPS Navigation:", err),
            { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
        );

        return () => navigator.geolocation.clearWatch(watchId);
    }, [isNavigating, coords]);

    // Debounce API Call
    useEffect(() => {
        if (isSearchLocationSelected || !debounceText.trim()) return;
        const timer = setTimeout(async () => {
            try {
                const data = await searchLocation(debounceText);
                setFilteredLocations(data);
                setShowSearchDropdown(true);
                if (data.length === 0) setErrorMessage('Không tìm thấy kết quả');
                else setErrorMessage('');
            } catch (err) {
                setErrorMessage('Lỗi khi tìm kiếm');
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [debounceText, isSearchLocationSelected]);

    // --- TÍNH TOÁN TUYẾN ĐƯỜNG ---
    const handleSearch = useCallback(async (mode = 'car', routeType = 'fastest') => {
        if (!selectedLocation || !selectPosition) return;

        try {
            setErrorMessage('');
            const data = await calculateRoute(
                { lat: selectedLocation.lat, lon: selectedLocation.lon },
                { lat: selectPosition.lat, lon: selectPosition.lon },
                mode,
                routeType
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
                    // Không truyền bearing để map không xoay
                });
            } else {
                setIsNavigating(false);
                setUserLocation(null); 
            }

            if (localStorage.getItem('token')) {
                saveRoute(
                    selectedLocation.name, selectedLocation.lat, selectedLocation.lon,
                    selectPosition.name, selectPosition.lat, selectPosition.lon
                ).catch(console.error);
            }
        } catch (err) {
            setErrorMessage('Không thể tìm đường đi');
        }
    }, [selectedLocation, selectPosition]);

    return (
        <Box className={classes.root}>
            {!openModal && (
                <Fab className={classes.openSidebarButton} onClick={() => setOpenModal(true)}>
                    <MenuIcon />
                </Fab>
            )}

            <Box className={classes.mapContainer}>
                {/* Truyền cả 2 điểm vào map để hiển thị Marker */}
                <GoongMap
                    origin={selectedLocation}     // Marker điểm đầu
                    destination={selectPosition}  // Marker điểm cuối
                    coords={coords}
                    style={mapStyle}
                    userLocation={userLocation} 
                />
                
                <MyLocationControl onLocationFound={(loc) => setUserLocation(loc)} />
                <GoongMapStyleControl currentStyle={mapStyle} onStyleChange={setMapStyle} />
            </Box>

            {/* SIDEBAR */}
            <Box className={`${classes.sidebarContainer} ${openModal ? "open" : "closed"}`}>
                <Box className={classes.sidebarHeader}>
                    <Typography className={classes.sidebarTitle}>
                        {"Tìm đường"}
                    </Typography>
                    <IconButton onClick={() => setOpenModal(!openModal)} className={classes.toggleButton}>
                        {openModal ? <CloseIcon /> : <SearchIcon />}
                    </IconButton>
                </Box>

                {openModal && (
                    <Box className={classes.sidebarContent}>
                        {errorMessage && (
                            <Paper style={{ marginBottom: 16, padding: 12, backgroundColor: '#ffebee', border: '1px solid #ef5350' }}>
                                <Typography style={{ color: '#c62828', fontSize: 14 }}>⚠️ {errorMessage}</Typography>
                            </Paper>
                        )}

                        <SearchBoxRoutes
                            selectPosition={selectPosition}
                            setSelectPosition={setSelectPosition} // Sidebar cũng cập nhật được Điểm đến
                            onSearch={handleSearch}
                            initialFrom={selectedLocation?.name || ""}
                            travelMode={travelMode}
                            setTravelMode={setTravelMode}
                            routeType={routeType}
                            setRouteType={setRouteType}
                            onFromLocationChange={(loc) => {
                                setSelectedLocation(loc); // Update điểm ĐI từ sidebar
                                if (!loc.isGPS) setIsNavigating(false);
                            }}
                        />
                        
                        {/* Kết quả tìm đường */}
                        {coords.length > 0 && distance !== null && duration !== null && (
                            <Paper style={{ marginTop: 16, padding: 12, backgroundColor: '#e3f2fd' }}>
                                <Typography><b>Khoảng cách:</b> {distance.toFixed(2)} km</Typography>
                                <Typography><b>Thời gian:</b> {duration.toFixed(1)} phút</Typography>
                            </Paper>
                        )}
                        
                        {/* ... (Phần History giữ nguyên) ... */}
                    </Box>
                )}
            </Box>
        </Box>
    );
}

export default RoutesPage;