import React, { useState } from "react";
import {
  OutlinedInput,
  Button,
  Grid,
  Typography,
  Box,
} from "@material-ui/core";

export default function SearchBoxBus(props) {
  const { setSelectPosition } = props;
  const [fromLocation, setFromLocation] = useState("");
  const [toLocation, setToLocation] = useState("");

  const handleSearch = () => {
    console.log("Bus search with:", {
      from: fromLocation,
      to: toLocation,
    });
    // API call would go here
  };

  return (
    <Box style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* From Location */}
      <Box>
        <Typography variant="subtitle2" style={{ marginBottom: "8px", fontWeight: "bold" }}>
           From (Điểm đi)
        </Typography>
        <OutlinedInput
          fullWidth
          placeholder="Enter starting location"
          value={fromLocation}
          onChange={(e) => setFromLocation(e.target.value)}
          style={{ backgroundColor: "#f9f9f9" }}
        />
      </Box>

      {/* To Location */}
      <Box>
        <Typography variant="subtitle2" style={{ marginBottom: "8px", fontWeight: "bold" }}>
           To (Điểm tới)
        </Typography>
        <OutlinedInput
          fullWidth
          placeholder="Enter destination"
          value={toLocation}
          onChange={(e) => setToLocation(e.target.value)}
          style={{ backgroundColor: "#f9f9f9" }}
        />
      </Box>

      {/* Bus Info */}
      <Box
        style={{
          backgroundColor: "#e3f2fd",
          padding: "12px",
          borderRadius: "4px",
          textAlign: "center",
          borderLeft: "4px solid #0277BD",
        }}
      >
        <Typography variant="body2" style={{ fontWeight: "bold", color: "#0277BD" }}>
           Bus Only Routes
        </Typography>
        <Typography variant="caption" style={{ color: "#0277BD" }}>
          Showing only public bus transportation
        </Typography>
      </Box>

      {/* Search Button */}
      <Button
        variant="contained"
        color="primary"
        size="large"
        fullWidth
        onClick={handleSearch}
        style={{
          padding: "12px",
          fontWeight: "bold",
          backgroundColor: "#0277BD",
        }}
      >
         Find Bus Routes
      </Button>
    </Box>
  );
}
