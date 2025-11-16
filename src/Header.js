import React from "react";
import { AppBar, Toolbar, Typography, Box, IconButton, Tabs, Tab, makeStyles } from "@material-ui/core";
import { Brightness4, Brightness7 } from "@material-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  appBar: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    paddingLeft: theme.spacing(3),
    paddingRight: theme.spacing(3),
  },
  title: {
    fontWeight: 700,
    fontSize: "1.5rem",
    letterSpacing: "-0.5px",
  },
  tabs: {
    marginLeft: theme.spacing(4),
    minHeight: 64,
    "& .MuiTabs-indicator": {
      backgroundColor: "#fff",
      height: 3,
    },
  },
  tab: {
    color: "rgba(255, 255, 255, 0.7)",
    fontWeight: 500,
    fontSize: "1rem",
    "&.Mui-selected": {
      color: "#fff",
    },
    textTransform: "none",
    marginRight: theme.spacing(2),
  },
  rightSection: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing(1),
  },
}));

export default function Header({ darkMode, onToggleDarkMode }) {
  const classes = useStyles();
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab based on current location
  const tabValue = location.pathname === "/busmap" ? 1 : 0;

  const handleTabChange = (event, newValue) => {
    if (newValue === 0) {
      navigate("/routes");
    } else {
      navigate("/busmap");
    }
  };

  return (
    <AppBar position="static" className={classes.appBar}>
      <Toolbar className={classes.toolbar}>
        {/* Left Section: Title */}
        <Box style={{ display: "flex", alignItems: "center" }}>
          <Typography variant="h6" className={classes.title}>
            🗺️ Unified Mobility
          </Typography>

          {/* Navigation Tabs */}
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            className={classes.tabs}
            indicatorColor="primary"
          >
            <Tab label="🚩 Find Routes" className={classes.tab} />
            <Tab label="🚌 Bus Map" className={classes.tab} />
          </Tabs>
        </Box>

        {/* Right Section: Dark Mode Toggle */}
        <Box className={classes.rightSection}>
          <IconButton
            color="inherit"
            onClick={onToggleDarkMode}
            title={darkMode ? "Light mode" : "Dark mode"}
          >
            {darkMode ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
