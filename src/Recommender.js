import React from "react";
import { Typography, Grid, Card, CardContent, LinearProgress } from "@material-ui/core";

export default function Recommender({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) {
    return <Typography color="textSecondary">No recommendations available. Select a place to get in-trip suggestions.</Typography>;
  }

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Top Recommendations
      </Typography>

      <Grid container spacing={2}>
        {recommendations.map((r) => (
          <Grid item xs={12} sm={6} key={r.id}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1">{r.mode}</Typography>
                <Typography variant="body2" color="textSecondary">
                  ETA: {r.eta} • Cost: {r.cost}
                </Typography>

                <div style={{ marginTop: 12 }}>
                  <LinearProgress variant="determinate" value={Math.round((r.confidence || 0) * 100)} />
                  <Typography variant="caption">Confidence: {Math.round((r.confidence || 0) * 100)}%</Typography>
                </div>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}
