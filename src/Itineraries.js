import React, { useState } from "react";
import {
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Collapse,
  List,
  ListItem,
  ListItemText,
} from "@material-ui/core";

export default function Itineraries({ itineraries = [] }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!itineraries || itineraries.length === 0) {
    return <Typography color="textSecondary">No itineraries to display. Search for a place to see suggestions.</Typography>;
  }

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Itineraries
      </Typography>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {itineraries.map((it) => (
          <Card key={it.id} variant="outlined">
            <CardContent style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <Typography variant="subtitle1">{it.label}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {it.time || it.totalTime} • {it.distance || "5 km"}
                </Typography>
              </div>

              <div style={{ textAlign: "right" }}>
                <Typography variant="subtitle1">{it.cost}</Typography>
                <Typography variant="body2" color="textSecondary">
                  Feasibility: {it.feasibility}
                </Typography>
              </div>
            </CardContent>

            <CardActions>
              <Button size="small" color="primary" onClick={() => setExpandedId(expandedId === it.id ? null : it.id)}>
                {expandedId === it.id ? "Hide details" : "Show details"}
              </Button>
            </CardActions>

            <Collapse in={expandedId === it.id} timeout="auto" unmountOnExit>
              <CardContent>
                <Typography variant="subtitle2">Details</Typography>
                <List dense>
                  {it.stops && it.stops.map((b, i) => (
                    <ListItem key={i}>
                      <ListItemText primary={`${b.name || b.from}`} secondary={`${b.time || b.start} • ${b.duration}`} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Collapse>
          </Card>
        ))}
      </div>
    </div>
  );
}
