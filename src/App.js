import React, { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@material-ui/core/styles";
import Header_v2 from "./Header_v2";
import RoutesPage from "./pages/RoutesPage";
import BusMapPage from "./pages/BusMapPage";
import { Box } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

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
  },
}));

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const theme = darkMode ? darkTheme : lightTheme;
  const classes = useStyles();

  const handleToggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

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
        <Box className={classes.root}>
          <Header_v2 darkMode={darkMode} onToggleDarkMode={handleToggleDarkMode} />
          <Box className={classes.content} data-dark-mode={darkMode}>
            <Routes>
              <Route path="/" element={<RoutesPage darkMode={darkMode} />} />
              <Route path="/routes" element={<RoutesPage darkMode={darkMode} />} />
              <Route path="/busmap" element={<BusMapPage darkMode={darkMode} />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
