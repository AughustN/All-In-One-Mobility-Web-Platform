import React from "react";
import { AppBar, Toolbar, Typography, Box, IconButton, Tabs, Tab, makeStyles, Button, Menu, MenuItem, Avatar, Drawer, List, ListItem, ListItemText, Divider } from "@material-ui/core";
import { Brightness4, Brightness7, AccountCircle, History, Menu as MenuIcon } from "@material-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  appBar: {
    background: "linear-gradient(135deg, #498ac7ff 0%, #a5a6afff 100%)",
    boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1300,
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
    minHeight: 50,
    [theme.breakpoints.down('sm')]: {
      minHeight: 56,
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
    },
  },
  logoSection: {
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
  },
  logoIcon: {
    fontSize: 32,
    marginRight: theme.spacing(1),
  },
  title: {
    fontWeight: 800,
    fontSize: "1.4rem",
    letterSpacing: "0.5px",
    background: "linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    [theme.breakpoints.down('sm')]: {
      fontSize: "1.1rem",
    },
  },
  mobileMenuButton: {
    display: 'none',
    [theme.breakpoints.down('sm')]: {
      display: 'block',
    },
  },
  drawerPaper: {
    width: 250,
    paddingTop: theme.spacing(2),
  },
  drawerItem: {
    padding: '12px 24px',
    '&:hover': {
      backgroundColor: 'rgba(2, 119, 189, 0.08)',
    },
  },
  activeDrawerItem: {
    backgroundColor: 'rgba(2, 119, 189, 0.15)',
    borderLeft: '4px solid #0277BD',
    '& .MuiListItemText-primary': {
      fontWeight: 600,
      color: '#0277BD',
    },
  },
  tabs: {
    marginLeft: theme.spacing(4),
    "& .MuiTabs-indicator": {
      backgroundColor: "#FF8E53",
      height: 3,
      borderRadius: 3,
    },
    [theme.breakpoints.down('sm')]: {
      display: 'none',
    },
  },
  tab: {
    color: "rgba(255, 255, 255, 0.8)",
    fontWeight: 600,
    fontSize: "0.95rem",
    minWidth: 100,
    "&.Mui-selected": {
      color: "#fff",
    },
    textTransform: "none",
    transition: "all 0.3s",
    '&:hover': {
      color: "#fff",
      opacity: 1,
    }
  },
  rightSection: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing(1),
  },
  authButton: {
    borderRadius: 20,
    padding: "6px 20px",
    textTransform: "none",
    fontWeight: 600,
    boxShadow: "none",
    '&:hover': {
      boxShadow: "0 2px 8px rgba(255,255,255,0.2)",
    }
  },
  userChip: {
    display: 'flex',
    alignItems: 'center',
    padding: '4px 12px',
    borderRadius: 24,
    backgroundColor: 'rgba(255,255,255,0.1)',
    cursor: 'pointer',
    transition: 'background 0.2s',
    '&:hover': {
      backgroundColor: 'rgba(255,255,255,0.2)',
    }
  }
}));

export default function Header({ darkMode, onToggleDarkMode }) {
  const classes = useStyles();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = React.useState(localStorage.getItem('username'));
  const [anchorEl, setAnchorEl] = React.useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  React.useEffect(() => {
    const handleAuthChange = () => {
      setUsername(localStorage.getItem('username'));
    };
    window.addEventListener('auth-change', handleAuthChange);
    return () => window.removeEventListener('auth-change', handleAuthChange);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setUsername(null);
    setAnchorEl(null);
    navigate('/login');
  };

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Determine active tab
  let tabValue = 0;
  if (location.pathname === "/routes") tabValue = 0;
  else if (location.pathname === "/busmap") tabValue = 1;
  else if (location.pathname === "/cameras") tabValue = 2;
  else if (location.pathname === "/sos") tabValue = 3; // Tab mới số 3
  else if (location.pathname === "/planTrip") tabValue = 4;
  else if (location.pathname === "/history") tabValue = 5;

  const handleTabChange = (event, newValue) => {
    if (newValue === 0) navigate("/routes");
    else if (newValue === 1) navigate("/busmap");
    else if (newValue === 2) navigate("/cameras");
    else if (newValue === 3) navigate("/sos"); // Link tới trang SOS
    else if (newValue === 4) navigate("/planTrip");
    else if (newValue === 5) navigate("/history");
  };

  return (
    <>
      <AppBar position="fixed" className={classes.appBar}>
        <Toolbar className={classes.toolbar}>
          {/* Mobile Menu Button */}
          <IconButton
            edge="start"
            color="inherit"
            className={classes.mobileMenuButton}
            onClick={() => setMobileMenuOpen(true)}
          >
            <MenuIcon />
          </IconButton>

          {/* Left Section: Logo & Title */}
          <Box className={classes.logoSection} onClick={() => navigate('/')}>
            <Typography variant="h6" className={classes.title}>
              MAP APP HCMUS
            </Typography>
          </Box>

          {/* Center Section: Navigation Tabs */}
          <Box flexGrow={1} display="flex" justifyContent="center">
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              className={classes.tabs}
              centered
            >
              <Tab label="Find Routes" className={classes.tab} />
              <Tab label="Bus Map" className={classes.tab} />
              <Tab label="Cameras Map" className={classes.tab} />
              <Tab label="SOS Map" className={classes.tab} />
              <Tab label="Plan Trip" className={classes.tab} />
              {username && <Tab label="History" className={classes.tab} />}
            </Tabs>
          </Box>

          {/* Right Section: Auth & Dark Mode */}
          <Box className={classes.rightSection}>
            <IconButton
              color="inherit"
              onClick={onToggleDarkMode}
              style={{ marginRight: 8 }}
            >
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>

            {username ? (
              <>
                <Box className={classes.userChip} onClick={handleMenuOpen}>
                  <Avatar style={{ width: 32, height: 32, marginRight: 8, backgroundColor: '#FF8E53' }}>
                    {username[0].toUpperCase()}
                  </Avatar>
                  <Typography variant="subtitle2" style={{ fontWeight: 600 }}>
                    {username}
                  </Typography>
                </Box>
                <Menu
                  anchorEl={anchorEl}
                  keepMounted
                  open={Boolean(anchorEl)}
                  onClose={handleMenuClose}
                  getContentAnchorEl={null}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                >
                  <MenuItem onClick={() => { handleMenuClose(); navigate('/history'); }}>
                    <History style={{ marginRight: 8, fontSize: 20 }} /> Lịch sử
                  </MenuItem>
                  <MenuItem onClick={handleLogout}>Logout</MenuItem>
                </Menu>
              </>
            ) : (
              <>
                <Button
                  color="inherit"
                  className={classes.authButton}
                  onClick={() => navigate('/login')}
                  style={{ marginRight: 8 }}
                >
                  Login
                </Button>
                <Button
                  variant="contained"
                  className={classes.authButton}
                  // style={{ backgroundColor: '#FF8E53', color: 'white' }}
                  onClick={() => navigate('/register')}
                >
                  Sign Up
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer Menu */}
      <Drawer
        anchor="left"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        classes={{ paper: classes.drawerPaper }}
      >
        <Box style={{ padding: '16px 24px', borderBottom: '1px solid #e0e0e0' }}>
          <Typography variant="h6" style={{ fontWeight: 700, color: '#0277BD' }}>
            Menu
          </Typography>
        </Box>

        <List>
          <ListItem
            button
            className={`${classes.drawerItem} ${tabValue === 0 ? classes.activeDrawerItem : ''}`}
            onClick={() => {
              navigate('/routes');
              setMobileMenuOpen(false);
            }}
          >
            <ListItemText primary=" Find Routes" />
          </ListItem>

          <ListItem
            button
            className={`${classes.drawerItem} ${tabValue === 1 ? classes.activeDrawerItem : ''}`}
            onClick={() => {
              navigate('/busmap');
              setMobileMenuOpen(false);
            }}
          >
            <ListItemText primary=" Bus Map" />
          </ListItem>

          <ListItem
            button
            className={`${classes.drawerItem} ${tabValue === 2 ? classes.activeDrawerItem : ''}`}
            onClick={() => {
              navigate('/cameras');
              setMobileMenuOpen(false);
            }}
          >
            <ListItemText primary=" Cameras Map" />
          </ListItem>

          <ListItem
            button
            className={`${classes.drawerItem} ${tabValue === 3 ? classes.activeDrawerItem : ''}`}
            onClick={() => {
              navigate('/sos');
              setMobileMenuOpen(false);
            }}
          >
            <ListItemText primary=" SOS Map" />
          </ListItem>

          <ListItem
            button
            className={`${classes.drawerItem} ${tabValue === 4 ? classes.activeDrawerItem : ''}`}
            onClick={() => {
              navigate('/planTrip');
              setMobileMenuOpen(false);
            }}
          >
            <ListItemText primary=" Plan Trip" />
          </ListItem>

          {username && (
            <ListItem
              button
              className={`${classes.drawerItem} ${tabValue === 5 ? classes.activeDrawerItem : ''}`}
              onClick={() => {
                navigate('/history');
                setMobileMenuOpen(false);
              }}
            >
              <ListItemText primary=" History" />
            </ListItem>
          )}
        </List>

        <Divider />

        <Box style={{ padding: '16px 24px' }}>
          {username ? (
            <Box>
              <Typography variant="subtitle2" style={{ color: '#666', marginBottom: 8 }}>
                Logged in as
              </Typography>
              <Box style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                <Avatar style={{ width: 32, height: 32, marginRight: 8, backgroundColor: '#FF8E53' }}>
                  {username[0].toUpperCase()}
                </Avatar>
                <Typography variant="body1" style={{ fontWeight: 600 }}>
                  {username}
                </Typography>
              </Box>
              <Button
                fullWidth
                variant="outlined"
                color="secondary"
                onClick={() => {
                  handleLogout();
                  setMobileMenuOpen(false);
                }}
              >
                Logout
              </Button>
            </Box>
          ) : (
            <Box>
              <Button
                fullWidth
                variant="outlined"
                color="primary"
                style={{ marginBottom: 8 }}
                onClick={() => {
                  navigate('/login');
                  setMobileMenuOpen(false);
                }}
              >
                Login
              </Button>
              <Button
                fullWidth
                variant="contained"
                style={{ backgroundColor: '#FF8E53', color: 'white' }}
                onClick={() => {
                  navigate('/register');
                  setMobileMenuOpen(false);
                }}
              >
                Sign Up
              </Button>
            </Box>
          )}
        </Box>
      </Drawer>
    </>
  );
}
