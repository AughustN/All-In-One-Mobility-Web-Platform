import React, { useState, useCallback, useEffect } from 'react';
import {
    Box, Paper, IconButton, TextField, List,
    ListItem, ListItemIcon, ListItemText, Typography
} from '@material-ui/core';

import { makeStyles } from '@material-ui/core/styles';
import CloseIcon from '@material-ui/icons/Close';
import SearchIcon from '@material-ui/icons/Search';
import LocationOnIcon from '@material-ui/icons/LocationOn';

import axios from "axios";
import Maps from '../Maps';
import SearchBoxRoutes from '../SearchBoxRoutes';

const API = "https://api.hcmus.fit";

const useStyles = makeStyles(theme => ({
    root: {
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        backgroundColor: '#f5f5f5',
        position: 'relative',
    },
    mapContainer: { width: '100%', height: '100%' },
    searchBarContainer: {
        position: 'fixed',
        top: '15px',
        left: '70px',
        zIndex: 9999,
        width: '320px',
        pointerEvents: 'auto',
    },
    searchField: {
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        '& .MuiOutlinedInput-root': { borderRadius: '8px' },
    },
    searchDropdown: {
        marginTop: '8px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        maxHeight: '400px',
        overflow: 'auto',
    },
    listItem: {
        cursor: 'pointer',
        borderBottom: '1px solid #f0f0f0',
        padding: '12px 16px',
        '&:hover': { backgroundColor: 'rgba(2,119,189,0.05)' },
        '&:last-child': { borderBottom: 'none' },
    },
    sidebarContainer: {
        position: "fixed",
        top: 0,
        left: 0,
        height: "100vh",
        width: 400,
        background: "#fff",
        zIndex: 2000,
        boxShadow: "2px 0 16px rgba(0,0,0,0.2)",
        display: "flex",
        flexDirection: "column",
        transition: "transform 0.35s ease",
        paddingTop: "50px",
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
    sidebarContent: { padding: "16px", overflowY: "auto", flexGrow: 1 },
    "@global": {
        ".open": { transform: "translateX(0)" },
        ".closed": { transform: "translateX(-85%)" },
    },
}));

function RoutesPage() {
    const classes = useStyles();

    const [filteredLocations, setFilteredLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [coords, setCoords] = useState([]);
    const [distance, setDistance] = useState(null);
    const [duration, setDuration] = useState(null);
    const [openModal, setOpenModal] = useState(false);
    const [showSearchDropdown, setShowSearchDropdown] = useState(false);
    const [searchInput, setSearchInput] = useState('');
    const [debounceText, setDebounceText] = useState('');
    const [selectPosition, setSelectPosition] = useState(null);
    const [travelMode, setTravelMode] = useState('car');
    const [errorMessage, setErrorMessage] = useState('');
    const [isSearchLocationSelected, setIsSearchLocationSelected] = useState(false);

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

    useEffect(() => {
        // Không tìm kiếm nếu đã chọn địa điểm
        if (isSearchLocationSelected) {
            return;
        }

        if (!debounceText.trim()) return;

        const timer = setTimeout(async () => {
            try {
                const res = await axios.post(`${API}/search`, { 
                    address: debounceText 
                });
                setFilteredLocations(res.data);
                setShowSearchDropdown(true);
                
                // Hiển thị thông báo nếu không có kết quả
                if (res.data.length === 0) {
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
    };

    /** 🛣 Tìm route bằng Flask /route */
    const handleSearch = useCallback(async (mode = 'car', routeType = 'fastest') => {
        if (!selectedLocation || !selectPosition) {
            console.log("Missing locations");
            return;
        }

        try {
            setErrorMessage('');
            const res = await axios.post(`${API}/route`, {
                start: { lat: selectedLocation.lat, lon: selectedLocation.lon },
                end: { lat: selectPosition.lat, lon: selectPosition.lon },
                travelMode: mode,
                routeType: routeType
            });

            setCoords(res.data.coords);
            setDistance(res.data.distance_km);
            setDuration(res.data.duration_min);
        } catch (err) {
            console.error("Route API Error:", err);
            if (err.response && err.response.data && err.response.data.error) {
                setErrorMessage(err.response.data.error);
            } else {
                setErrorMessage('Không thể tìm đường đi');
            }
        }
    }, [selectedLocation, selectPosition]);

    return (
        <Box className={classes.root}>
            {/* Full Screen Map */}
            <Box className={classes.mapContainer}>
                <Maps 
                    origin={selectedLocation}
                    destination={selectPosition}
                    coords={coords}
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
                        startAdornment: <SearchIcon style={{ marginRight: 8, color: "#0277BD" }} />
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
            <Box   data-sidebar="container" className={`${classes.sidebarContainer} ${openModal ? "open" : "closed"}`}>
                <Box  data-sidebar="header" className={classes.sidebarHeader}>
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
                        />

                        {coords.length > 0 && distance !== null && duration !== null && (
                            <Paper style={{ marginTop: 16, padding: 12, backgroundColor: '#e3f2fd' }}>
                                <Typography><b>Khoảng cách:</b> {distance.toFixed(2)} km</Typography>
                                <Typography><b>Thời gian:</b> {duration.toFixed(1)} phút</Typography>
                            </Paper>
                        )}
                    </Box>
                )}
            </Box>
        </Box>
    );
}

export default RoutesPage;