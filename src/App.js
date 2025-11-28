import React, { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@material-ui/core/styles";
import Header from './Header';
import HistoryPage from './pages/HistoryPage';
import RoutesPage from "./pages/RoutesPage";
import BusMapPage from "./pages/BusMapPage";
import CameraMapNew from "./pages/CameraMapNew";
import SOSMapPage from './pages/SOSMapPage';
import Login from "./pages/Login";
import Register from "./pages/Register";
import EarthTestPage from "./pages/EarthTestPage";
import { Box } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import { MapProvider } from './contexts/MapContext';

// Define light and dark themes
const lightTheme = createTheme({
  palette: {
    type: "light",
    primary: {
      main: "#0277BD",
    },
    secondary: {
      main: "#FFA726",
    },
    background: {
      default: "#f5f7fa",
      paper: "#ffffff",
    },
    text: {
      primary: "#212121",
      secondary: "#666666",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  overrides: {
    MuiPaper: {
      root: {
        backgroundColor: "#ffffff",
        color: "#212121",
      },
    },
    MuiCard: {
      root: {
        backgroundColor: "#ffffff",
        color: "#212121",
      },
    },
  },
});

const darkTheme = createTheme({
  palette: {
    type: "dark",
    primary: {
      main: "#0277BD",
    },
    secondary: {
      main: "#FFA726",
    },
    background: {
      default: "#121212",
      paper: "#1e1e1e",
    },
    text: {
      primary: "#ffffff",
      secondary: "#b0b0b0",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  overrides: {
    MuiPaper: {
      root: {
        backgroundColor: "#1e1e1e",
        color: "#ffffff",
      },
    },
    MuiCard: {
      root: {
        backgroundColor: "#1e1e1e",
        color: "#ffffff",
      },
    },
    MuiOutlinedInput: {
      root: {
        backgroundColor: "#2a2a2a",
        color: "#ffffff",
      },
    },
    MuiInputBase: {
      root: {
        color: "#ffffff",
      },
      input: {
        color: "#ffffff",
        "&::placeholder": {
          color: "rgba(255, 255, 255, 0.5)",
          opacity: 1,
        },
      },
    },
  },
});

const useStyles = makeStyles((theme) => ({
  root: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    backgroundColor: theme.palette.background.default,
    color: theme.palette.text.primary,
    transition: "background-color 0.3s ease, color 0.3s ease",
  },
  content: {
    flex: 1,
    overflow: "hidden",
    backgroundColor: theme.palette.background.default,
    transition: "background-color 0.3s ease, color 0.3s ease",
    marginTop: 50,
    [theme.breakpoints.down('sm')]: {
      marginTop: 56,
    },
  },
}));

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const theme = darkMode ? darkTheme : lightTheme;
  const classes = useStyles();

  const handleToggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  // Validate token on app load
  React.useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          // Try to fetch user data to validate token
          const response = await fetch('https://api.hcmus.fit/api/user/locations', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          
          if (response.status === 401) {
            // Token is invalid or expired
            console.warn('Token expired on app load, clearing...');
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            window.dispatchEvent(new Event('auth-change'));
          }
        } catch (err) {
          console.error('Token validation error:', err);
        }
      }
    };
    
    validateToken();
  }, []);

  // Update root element attribute for dark mode
  React.useEffect(() => {
    const rootElement = document.getElementById("root");
    if (rootElement) {
      rootElement.setAttribute("data-dark-mode", darkMode);
      if (darkMode) {
        rootElement.style.backgroundColor = "#121212";
        rootElement.style.color = "#ffffff";
      } else {
        rootElement.style.backgroundColor = "#f5f7fa";
        rootElement.style.color = "#212121";
      }
    }
  }, [darkMode]);

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <MapProvider zoomThreshold={2}>
          <Box className={classes.root}>
            <Header darkMode={darkMode} onToggleDarkMode={() => setDarkMode(!darkMode)} />
            <Box className={classes.content} data-dark-mode={darkMode}>
              <Routes>
                <Route path="/" element={<RoutesPage darkMode={darkMode} />} />
                <Route path="/routes" element={<RoutesPage darkMode={darkMode} />} />
                <Route path="/busmap" element={<BusMapPage darkMode={darkMode} />} />
                <Route path="/cameras" element={<CameraMapNew />} />
                <Route path="/sos" element={<SOSMapPage />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/earth-test" element={<EarthTestPage />} />
              </Routes>
            </Box>
          </Box>
        </MapProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
