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
import SearchIcon from '@material-ui/icons/Search';
import MenuIcon from '@material-ui/icons/Menu';
import EmojiEventsIcon from '@material-ui/icons/EmojiEvents';
import { getAITripPlan, saveTrip } from '../api';
import GoongPlanTripMap from '../GoongPlanTripMap';
import { useLocation } from 'react-router-dom';
import '../css/PlanTripPageDarkMode.css';
import { useNavigate } from 'react-router-dom';


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
  // Mobile FAB button
  openSidebarButton: {
    position: 'fixed',
    top: 140,
    left: 20,
    zIndex: 998,
    backgroundColor: '#6ac5faff',
    color: 'white',
    '&:hover': { backgroundColor: '#01579B' },
    [theme.breakpoints.up('md')]: {
      display: 'none',
    },
  },
  // Sidebar container - slide in/out
  sidebarContainer: {
    position: 'fixed',
    top: 50,
    left: 0,
    height: 'calc(100vh - 56px)',
    width: 400,
    background: '#fff',
    zIndex: 999,
    boxShadow: '2px 0 16px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'transform 0.35s ease',
    [theme.breakpoints.down('sm')]: {
      width: '100%',
      maxWidth: '320px',
      transform: 'translateX(-100%)',
      '&.open': { transform: 'translateX(0)' },
    },
  },
  sidebarHeader: {
    padding: '14px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #e0e0e0',
  },
  sidebarTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0277BD',
  },
  closeButton: {
    background: '#f2f5f7',
    borderRadius: 8,
  },
  sidebarContent: {
    padding: '16px',
    overflowY: 'auto',
    flexGrow: 1,
    maxHeight: 'calc(100vh - 70px)',
    '&::-webkit-scrollbar': { width: '8px' },
    '&::-webkit-scrollbar-track': { background: '#f1f1f1' },
    '&::-webkit-scrollbar-thumb': {
      background: '#888',
      borderRadius: '4px',
    },
    '&::-webkit-scrollbar-thumb:hover': { background: '#555' },
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
    color: '#0277BD'
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 24,
    color: '#666',
    fontSize: 14,
  },
  inputBox: {
    backgroundColor: '#fff',
    borderRadius: 8,
    marginBottom: 16,
    '& .MuiOutlinedInput-root': {
      '& fieldset': { borderColor: 'rgba(33, 150, 243, 0.3)' },
      '&:hover fieldset': { borderColor: '#2196F3' },
      '&.Mui-focused fieldset': { borderColor: '#0277BD' },
    },
  },

  planButton: {
    background: '#0277BD',
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    padding: '12px',
    borderRadius: 8,
    textTransform: 'none',
    boxShadow: '0 4px 12px rgba(2, 119, 189, 0.3)',
    '&:hover': { background: '#01579B' },
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginTop: 16,
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  timelineDot: {
    backgroundColor: '#0277BD',
    width: 12,
    height: 12,
    borderRadius: '50%',
    marginRight: 16,
    marginTop: 6
  },
  costBox: {
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    padding: 16,
    textAlign: 'center',
    marginTop: 16,
    border: '1px solid #2196F3',
  },
  // Itinerary / result styles
  itineraryList: { paddingTop: 8, paddingBottom: 8 },
  itineraryItem: { paddingTop: 12, paddingBottom: 12 },
  timeBadge: {
    backgroundColor: '#0277BD',
    color: 'white',
    borderRadius: 8,
    padding: '6px 10px',
    fontWeight: 700,
    display: 'inline-block'
  },
  activityTitle: { fontWeight: '700', color: '#333' },
  placeText: { color: '#0277BD', display: 'block', marginTop: 6 },
  addressText: { opacity: 0.7, display: 'block', color: '#666' },
  costText: { color: '#0277BD', fontWeight: 700 },
  itemCostBox: { minWidth: 120, textAlign: 'right' },
  acceptButton: { marginTop: 16 },
  '@global': {
    '.open': {
      transform: 'translateX(0)',
      [theme.breakpoints.up('md')]: {
        transform: 'translateX(0)',
      },
    },
    '.closed': {
      transform: 'translateX(-85%)',
      [theme.breakpoints.down('sm')]: {
        transform: 'translateX(-100%)',
      },
    },
  },
}));

export default function PlanTripPage() {
  const classes = useStyles();
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const locationState = useLocation();
  const [activeSegments, setActiveSegments] = useState([]);
  const navigate = useNavigate();


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

  // Initialize activeSegments when plan is set
  useEffect(() => {
    if (plan?.itinerary) {
      setActiveSegments(Array(plan.itinerary.length - 1).fill(false)); // default: all OFF
    }
  }, [plan]);

  const toggleSegment = (index) => {
    setActiveSegments(prev => {
      const arr = [...prev];
      arr[index] = !arr[index];
      return arr;
    });
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
        <GoongPlanTripMap
          plan={plan}
          activeSegments={activeSegments}
        />
      )}


      {/* Sidebar */}
      <Box data-sidebar="container" className={`${classes.sidebarContainer} ${openModal ? 'open' : 'closed'}`}>
        {/* Header with Close Button */}
        <Box data-sidebar="header" className={classes.sidebarHeader}>
          <Typography className={classes.sidebarTitle}>Lập kế hoạch chuyến đi</Typography>
          <IconButton onClick={() => setOpenModal(!openModal)} className={classes.closeButton}>
            {openModal ? <CloseIcon /> : <SearchIcon />}
          </IconButton>
        </Box>

        {/* Scrollable Content */}
        <Box className={classes.sidebarContent}>
          <Typography className={classes.title}>Lập kế hoạch chuyến đi với AI</Typography>
          <Typography className={classes.subtitle}>Tạo lịch trình hoàn hảo trong vài giây</Typography>

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
                    color: '#0277BD',
                    textAlign: 'center',
                    marginBottom: 16,
                    fontWeight: 'bold'
                  }}
                >
                  {plan.title}
                </Typography>

                <Typography
                  style={{
                    color: '#666',
                    textAlign: 'center',
                    marginBottom: 24
                  }}
                >
                  Lịch trình cá nhân của bạn đã sẵn sàng!
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
                              background: '#0277BD',
                              padding: '6px 12px',
                              borderRadius: 8,
                              marginRight: 16,
                              minWidth: 64,
                              textAlign: 'center',
                              boxShadow: '0 2px 4px rgba(2, 119, 189, 0.2)'
                            }}
                          >
                            <Typography
                              variant="body2"
                              style={{
                                fontWeight: 700,
                                color: 'white',
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
                                  color: '#333'
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
                                    color: '#0277BD',
                                    fontWeight: 500
                                  }}
                                >
                                  {item.place}
                                </Typography>

                                <Typography
                                  variant="body2"
                                  style={{
                                    color: '#666',
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
                                color: '#0277BD',
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
                              backgroundColor: '#e0e0e0',
                              marginLeft: 80,
                              marginRight: 8
                            }}
                          />
                        )}

                        {idx < plan.itinerary.length - 1 && (
                          <div style={{ display: "flex", alignItems: "center", gap: 10, marginLeft: 16 }}>

                            <span style={{ fontSize: 20, marginRight: 8 }}>⬇</span>

                            {/* Toggle button */}
                            <IconButton
                              onClick={() => toggleSegment(idx)}
                              style={{
                                backgroundColor: activeSegments[idx] ? "#4caf50" : "#f44336",
                                color: "white",
                                padding: "6px 16px",
                                borderRadius: "20px",
                                fontWeight: "bold",
                                fontSize: "0.8rem",
                                boxShadow: "0 2px 5px rgba(0,0,0,0.2)"
                              }}
                            >
                              {activeSegments[idx] ? "ON" : "OFF"}
                            </IconButton>

                          </div>
                        )}

                      </React.Fragment>
                    );
                  })}
                </List>

                {/* Total Cost */}
                <Box className={classes.costBox}>
                  <Typography style={{ fontSize: 18, fontWeight: 'bold', color: '#0277BD' }}>
                    Tổng chi phí: {plan.totalCost.toLocaleString()} ₫
                  </Typography>
                </Box>

                {/* Accept Plan */}
                <Button
                  fullWidth
                  className={`${classes.planButton} ${classes.acceptButton}`}
                  onClick={() => {
                    if (!plan) {
                      alert("No trip plan to save!");
                      return;
                    }
                    const token = localStorage.getItem('token');
                    if (!token) {
                      setTimeout(() => navigate('/login'), 1500);
                      alert("Ban cần đăng nhập để lưu kế hoạch chuyến đi!");
                      return;
                    }
                    saveTrip(plan);
                  }
                  }
                  startIcon={<EmojiEventsIcon />}
                >
                  Chấp nhận kế hoạch
                </Button>

              </Paper>
            </Box>
          )}

        </Box>
      </Box>
    </Box>
  );
}