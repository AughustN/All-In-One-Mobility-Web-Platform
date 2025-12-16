import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
    Box, Paper, IconButton, TextField, List,
    ListItem, ListItemIcon, ListItemText, Typography, Fab,
} from '@material-ui/core';

import { makeStyles } from '@material-ui/core/styles';
import CloseIcon from '@material-ui/icons/Close';
import SearchIcon from '@material-ui/icons/Search';
import LocationOnIcon from '@material-ui/icons/LocationOn';
import MenuIcon from '@material-ui/icons/Menu';
import { useLocation } from 'react-router-dom';
import cameraLocations from '../camera_locations.json';
import GoongMap from '../GoongMap';
import GoongMapStyleControl from '../GoongMapStyleControl';
import MyLocationControl from '../MyLocationControl';
import SearchBoxRoutes from '../SearchBoxRoutes';
import '../css/CameraMap.css';
import { saveLocation, saveRoute, getSavedLocations, getSavedRoutes, searchLocation, calculateRoute, detectRouteCameras, getCongestionGeoJSON, fetchCameraImages } from "../api";
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
        width: '100%',
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

// ============================
// Helper to get color hex from level   
// ============================
const BASE_COLOR = "#0277BD";
const GREEN_HEX = "#00C851";
const YELLOW_HEX = "#ffbb33";
const RED_HEX = "#ff4444";

// Haversine distance in meters
function haversineMeters(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const toRad = d => (d * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) *
        Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// simple centroid of first ring of a Polygon
function polygonCentroid(coords) {
    // coords: [ [ [lon, lat], ... ] ]
    const ring = coords?.[0];
    if (!ring || ring.length === 0) return null;
    let sumLat = 0, sumLon = 0;
    ring.forEach(([lon, lat]) => {
        sumLat += lat;
        sumLon += lon;
    });
    return {
        lat: sumLat / ring.length,
        lon: sumLon / ring.length,
    };
}

function severityFromColor(hex) {
    if (!hex) return 0;
    const c = hex.toLowerCase();

    // ✅ green = 0 → handled as base color
    if (c === GREEN_HEX.toLowerCase()) return 0;

    if (c === YELLOW_HEX.toLowerCase()) return 1; // medium
    if (c === RED_HEX.toLowerCase()) return 2; // worst
    return 0;
}

// build colored route segments as GeoJSON FeatureCollection
function buildColoredRouteGeoJSON(routeCoords, congestionGeoJSON) {
    if (!routeCoords || routeCoords.length < 2 || !congestionGeoJSON?.features) {
        return null;
    }

    // precompute segment centroids + colors from polygons
    const segs = congestionGeoJSON.features
        .map(f => {
            const color = f.properties?.congestion_color;
            const geom = f.geometry;
            if (!geom || geom.type !== "Polygon") return null;
            const centroid = polygonCentroid(geom.coordinates);
            if (!centroid || !color) return null;
            return { ...centroid, color, severity: severityFromColor(color) };
        })
        .filter(Boolean);

    if (segs.length === 0) {
        return null;
    }

    const MAX_DIST = 100; // meters
    const features = [];

    // helper to decide color for midpoint
    function colorForPoint(lat, lon) {
        let bestSeverity = 0;
        let bestColor = null;

        for (const s of segs) {
            const d = haversineMeters(lat, lon, s.lat, s.lon);
            if (d <= MAX_DIST && s.severity >= bestSeverity) {
                bestSeverity = s.severity;
                bestColor = s.color;
            }
        }

        if (bestSeverity == 0) {
            return BASE_COLOR;
        }

        // no nearby segment → keep base color
        return bestColor || BASE_COLOR;
    }

    // iterate segments, group consecutive with same color
    let currentColor = null;
    let currentCoords = [];

    for (let i = 0; i < routeCoords.length - 1; i++) {
        const p1 = routeCoords[i];
        const p2 = routeCoords[i + 1];

        const midLat = (p1.lat + p2.lat) / 2;
        const midLon = (p1.lon + p2.lon) / 2;

        const segColor = colorForPoint(midLat, midLon);

        if (!currentColor) {
            // start first segment
            currentColor = segColor;
            currentCoords = [[p1.lon, p1.lat], [p2.lon, p2.lat]];
        } else if (segColor === currentColor) {
            // same color, extend line
            currentCoords.push([p2.lon, p2.lat]);
        } else {
            // color changed → push feature and start new one
            features.push({
                type: "Feature",
                properties: { color: currentColor },
                geometry: {
                    type: "LineString",
                    coordinates: currentCoords,
                },
            });

            currentColor = segColor;
            currentCoords = [[p1.lon, p1.lat], [p2.lon, p2.lat]];
        }
    }

    // push last feature
    if (currentCoords.length >= 2) {
        features.push({
            type: "Feature",
            properties: { color: currentColor },
            geometry: {
                type: "LineString",
                coordinates: currentCoords,
            },
        });
    }

    return {
        type: "FeatureCollection",
        features,
    };
}

function RoutesPage() {
    const classes = useStyles();
    const location = useLocation();

    const [filteredLocations, setFilteredLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [coords, setCoords] = useState([]);
    const [distance, setDistance] = useState(null);
    const [duration, setDuration] = useState(null);
    const [openModal, setOpenModal] = useState(window.innerWidth >= 960); // Open on desktop, closed on mobile
    const [showSearchDropdown, setShowSearchDropdown] = useState(false);
    const [searchInput, setSearchInput] = useState('');
    const [debounceText, setDebounceText] = useState('');
    const [selectPosition, setSelectPosition] = useState(null);
    const [travelMode, setTravelMode] = useState('car');

    const [errorMessage, setErrorMessage] = useState('');
    const [isSearchingRoute, setIsSearchingRoute] = useState(false);
    const [isSearchLocationSelected, setIsSearchLocationSelected] = useState(false);


    const [recentHistory, setRecentHistory] = useState({ locations: [], routes: [] });
    const [mapStyle, setMapStyle] = useState('goong_map_web');
    const [userLocation, setUserLocation] = useState(null);

    // Camera states
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [searchMode, setSearchMode] = useState('location'); // 'location' or 'camera'
    const [cameraSearchTerm, setCameraSearchTerm] = useState('');
    const [filteredCameras, setFilteredCameras] = useState([]);

    // Detect states
    const [routeCameras, setRouteCameras] = useState([]);
    const [congestionGeoJSON, setCongestionGeoJSON] = useState(null);
    const [coloredRouteGeoJSON, setColoredRouteGeoJSON] = useState(null);

    // Convert camera locations to array
    const cameras = useMemo(() => {
        return Object.entries(cameraLocations)
            .filter(([, data]) => data.lat !== null && data.lon !== null)
            .map(([id, data]) => ({
                id,
                ...data
            }));
    }, []);

    // Reset route outputs
    const resetRouteResults = useCallback(() => {
        setCoords([]);
        setDistance(null);
        setDuration(null);
        setRouteCameras([]);
        setSelectedCamera(null);
        setCongestionGeoJSON(null);
        setColoredRouteGeoJSON(null);
    }, []);

    // Wrap setSelectPosition to also reset route results
    const setSelectPositionWithReset = useCallback((next) => {
        setSelectPosition(next);
        resetRouteResults();
    }, [resetRouteResults]);


    const runRoutePipeline = useCallback(
        async (start, end, mode, errorMsg = 'Không thể tìm đường đi') => {
            if (!start || !end) return null;
            try {
                setIsSearchingRoute(true);
                setErrorMessage('');

                const data = await calculateRoute(
                    { lat: start.lat, lon: start.lon },
                    { lat: end.lat, lon: end.lon },
                    mode
                );

                setCoords(data.coords);
                setDistance(data.distance_km);
                setDuration(data.duration_min);

                const camerasOnRoute = data.cameras_on_route || [];
                setRouteCameras(camerasOnRoute);

                if (camerasOnRoute.length > 0) {
                    try {
                        const ids = camerasOnRoute.map(c => c.id);
                        await detectRouteCameras(ids);

                        const cg = await getCongestionGeoJSON();
                        setCongestionGeoJSON(cg || null);

                        if (cg) {
                            const colored = buildColoredRouteGeoJSON(data.coords, cg);
                            setColoredRouteGeoJSON(colored);
                        } else {
                            setColoredRouteGeoJSON(null);
                        }
                    } catch (e) {
                        console.error("Route camera detection error:", e);
                    }
                } else {
                    // no cameras → no congestion overlay
                    setColoredRouteGeoJSON(null);
                }

                setIsSearchingRoute(false);
                return data;
            } catch (err) {
                console.error("Route API Error:", err);
                setIsSearchingRoute(false);
                setErrorMessage(errorMsg);
                return null;
            }
        },
        []
    );



    /** 🔍 Search input change with debounce */
    const handleSearchChange = (e) => {
        const value = e.target.value;

        if (searchMode === 'location') {
            setSearchInput(value);
            setDebounceText(value);
            setIsSearchLocationSelected(false);

            if (!value.trim()) {
                setShowSearchDropdown(false);
                setFilteredLocations([]);
            }
        } else {
            // Camera search mode
            setCameraSearchTerm(value);
            setSearchInput(value);
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
                await runRoutePipeline(
                    { name: route.start.name, lat: route.start.lat, lon: route.start.lon },
                    { name: route.end.name, lat: route.end.lat, lon: route.end.lon },
                    travelMode,
                    'Không thể tải tuyến đường'
                );
            }, 500);
        }
    }, [location.state, travelMode, runRoutePipeline]);

    useEffect(() => {
        // Load history if logged in
        if (localStorage.getItem('token')) {
            Promise.all([getSavedLocations(), getSavedRoutes()])
                .then(([locs, routes]) => setRecentHistory({ locations: locs, routes: routes }))
                .catch(err => console.error("Failed to load history", err));
        }
    }, [openModal]); // Reload when sidebar opens

    useEffect(() => {
        async function loadCongestion() {
            try {
                const data = await getCongestionGeoJSON();
                setCongestionGeoJSON(data);
            } catch (err) {
                console.error("Failed to load congestion geojson", err);
            }
        }
        loadCongestion();
    }, []);

    useEffect(() => {
        if (!userLocation) return;

        const nameCoord = `${userLocation.lat}, ${userLocation.lon}`;
        setSelectedLocation({ name: nameCoord, lat: userLocation.lat, lon: userLocation.lon });
        setSearchInput(nameCoord);
        setIsSearchLocationSelected(true);
        setOpenModal(true);
        resetRouteResults();
    }, [userLocation, resetRouteResults]);

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
        resetRouteResults();
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

    const handleCameraSelect = (camera) => {
        setSelectedCamera(camera);
        setSearchInput('');
        setCameraSearchTerm('');
        setShowSearchDropdown(false);
        setFilteredCameras([]);
    };

    useEffect(() => {
        if (searchMode === 'camera' && cameraSearchTerm.trim() !== '') {
            const filtered = cameras.filter(camera => {
                const cameraName = camera.camera_name || '';
                const displayName = camera.display_name || '';
                const searchLower = cameraSearchTerm.toLowerCase();

                return cameraName.toLowerCase().includes(searchLower) ||
                    displayName.toLowerCase().includes(searchLower);
            });
            setFilteredCameras(filtered);
            setShowSearchDropdown(true);
        } else if (searchMode === 'camera') {
            setFilteredCameras([]);
            setShowSearchDropdown(false);
        }
    }, [cameraSearchTerm, cameras, searchMode]);

    /** 🛣 Tìm route bằng Flask /route */
    const handleSearch = useCallback(async (mode = 'car', routeType = 'fastest') => {
        if (!selectedLocation || !selectPosition) {
            console.log("Missing locations");
            return;
        }

        try {
            setErrorMessage('');
            const data = await calculateRoute(
                { lat: selectedLocation.lat, lon: selectedLocation.lon },
                { lat: selectPosition.lat, lon: selectPosition.lon },
                mode
            );

            setCoords(data.coords);
            setDistance(data.distance_km);
            setDuration(data.duration_min);

            const camerasOnRoute = data.cameras_on_route || [];
            setRouteCameras(camerasOnRoute);

            // Trigger detection for these cameras (by id)
            if (camerasOnRoute.length > 0) {
                try {
                    const ids = camerasOnRoute.map(c => c.id);
                    await detectRouteCameras(ids);

                    // refresh congestion from backend
                    const cg = await getCongestionGeoJSON();
                    if (cg) {
                        setCongestionGeoJSON(cg);
                        const colored = buildColoredRouteGeoJSON(data.coords, cg);
                        setColoredRouteGeoJSON(colored);
                    } else {
                        setColoredRouteGeoJSON(null);
                    }
                } catch (e) {
                    console.error("Route camera detection error:", e);
                }
            } else {
                // no cameras → no congestion overlay
                setColoredRouteGeoJSON(null);
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
                    congestionGeoJSON={congestionGeoJSON}
                    coloredRouteGeoJSON={coloredRouteGeoJSON}
                    routeCameras={routeCameras}
                    onRouteCameraClick={handleCameraSelect}
                    selectedCamera={selectedCamera}
                />

                <MyLocationControl onLocationFound={(location) => setUserLocation(location)} />
                <GoongMapStyleControl currentStyle={mapStyle} onStyleChange={setMapStyle} />
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
                        {/* Sidebar Search Box */}
                        <Box mb={2}>
                            <TextField
                                fullWidth
                                placeholder={searchMode === 'location' ? "Tìm kiếm địa điểm..." : "Tìm kiếm camera..."}
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
                                    setTimeout(() => setShowSearchDropdown(false), 200);
                                }}
                                className={classes.searchField}
                                InputProps={{
                                    startAdornment: <span style={{ marginRight: 9 }}>🔍</span>
                                }}
                            />

                            {/* Location results */}
                            {showSearchDropdown && searchMode === 'location' && filteredLocations.length > 0 && (
                                <Paper className={classes.searchDropdown}>
                                    <List dense>
                                        {filteredLocations.map((loc, i) => (
                                            <ListItem
                                                key={i}
                                                button
                                                className={classes.listItem}
                                                onMouseDown={(e) => {
                                                    e.preventDefault();
                                                    handleLocationSelect(loc);
                                                }}
                                            >
                                                <ListItemIcon><LocationOnIcon /></ListItemIcon>
                                                <ListItemText
                                                    primary={loc.address.freeformAddress}
                                                    secondary={loc.poi?.name}
                                                />
                                            </ListItem>
                                        ))}
                                    </List>
                                </Paper>
                            )}

                            {/* Camera results */}
                            {showSearchDropdown && searchMode === 'camera' && filteredCameras.length > 0 && (
                                <Paper className={classes.searchDropdown}>
                                    <List dense>
                                        {filteredCameras.slice(0, 8).map((camera) => (
                                            <ListItem
                                                key={camera.id}
                                                button
                                                className={classes.listItem}
                                                onMouseDown={(e) => {
                                                    e.preventDefault();
                                                    handleCameraSelect(camera);
                                                }}
                                            >
                                                <ListItemIcon><span>📹</span></ListItemIcon>
                                                <ListItemText
                                                    primary={camera.camera_name}
                                                    secondary={camera.display_name}
                                                />
                                            </ListItem>
                                        ))}
                                    </List>
                                </Paper>
                            )}
                        </Box>

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
                            setSelectPosition={setSelectPositionWithReset}
                            onSearch={handleSearch}
                            initialFrom={selectedLocation?.name || ""}
                            travelMode={travelMode}
                            setTravelMode={setTravelMode}
                            onFromLocationChange={(locationData) => {
                                resetRouteResults();
                                setSelectedLocation(locationData);
                                setSearchInput(locationData.name);
                                setIsSearchLocationSelected(true);
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
            {/* Camera Popup Panel */}
            {selectedCamera && (
                <div className="camera-info-panel">
                    <button
                        className="close-button"
                        onClick={() => setSelectedCamera(null)}
                    >
                        ×
                    </button>

                    <h3>{selectedCamera.camera_name}</h3>
                    <p><strong>Địa điểm:</strong> {selectedCamera.display_name}</p>
                    <p>
                        <strong>Tọa độ:</strong>
                        {selectedCamera.lat.toFixed(6)}, {selectedCamera.lon.toFixed(6)}
                    </p>

                    <CameraPopup
                        cameraId={selectedCamera.id}
                        cameraName={selectedCamera.camera_name}
                    />
                </div>
            )}
        </Box>
    );
}


function CameraPopup({ cameraId, cameraName }) {
    const [images, setImages] = useState([]);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadImages = async () => {
            try {
                setLoading(true);
                setError(null);
                const imageUrls = await fetchCameraImages(cameraId);
                setImages(imageUrls);
                setLoading(false);
            } catch (err) {
                setError("Không thể tải ảnh camera");
                setLoading(false);
            }
        };

        loadImages();
    }, [cameraId]);

    const nextImage = () => {
        setCurrentImageIndex((prev) => (prev + 1) % images.length);
    };

    const prevImage = () => {
        setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length);
    };

    return (
        <div className="camera-popup">
            <h3>{cameraName}</h3>
            <div className="camera-id">ID: {cameraId}</div>

            {loading && <div className="loading">Đang tải ảnh...</div>}
            {error && <div className="error">{error}</div>}

            {!loading && !error && images.length > 0 && (
                <div className="image-viewer">
                    <img
                        src={images[currentImageIndex]}
                        alt={`Camera ${cameraName}`}
                        className="camera-image"
                    />

                    {images.length > 1 && (
                        <div className="image-controls">
                            <button onClick={prevImage} className="nav-button">‹</button>
                            <span className="image-counter">
                                {currentImageIndex + 1} / {images.length}
                            </span>
                            <button onClick={nextImage} className="nav-button">›</button>
                        </div>
                    )}
                </div>
            )}

            {!loading && !error && images.length === 0 && (
                <div className="no-images">Không có ảnh cho camera này</div>
            )}
        </div>
    );
}

export default RoutesPage;