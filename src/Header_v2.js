import React from "react";
import { AppBar, Toolbar, Typography, Box, IconButton } from "@material-ui/core";
import { Brightness4, Brightness7 } from "@material-ui/icons";
import { useLocation, useNavigate } from "react-router-dom";

function Header({ darkMode, onToggleDarkMode }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AppBar
      position="fixed"
      style={{ background: "linear-gradient(135deg, #0e1227 0%, #dad4e0ff 100%)" }}
    >
      <Toolbar style={{ display: "flex", justifyContent: "center", position: "relative" }}>
        
        {/* Navigation center */}
        <Box style={{ display: "flex", gap: "20px", position: "absolute", left: "50%", transform: "translateX(-50%)" }}>
          <button
            onClick={() => navigate("/routes")}
            style={{
              background: location.pathname === "/routes" ? "#fff" : "transparent",
              color: location.pathname === "/routes" ? "#667eea" : "#fff",
              border: "none",
              padding: "8px 16px",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "500",
              fontSize: "16px"
            }}
          >
            Find Routes
          </button>

          <button
            onClick={() => navigate("/busmap")}
            style={{
              background: location.pathname === "/busmap" ? "#fff" : "transparent",
              color: location.pathname === "/busmap" ? "#667eea" : "#fff",
              border: "none",
              padding: "8px 16px",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "500",
              fontSize: "16px"
            }}
          >
            Bus Map
          </button>
        </Box>

        {/* Dark mode toggle — right side */}
        <IconButton
          color="inherit"
          onClick={onToggleDarkMode}
          style={{ position: "absolute", right: "16px" }}
        >
          {darkMode ? <Brightness7 /> : <Brightness4 />}
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
