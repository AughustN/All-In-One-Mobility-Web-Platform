import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Typography,
  Button,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Fab,
} from '@material-ui/core';
import { makeStyles } from '@material-ui/core/styles';
import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import CloseIcon from '@material-ui/icons/Close';
import MenuIcon from '@material-ui/icons/Menu';
import EmojiEventsIcon from '@material-ui/icons/EmojiEvents';
import { getAITripPlan, saveTrip } from '../api';
import GoongPlanTripMap from '../GoongPlanTripMap';
import { useLocation } from 'react-router-dom';

const useStyles = makeStyles((theme) => ({
  root: {
    display: 'flex',
    height: '100vh',
    overflow: 'hidden',
    backgroundColor: '#0a1d37',
    position: 'relative',
  },
  // Mobile FAB button
  openSidebarButton: {
    position: 'fixed',
    top: 140,
    left: 20,
    zIndex: 998,
    backgroundColor: '#ff6b9d',
    color: 'white',
    '&:hover': { backgroundColor: '#ff4b8a' },
  },
  // Sidebar container - slide in/out
  sidebarContainer: {
    position: 'fixed',
    top: 50,
    left: 0,
    height: 'calc(100vh - 50px)',
    width: 600,
    background: 'linear-gradient(135deg, #1e3c72, #2a5298)',
    color: 'white',
    zIndex: 999,
    boxShadow: '4px 0 20px rgba(0,0,0,0.4)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
    [theme.breakpoints.down('sm')]: {
      top: 56,
      height: 'calc(100vh - 56px)',
      width: '100%',
      maxWidth: '380px',
      transform: 'translateX(-100%)',
      '&.open': { transform: 'translateX(0)' },
    },
    // Desktop: start open, allow closing
    [theme.breakpoints.up('md')]: {
      transform: 'translateX(0)',           // open by default on desktop
        '&.closed': { transform: 'translateX(-100%)' }, // can be closed
    },
  },
  sidebarHeader: {
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    flexShrink: 0,
  },
  sidebarTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ff6b9d',
  },
  closeButton: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    color: 'white',
    '&:hover': { backgroundColor: 'rgba(255,255,255,0.25)' },
  },
  sidebarContent: {
    padding: theme.spacing(3),
    overflowY: 'auto',
    flexGrow: 1,
    '&::-webkit-scrollbar': { width: '8px' },
    '&::-webkit-scrollbar-track': { background: 'transparent' },
    '&::-webkit-scrollbar-thumb': {
      background: 'rgba(255,255,255,0.3)',
      borderRadius: '4px',
    },
    '&::-webkit-scrollbar-thumb:hover': { background: 'rgba(255,255,255,0.5)' },
  },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 8, color: '#ff6b9d' },
  subtitle: { textAlign: 'center', marginBottom: 32, opacity: 0.9 },
  inputBox: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    marginBottom: 24,
    '& .MuiOutlinedInput-root': {
      color: 'white',
      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
      '&.Mui-focused fieldset': { borderColor: '#ff6b9d' },
    },
    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
    '& input, & textarea': { color: 'white' },
    '& input::placeholder, & textarea::placeholder': { color: 'rgba(255,255,255,0.5)', opacity: 1 },
  },
 
  planButton: {
    background: 'linear-gradient(45deg, #ff6b9d, #ff8eb0)',
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    padding: '16px',
    borderRadius: 30,
    textTransform: 'none',
    boxShadow: '0 6px 20px rgba(255,107,157,0.4)',
    '&:hover': { background: 'linear-gradient(45deg, #ff4b8a, #ff6b9d)' },
  },
  resultCard: { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 16, padding: 24, mt: 3, backdropFilter: 'blur(10px)' },
  timelineDot: { backgroundColor: '#ff6b9d', width: 12, height: 12, borderRadius: '50%', marginRight: 16, marginTop: 6 },
  costBox: { backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: 16, textAlign: 'center', mt: 3 },
  // Itinerary / result styles
  itineraryList: { paddingTop: 8, paddingBottom: 8 },
  itineraryItem: { paddingTop: 12, paddingBottom: 12 },
  timeBadge: { backgroundColor: 'white', color: '#ff6b9d', borderRadius: 8, padding: '6px 10px', fontWeight: 700, display: 'inline-block' },
  activityTitle: { fontWeight: '700', color: 'white' },
  placeText: { color: '#ffcccb', display: 'block', marginTop: 6 },
  addressText: { opacity: 0.8, display: 'block' },
  costText: { color: '#ff6b9d', fontWeight: 700 },
  itemCostBox: { minWidth: 120, textAlign: 'right' },
  acceptButton: { marginTop: 16 },
}));

export default function PlanTripPage() {
  const classes = useStyles();
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const locationState = useLocation();


  // Same logic as BusMapPage: open by default on desktop
  const [openModal, setOpenModal] = useState(window.innerWidth >= 960);

  const handlePlan = async () => {
    if (!description.trim()) return;
    location.trim();
    setLoading(true);
    try {
        const result = await getAITripPlan(location ? `${description} in ${location}` : description);  // <-- call backend
        setPlan(result);                                  // <-- display result
    } catch (err) {
      alert("Có lỗi xảy ra khi tạo lịch trình!");
      console.error(err);
    }
    setLoading(false);
  };

// Handle navigation from HistoryPage
    useEffect(() => {
        if (locationState.state?.trip) {
            const raw = locationState.state.trip;

            const tripData =
                raw.trip_json?.trip ||     // backend style 1
                raw.trip_json ||           // backend style 2
                raw.trip ||                // client-passed object
                raw;                       // fallback

            setPlan(tripData);
            setOpenModal(true);
        }
    }, [locationState.state]);


  return (
    <Box className={classes.root}>
      {/* Mobile: Show FAB when sidebar is closed */}
      {!openModal && (
        <Fab className={classes.openSidebarButton} onClick={() => setOpenModal(true)}>
          <MenuIcon />
        </Fab>
      )}

      {plan && (
          <GoongPlanTripMap plan={plan} />
      )}


      {/* Sidebar */}
      <Box className={`${classes.sidebarContainer} ${openModal ? 'open' : 'closed'}`}>
        {/* Header with Close Button */}
        <Box className={classes.sidebarHeader}>
          <Typography className={classes.sidebarTitle}>Personal Planner</Typography>
          <IconButton onClick={() => setOpenModal(false)} className={classes.closeButton}>
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Scrollable Content */}
        <Box className={classes.sidebarContent}>
          <Typography className={classes.title}>AI Trip Planner</Typography>
          <Typography className={classes.subtitle}>Design the perfect Schedule in seconds.</Typography>

          {/* Inputs */}
          <TextField
            className={classes.inputBox}
            variant="outlined"
            multiline
            rows={4}
            placeholder="Một ngày vui vẻ và lãng mạn, ngân sách dưới 1 triệu..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
          />

          <TextField
            className={classes.inputBox}
            variant="outlined"
            placeholder="Quận 5, TP.HCM (tùy chọn)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            fullWidth
          />

          <Button
            className={classes.planButton}
            fullWidth
            onClick={handlePlan}
            disabled={loading || !description.trim()}
          >
            {loading ? <CircularProgress size={28} color="inherit" /> : 'Plan My Trip'}
          </Button>

          {/* Result */}
          {plan && (
            <Box sx={{ mt: 4, pb: 12 }}>
              <Paper elevation={0} className={classes.resultCard}>
                
                {/* Title */}
                <Typography
                  variant="h5"
                  style={{
                    color: '#ff6b9d',
                    textAlign: 'center',
                    marginBottom: 16
                  }}
                >
                  {plan.title}
                </Typography>

                <Typography
                  style={{
                    opacity: 0.9,
                    textAlign: 'center',
                    marginBottom: 24
                  }}
                >
                  Your personalized itinerary is ready!
                </Typography>

                {/* Itinerary List */}
                <List className={classes.itineraryList}>
                  {plan.itinerary?.map((item, idx) => {
                    const activityText = (item.activity || '')
                      .replace(/^\s*(Buổi sáng|Buổi trưa|Buổi chiều|Buổi tối)\s*[:\-–—]?\s*/i, '')
                      .trim();

                    return (
                      <React.Fragment key={idx}>
                        <ListItem
                          alignItems="flex-start"
                          className={classes.itineraryItem}
                          style={{
                            paddingTop: 12,
                            paddingBottom: 12,
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          {/* Time Badge */}
                          <Box
                            style={{
                              background: '#ffd369',
                              padding: '6px 12px',
                              borderRadius: 12,
                              marginRight: 16,
                              minWidth: 64,
                              textAlign: 'center',
                              boxShadow: '0 0 6px rgba(255, 211, 105, 0.3)'
                            }}
                          >
                            <Typography
                              variant="body2"
                              style={{
                                fontWeight: 700,
                                color: '#1b2430',
                                fontSize: 13
                              }}
                            >
                              {item.time}
                            </Typography>
                          </Box>

                          {/* Activity, place, address */}
                          <ListItemText
                            primary={
                              <Typography
                                style={{
                                  fontSize: 16,
                                  fontWeight: 600,
                                  color: 'black'
                                }}
                              >
                                {item.activity}
                              </Typography>
                            }
                            secondary={
                              <>
                                <Typography
                                  variant="body2"
                                  style={{
                                    marginTop: 4,
                                    color: '#ffb6c1',
                                    fontWeight: 500
                                  }}
                                >
                                  {item.place}
                                </Typography>

                                <Typography
                                  variant="body2"
                                  style={{
                                    opacity: 0.8
                                  }}
                                >
                                  {item.address}
                                </Typography>
                              </>
                            }
                          />

                          {/* Cost */}
                          <Box style={{ marginLeft: 'auto', paddingLeft: 16 }}>
                            <Typography
                              style={{
                                color: '#ff6b9d',
                                fontWeight: 600,
                                fontSize: 14
                              }}
                            >
                              {item.cost}
                            </Typography>
                          </Box>
                        </ListItem>

                        {/* Divider */}
                        {idx < plan.itinerary.length - 1 && (
                          <Divider
                            style={{
                              backgroundColor: 'rgba(255,255,255,0.08)',
                              marginLeft: 80,
                              marginRight: 8
                            }}
                          />
                        )}
                      </React.Fragment>
                    );
                  })}
                </List>

                {/* Total Cost */}
                <Box className={classes.costBox}>
                  <Typography style={{ fontSize: 20, fontWeight: 'bold' }}>
                    Tổng chi phí: {plan.totalCost.toLocaleString()} ₫
                  </Typography>
                </Box>

                {/* Accept Plan */}
                <Button
                  fullWidth
                  className={`${classes.planButton} ${classes.acceptButton}`}
                  onClick={()=>{
                    if (!plan) {
                        alert("No trip plan to save!");
                        return;
                    }
                    saveTrip(plan);}
                  }
                  startIcon={<EmojiEventsIcon />}
                >
                  Accept Plan & Schedule
                </Button>

              </Paper>
            </Box>
          )}

        </Box>
      </Box>

      {/* Right side - map/background */}
      <Box style={{ flex: 1, backgroundColor: '#0d1b2a' }} />
    </Box>
  );
}