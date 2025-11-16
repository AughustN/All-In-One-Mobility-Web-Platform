import React, { useState } from 'react';
import { Box, Grid, Paper, Card, CardContent, Typography, Chip, Button } from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import Maps from '../Maps';
import SearchBoxBus from '../SearchBoxBus';

const useStyles = makeStyles(theme => ({
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
    [theme.breakpoints.down('sm')]: {
      height: '60%',
    },
    [theme.breakpoints.up('md')]: {
      height: '100%',
    },
  },
  panelContainer: {
    height: '40%',
    [theme.breakpoints.up('md')]: {
      height: '100%',
    },
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
  busCard: {
    marginBottom: theme.spacing(2),
    backgroundColor: '#f9f9f9',
    borderLeft: `4px solid #0277BD`,
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    '&:hover': {
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      backgroundColor: '#f0f7ff',
    },
  },
  busRoute: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing(1),
  },
  busRouteName: {
    fontWeight: 'bold',
    fontSize: '16px',
    color: '#333',
  },
  busRouteTime: {
    fontSize: '14px',
    color: '#666',
  },
  stopsContainer: {
    marginTop: theme.spacing(1),
    paddingTop: theme.spacing(1),
    borderTop: `1px solid #eee`,
  },
  stopItem: {
    fontSize: '12px',
    color: '#666',
    marginBottom: theme.spacing(0.5),
    paddingLeft: theme.spacing(1),
    borderLeft: `2px solid #FFA726`,
  },
  chipGroup: {
    display: 'flex',
    gap: theme.spacing(1),
    marginTop: theme.spacing(1),
    flexWrap: 'wrap',
  },
}));

function BusMapPage() {
  const classes = useStyles();
  const [selectPosition, setSelectPosition] = useState(null);
  const [selectedBusRoute, setSelectedBusRoute] = useState(null);

  // Mock bus routes data
  const busRoutes = [
    {
      id: 1,
      routeName: 'Bus 101 - Downtown Express',
      stops: 8,
      departTime: '10:00 AM',
      arriveTime: '10:35 AM',
      fare: '$2.50',
      congestion: 'Low',
      stops_list: [
        'Main St Station',
        'Market Ave',
        'Oak Park',
        'Central Plaza',
        'Downtown Terminal',
      ],
    },
    {
      id: 2,
      routeName: 'Bus 215 - Airport Connector',
      stops: 5,
      departTime: '10:05 AM',
      arriveTime: '10:45 AM',
      fare: '$3.50',
      congestion: 'Medium',
      stops_list: [
        'Start Point',
        'Highway Junction',
        'Airport Road',
        'Terminal 1',
        'Terminal 2',
      ],
    },
    {
      id: 3,
      routeName: 'Bus 42 - Residential Loop',
      stops: 12,
      departTime: '10:10 AM',
      arriveTime: '11:00 AM',
      fare: '$1.50',
      congestion: 'Heavy',
      stops_list: [
        'Residential Ave',
        'Maple St',
        'Pine St',
        'Community Center',
        'Shopping Mall',
        'Park Entrance',
      ],
    },
  ];

  const getCongestionColor = (level) => {
    switch (level) {
      case 'Low':
        return '#4CAF50';
      case 'Medium':
        return '#FFA726';
      case 'Heavy':
        return '#F44336';
      default:
        return '#666';
    }
  };

  return (
    <Box className={classes.root}>
      <Box className={classes.mainContent}>
        <Grid container style={{ height: '100%' }} spacing={0}>
          {/* Map Section */}
          <Grid item xs={12} md={7} className={classes.mapContainer}>
            <Maps selectPosition={selectPosition} />
          </Grid>

          {/* Panel Section */}
          <Grid item xs={12} md={5} className={classes.panelContainer}>
            <Paper style={{ height: '100%', overflow: 'auto' }}>
              <Box style={{ padding: 16 }}>
                {/* Title */}
                <Box className={classes.title}>🚌 Bus Routes</Box>

                {/* Search Box */}
                <Paper className={classes.contentPaper} elevation={2}>
                  <SearchBoxBus
                    selectPosition={selectPosition}
                    setSelectPosition={setSelectPosition}
                  />
                </Paper>

                {/* Bus Routes List */}
                <Paper className={classes.contentPaper} elevation={2}>
                  <Typography variant="h6" style={{ marginBottom: 16, fontWeight: 'bold' }}>
                    Available Routes
                  </Typography>

                  {busRoutes.map(route => (
                    <Card
                      key={route.id}
                      className={classes.busCard}
                      onClick={() => setSelectedBusRoute(selectedBusRoute?.id === route.id ? null : route)}
                    >
                      <CardContent style={{ paddingBottom: 12 }}>
                        {/* Route Header */}
                        <Box className={classes.busRoute}>
                          <Box>
                            <Typography className={classes.busRouteName}>
                              {route.routeName}
                            </Typography>
                            <Typography className={classes.busRouteTime}>
                              {route.departTime} → {route.arriveTime}
                            </Typography>
                          </Box>
                          <Box textAlign="right">
                            <Typography style={{ fontWeight: 'bold', color: '#0277BD' }}>
                              {route.fare}
                            </Typography>
                            <Chip
                              label={`${route.stops} stops`}
                              size="small"
                              style={{ marginTop: 8 }}
                            />
                          </Box>
                        </Box>

                        {/* Chips */}
                        <Box className={classes.chipGroup}>
                          <Chip
                            label={`Traffic: ${route.congestion}`}
                            style={{
                              backgroundColor: getCongestionColor(route.congestion),
                              color: '#fff',
                            }}
                            size="small"
                          />
                          <Chip
                            label="Real-time tracking"
                            variant="outlined"
                            size="small"
                          />
                        </Box>

                        {/* Expandable Stops */}
                        {selectedBusRoute?.id === route.id && (
                          <Box className={classes.stopsContainer}>
                            <Typography
                              variant="subtitle2"
                              style={{ fontWeight: 'bold', marginBottom: 8 }}
                            >
                               Route Stops
                            </Typography>
                            {route.stops_list.map((stop, idx) => (
                              <Box key={idx} className={classes.stopItem}>
                                {idx + 1}. {stop}
                              </Box>
                            ))}
                            <Button
                              variant="contained"
                              color="primary"
                              fullWidth
                              style={{ marginTop: 12 }}
                            >
                              Select This Route
                            </Button>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Paper>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default BusMapPage;
