import React, { useEffect, useState } from 'react';
import {
    Container, Typography, Paper, List, ListItem,
    ListItemText, ListItemIcon, Divider, Box, Button
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import LocationOnIcon from '@material-ui/icons/LocationOn';
import DirectionsIcon from '@material-ui/icons/Directions';
import HistoryIcon from '@material-ui/icons/History';
import { getSavedLocations, getSavedRoutes } from '../api';
import { useNavigate } from 'react-router-dom';
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
dayjs.extend(utc)
dayjs.extend(timezone)
const useStyles = makeStyles((theme) => ({
    root: {
        paddingTop: theme.spacing(4),
        paddingBottom: theme.spacing(4),
        minHeight: '100vh',
        backgroundColor: '#f4f6f8',
        maxHeight: '100vh',
        overflowY: 'auto',
    },
    paper: {
        padding: theme.spacing(3),
        borderRadius: 16,
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
        marginBottom: theme.spacing(3),
    },
    sectionTitle: {
        display: 'flex',
        alignItems: 'center',
        marginBottom: theme.spacing(2),
        color: '#1a237e',
        fontWeight: 600,
    },
    icon: {
        marginRight: theme.spacing(1),
        color: '#1a237e',
    },
    listItem: {
        borderRadius: 8,
        marginBottom: theme.spacing(1),
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        '&:hover': {
            backgroundColor: '#e8eaf6',
            transform: 'translateX(4px)',
        },
    },
    emptyState: {
        textAlign: 'center',
        padding: theme.spacing(4),
        color: '#757575',
    }
}));

export default function HistoryPage() {
    const classes = useStyles();
    const navigate = useNavigate();
    const [locations, setLocations] = useState([]);
    const [routes, setRoutes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [locs, rts] = await Promise.all([
                    getSavedLocations(),
                    getSavedRoutes()
                ]);
                setLocations(locs);
                setRoutes(rts);
            } catch (error) {
                console.error("Failed to fetch history:", error);
            } finally {
                setLoading(false);
            }
        };

        if (localStorage.getItem('token')) {
            fetchData();
        } else {
            navigate('/login');
        }
    }, [navigate]);

    if (loading) {
        return (
            <Container maxWidth="md" className={classes.root}>
                <Typography variant="h5">Loading history...</Typography>
            </Container>
        );
    }

    return (
        <Container maxWidth="md" className={classes.root}>
            <Box display="flex" alignItems="center" mb={4}>
                <HistoryIcon style={{ fontSize: 40, color: '#1a237e', marginRight: 16 }} />
                <Typography variant="h4" style={{ fontWeight: 700, color: '#1a237e' }}>
                    Lịch sử tìm kiếm
                </Typography>
            </Box>

            {/* Locations Section */}
            <Paper className={classes.paper}>
                <Typography variant="h6" className={classes.sectionTitle}>
                    <LocationOnIcon className={classes.icon} />
                    Địa điểm đã lưu
                </Typography>
                <Divider style={{ marginBottom: 16 }} />

                {locations.length === 0 ? (
                    <Typography className={classes.emptyState}>Chưa có địa điểm nào được lưu.</Typography>
                ) : (
                    <List>
                        {locations.map((loc, index) => (
                            <ListItem 
                                key={index} 
                                className={classes.listItem}
                                onClick={() => {
                                    // Navigate to routes page with location data
                                    navigate('/routes', { 
                                        state: { 
                                            location: {
                                                name: loc.name,
                                                lat: loc.lat,
                                                lon: loc.lng
                                            }
                                        } 
                                    });
                                }}
                            >
                                <ListItemIcon>
                                    <LocationOnIcon color="primary" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={loc.name}
                                    secondary={dayjs.tz(loc.timestamp, "YYYY-MM-DD HH:mm:ss", "Asia/Ho_Chi_Minh")
                                        .format("DD/MM/YYYY HH:mm:ss")}
                                    primaryTypographyProps={{ style: { fontWeight: 500 } }}
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Paper>

            {/* Routes Section */}
            <Paper className={classes.paper}>
                <Typography variant="h6" className={classes.sectionTitle}>
                    <DirectionsIcon className={classes.icon} />
                    Tuyến đường đã lưu
                </Typography>
                <Divider style={{ marginBottom: 16 }} />

                {routes.length === 0 ? (
                    <Typography className={classes.emptyState}>Chưa có tuyến đường nào được lưu.</Typography>
                ) : (
                    <List>
                        {routes.map((route, index) => (
                            <ListItem 
                                key={index} 
                                className={classes.listItem}
                                onClick={() => {
                                    // Navigate to routes page with route data
                                    navigate('/routes', { 
                                        state: { 
                                            route: {
                                                start: {
                                                    name: route.start_name,
                                                    lat: route.start_lat,
                                                    lon: route.start_lng
                                                },
                                                end: {
                                                    name: route.end_name,
                                                    lat: route.end_lat,
                                                    lon: route.end_lng
                                                }
                                            }
                                        } 
                                    });
                                }}
                            >
                                <ListItemIcon>
                                    <DirectionsIcon color="secondary" />
                                </ListItemIcon>
                                <ListItemText
                                    primary={`${route.start_name} ➝ ${route.end_name}`}
                                    secondary={dayjs.tz(route.timestamp, "YYYY-MM-DD HH:mm:ss", "Asia/Ho_Chi_Minh")
                                        .format("DD/MM/YYYY HH:mm:ss")}
                                    primaryTypographyProps={{ style: { fontWeight: 500 } }}
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Paper>
        </Container>
    );
}
