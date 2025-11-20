import React from "react";
import { AppBar, Toolbar, Typography, Box, IconButton, Tabs, Tab, makeStyles, Button, Menu, MenuItem, Avatar } from "@material-ui/core";
import { Brightness4, Brightness7, AccountCircle, History } from "@material-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  appBar: {
    background: "linear-gradient(135deg, #1a237e 0%, #283593 100%)", // Darker, more professional blue
    boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
    minHeight: 50,
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
  },
  tabs: {
    marginLeft: theme.spacing(4),
    "& .MuiTabs-indicator": {
      backgroundColor: "#FF8E53",
      height: 3,
      borderRadius: 3,
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
  if (location.pathname === "/busmap") tabValue = 1;

  if (location.pathname === "/cameras") tabValue = 2;

  if (location.pathname === "/history") tabValue = 3;


  const handleTabChange = (event, newValue) => {
    if (newValue === 0) navigate("/routes");
    else if (newValue === 1) navigate("/busmap");
    else if (newValue == 2) navigate("/cameras")
    else if (newValue === 3) navigate("/history");

  };

  return (
    <AppBar position="static" className={classes.appBar}>
      <Toolbar className={classes.toolbar}>
        {/* Left Section: Logo & Title */}
        <Box className={classes.logoSection} onClick={() => navigate('/')}>
          <Typography variant="h6" className={classes.title}>
            Unified Mobility
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
                style={{ backgroundColor: '#FF8E53', color: 'white' }}
                onClick={() => navigate('/register')}
              >
                Sign Up
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}
