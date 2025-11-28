import React, { useState, useEffect } from "react";
import {
    OutlinedInput,
    Button,
    Box,
    Paper,
    Typography,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
} from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import LocationOnIcon from "@material-ui/icons/LocationOn";
import DirectionsWalkIcon from "@material-ui/icons/DirectionsWalk";
import DirectionsBikeIcon from "@material-ui/icons/DirectionsBike";
import DriveEtaIcon from "@material-ui/icons/DriveEta";
import { searchLocation } from "./api";

const useStyles = makeStyles((theme) => ({
    transportIconContainer: {
        display: 'flex',
        gap: '16px',
        justifyContent: 'center',
        marginBottom: '16px',
    },
    iconButton: {
        cursor: 'pointer',
        padding: '12px',
        borderRadius: '12px',
        border: '2px solid #e0e0e0',
        transition: 'all 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '60px',
        height: '60px',
        '&:hover': {
            borderColor: '#0277BD',
            backgroundColor: 'rgba(2, 119, 189, 0.05)',
        },
        '&.selected': {
            borderColor: '#0277BD',
            backgroundColor: 'rgba(2, 119, 189, 0.15)',
        },
    },
    icon: {
        fontSize: '32px',
        color: '#0277BD',
    },
    searchDropdown: {
        marginTop: '8px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        maxHeight: '300px',
        overflow: 'auto',
        position: 'absolute',
        width: '100%',
        zIndex: 1000,
    },
    listItem: {
        cursor: 'pointer',
        borderBottom: '1px solid #f0f0f0',
        padding: '12px 16px',
        '&:hover': { backgroundColor: 'rgba(2,119,189,0.05)' },
        '&:last-child': { borderBottom: 'none' },
    },
}));

const transportOptions = [
    { value: 'pedestrian', icon: DirectionsWalkIcon, label: 'Đi bộ' },
    { value: 'bicycle', icon: DirectionsBikeIcon, label: 'Xe đạp' },
    { value: 'car', icon: DriveEtaIcon, label: 'Ô tô' },
];

export default function SearchBoxRoutes(props) {
    const { setSelectPosition, onSearch, initialFrom = "", travelMode, setTravelMode, routeType, setRouteType, onFromLocationChange } = props;
    const classes = useStyles();

    const [fromLocation, setFromLocation] = useState(initialFrom);
    const [toLocation, setToLocation] = useState("");
    const [fromSearchResults, setFromSearchResults] = useState([]);
    const [toSearchResults, setToSearchResults] = useState([]);
    const [showFromDropdown, setShowFromDropdown] = useState(false);
    const [showToDropdown, setShowToDropdown] = useState(false);
    const [selectedTransport, setSelectedTransport] = useState(travelMode || "car");
    const [selectedRouteType, setSelectedRouteType] = useState(routeType || 'fastest');
    const [searchError, setSearchError] = useState('');
    const [isToLocationSelected, setIsToLocationSelected] = useState(false);
    const [isFromLocationSelected, setIsFromLocationSelected] = useState(false);
    const [gettingLocation, setGettingLocation] = useState(false);

    // Update from location when initialFrom changes
    useEffect(() => {
        setFromLocation(initialFrom);
    }, [initialFrom]);

    // Search FROM location with debounce
    useEffect(() => {
        if (isFromLocationSelected) return;

        if (!fromLocation.trim()) {
            setShowFromDropdown(false);
            setFromSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            try {
                const data = await searchLocation(fromLocation);
                setFromSearchResults(data);
                setShowFromDropdown(true);
            } catch (err) {
                console.error("Search API Error:", err);
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [fromLocation, isFromLocationSelected]);

    // Search TO location with debounce
    useEffect(() => {
        if (isToLocationSelected) return;

        if (!toLocation.trim()) {
            setShowToDropdown(false);
            setToSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            try {
                const data = await searchLocation(toLocation);
                setToSearchResults(data);
                setShowToDropdown(true);

                if (data.length === 0) {
                    setSearchError('Không tìm thấy địa điểm');
                } else {
                    setSearchError('');
                }
            } catch (err) {
                console.error("Search API Error:", err);
                setSearchError('Lỗi khi tìm kiếm');
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [toLocation, isToLocationSelected]);

    const handleFromLocationSelect = (loc) => {
        const pos = loc.position;
        const locationData = {
            lat: pos.lat,
            lon: pos.lon,
            name: loc.address.freeformAddress
        };
        
        setFromLocation(loc.address.freeformAddress);
        setShowFromDropdown(false);
        setFromSearchResults([]);
        setIsFromLocationSelected(true);
        
        // Notify parent component
        if (onFromLocationChange) {
            onFromLocationChange(locationData);
        }
    };

    const handleToLocationSelect = (loc) => {
        const pos = loc.position;
        setSelectPosition({
            lat: pos.lat,
            lon: pos.lon,
            name: loc.address.freeformAddress
        });
        setToLocation(loc.address.freeformAddress);
        setShowToDropdown(false);
        setSearchError('');
        setToSearchResults([]);
        setIsToLocationSelected(true);
    };

    // Get current location
    const handleGetCurrentLocation = () => {
        if (!navigator.geolocation) {
            alert('Trình duyệt không hỗ trợ định vị');
            return;
        }

        setGettingLocation(true);
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                
                // Reverse geocode to get address
                try {
                    const response = await fetch(
                        `https://rsapi.goong.io/Geocode?latlng=${latitude},${longitude}&api_key=WOh4DfxBHRZhUMufKtHKj4qXFb2RZu2vlatKPJpH`
                    );
                    const data = await response.json();
                    
                    const address = data.results?.[0]?.formatted_address || 'Vị trí hiện tại';
                    
                    setFromLocation(address);
                    setIsFromLocationSelected(true);
                    
                    // Notify parent with isGPS flag
                    if (onFromLocationChange) {
                        onFromLocationChange({
                            lat: latitude,
                            lon: longitude,
                            name: address,
                            isGPS: true // Enable real-time navigation
                        });
                    }
                } catch (err) {
                    console.error('Reverse geocode error:', err);
                    setFromLocation('Vị trí hiện tại');
                    
                    if (onFromLocationChange) {
                        onFromLocationChange({
                            lat: latitude,
                            lon: longitude,
                            name: 'Vị trí hiện tại',
                            isGPS: true // Enable real-time navigation
                        });
                    }
                }
                
                setGettingLocation(false);
            },
            (error) => {
                console.error('Geolocation error:', error);
                alert(`Không thể lấy vị trí. Vui lòng cho phép truy cập vị trí. ${error}`);
                setGettingLocation(false);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    };

    const handleTransportChange = (value) => {
        setSelectedTransport(value);
        if (setTravelMode) setTravelMode(value);
    };

    const handleRouteTypeChange = (value) => {
        setSelectedRouteType(value);
        if (setRouteType) setRouteType(value);
    };

    const handleSearch = () => {
        if (onSearch) {
            onSearch(selectedTransport, selectedRouteType);
        }
    };

    return (
        <Box data-route="item" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* From Location - Editable */}
            <Box style={{ position: 'relative' }}>
                <Typography variant="subtitle2" style={{ marginBottom: "8px", fontWeight: "bold" }}>
                    Điểm đi
                </Typography>
                <Box style={{ display: 'flex', gap: '8px' }}>
                    <OutlinedInput
                        fullWidth
                        placeholder="Nhập địa chỉ xuất phát"
                        value={fromLocation}
                        onChange={(e) => {
                            setFromLocation(e.target.value);
                            setIsFromLocationSelected(false);
                        }}
                        onFocus={() => {
                            if (fromLocation && !isFromLocationSelected) {
                                setShowFromDropdown(true);
                            }
                        }}
                        onBlur={() => {
                            setTimeout(() => setShowFromDropdown(false), 200);
                        }}
                        style={{ backgroundColor: "#f9f9f9" }}
                    />
                    <Button
                        variant="outlined"
                        color="primary"
                        onClick={handleGetCurrentLocation}
                        disabled={gettingLocation}
                        style={{ minWidth: '50px', padding: '8px' }}
                        title="Lấy vị trí hiện tại"
                    >
                        {gettingLocation ? '⏳' : '📍'}
                    </Button>
                </Box>

                {/* Dropdown FROM location */}
                {showFromDropdown && fromSearchResults.length > 0 && (
                    <Paper className={classes.searchDropdown}>
                        <List style={{ padding: 0 }}>
                            {fromSearchResults.map((location, i) => (
                                <ListItem
                                    key={i}
                                    className={classes.listItem}
                                    onMouseDown={(e) => {
                                        e.preventDefault();
                                        handleFromLocationSelect(location);
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

            {/* To Location - Searchable */}
            <Box style={{ position: 'relative' }}>
                <Typography variant="subtitle2" style={{ marginBottom: "8px", fontWeight: "bold" }}>
                    Điểm tới
                </Typography>
                <OutlinedInput
                    fullWidth
                    placeholder="Nhập địa chỉ đích trong TP.HCM"
                    value={toLocation}
                    onChange={(e) => {
                        setToLocation(e.target.value);
                        setIsToLocationSelected(false);
                    }}
                    onFocus={() => {
                        if (toLocation && !isToLocationSelected) {
                            setShowToDropdown(true);
                        }
                    }}
                    onBlur={() => {
                        // Đóng dropdown sau 200ms để có thời gian click vào item
                        setTimeout(() => {
                            setShowToDropdown(false);
                        }, 200);
                    }}
                    style={{ backgroundColor: "#f9f9f9" }}
                />

                {/* Hiển thị lỗi nếu không tìm thấy */}
                {searchError && toLocation && (
                    <Typography variant="caption" style={{ color: '#c62828', marginTop: 4, display: 'block' }}>
                        {searchError}
                    </Typography>
                )}

                {/* Dropdown kết quả tìm kiếm */}
                {showToDropdown && toSearchResults.length > 0 && (
                    <Paper className={classes.searchDropdown}>
                        <List style={{ padding: 0 }}>
                            {toSearchResults.map((location, i) => (
                                <ListItem
                                    key={i}
                                    className={classes.listItem}
                                    onMouseDown={(e) => {
                                        e.preventDefault(); // Ngăn onBlur trigger
                                        handleToLocationSelect(location);
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

            {/* Route Type Selection */}
            <Box>
                <Typography variant="subtitle2" style={{ marginBottom: "8px", fontWeight: "bold" }}>
                    Tuyến đường ưu tiên
                </Typography>
                <Box style={{ display: 'flex', gap: '12px' }}>
                    <Button
                        variant={selectedRouteType === 'fastest' ? 'contained' : 'outlined'}
                        color="primary"
                        onClick={() => handleRouteTypeChange('fastest')}
                        style={{ flexGrow: 1 }}
                    >
                     Nhanh nhất
                    </Button>
                    <Button
                        variant={selectedRouteType === 'shortest' ? 'contained' : 'outlined'}
                        color="primary"
                        onClick={() => handleRouteTypeChange('shortest')}
                        style={{ flexGrow: 1 }}
                    >
                     Ngắn nhất
                    </Button>
                </Box>
            </Box>

            {/* Transport Types */}
            <Box>
                <Typography variant="subtitle2" style={{ marginBottom: "12px", fontWeight: "bold" }}>
                    Phương tiện di chuyển
                </Typography>
                <Box className={classes.transportIconContainer}>
                    {transportOptions.map((option) => {
                        const IconComponent = option.icon;
                        return (
                            <Box
                                key={option.value}
                                className={`${classes.iconButton} ${selectedTransport === option.value ? 'selected' : ''}`}
                                onClick={() => handleTransportChange(option.value)}
                                title={option.label}
                            >
                                <IconComponent className={classes.icon} />
                            </Box>
                        );
                    })}
                </Box>
            </Box>

            {/* Search Button */}
            <Button
                variant="contained"
                color="primary"
                size="large"
                fullWidth
                onClick={handleSearch}
                disabled={!fromLocation || !toLocation}
                style={{ padding: "12px", fontWeight: "bold" }}
            >
                Tìm đường
            </Button>
        </Box>
    );
}