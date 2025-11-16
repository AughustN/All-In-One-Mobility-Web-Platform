import React, { useState } from "react";
import {
  OutlinedInput,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  FormControlLabel,
  Checkbox,
  Slider,
  Grid,
  Typography,
} from "@material-ui/core";

const NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search?";

export default function SearchBox(props) {
  const { setSelectPosition } = props;
  const [searchText, setSearchText] = useState("");
  const [listPlace, setListPlace] = useState([]);
  const [transportTypes, setTransportTypes] = useState({ bus: true, taxi: true, walk: true });
  const [maxWalking, setMaxWalking] = useState(1000);
  const [busOnly, setBusOnly] = useState(false);

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex" }}>
        <div style={{ flex: 1 }}>
          <OutlinedInput
            style={{ width: "100%" }}
            value={searchText}
            onChange={(event) => {
              setSearchText(event.target.value);
            }}
          />
        </div>
        <div
          style={{ display: "flex", alignItems: "center", padding: "0px 20px" }}
        >
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              // Search
              const params = {
                q: searchText,
                format: "json",
                addressdetails: 1,
                polygon_geojson: 0,
              };
              const queryString = new URLSearchParams(params).toString();
              const requestOptions = {
                method: "GET",
                redirect: "follow",
              };
              fetch(`${NOMINATIM_BASE_URL}${queryString}`, requestOptions)
                .then((response) => response.text())
                .then((result) => {
                  console.log(JSON.parse(result));
                  setListPlace(JSON.parse(result));
                })
                .catch((err) => console.log("err: ", err));
            }}
          >
            Search
          </Button>
        </div>
      </div>
      <div style={{ padding: 12 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12}>
            <Typography variant="subtitle2">Transport types</Typography>
          </Grid>

          <Grid item>
            <FormControlLabel
              control={<Checkbox checked={transportTypes.bus} onChange={(e) => setTransportTypes({ ...transportTypes, bus: e.target.checked })} />}
              label="Bus"
            />
          </Grid>
          <Grid item>
            <FormControlLabel
              control={<Checkbox checked={transportTypes.taxi} onChange={(e) => setTransportTypes({ ...transportTypes, taxi: e.target.checked })} />}
              label="Taxi"
            />
          </Grid>
          <Grid item>
            <FormControlLabel
              control={<Checkbox checked={transportTypes.walk} onChange={(e) => setTransportTypes({ ...transportTypes, walk: e.target.checked })} />}
              label="Walk"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle2">Max walking distance (m)</Typography>
            <Slider
              value={maxWalking}
              onChange={(e, v) => setMaxWalking(v)}
              aria-labelledby="max-walking"
              valueLabelDisplay="auto"
              min={0}
              max={5000}
            />
          </Grid>

          <Grid item>
            <FormControlLabel control={<Checkbox checked={busOnly} onChange={(e) => setBusOnly(e.target.checked)} />} label="Bus-only" />
          </Grid>
        </Grid>
      </div>
      <div>
        <List component="nav" aria-label="main mailbox folders">
          {listPlace.map((item) => {
            return (
              <div key={item?.place_id}>
                <ListItem
                  button
                  onClick={() => {
                    // set selection (item has lat/lon as strings)
                    setSelectPosition(item);
                  }}
                >
                  <ListItemIcon>
                    <img
                      src="./placeholder.png"
                      alt="Placeholder"
                      style={{ width: 38, height: 38 }}
                    />
                  </ListItemIcon>
                  <ListItemText primary={item?.display_name} />
                </ListItem>
                <Divider />
              </div>
            );
          })}
        </List>
      </div>
    </div>
  );
}
