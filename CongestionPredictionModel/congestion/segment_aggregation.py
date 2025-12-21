import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

class CameraToSegmentMapper: 
    def __init__(self, camera_locations_file='camera_locations.json',
                 db_path='detections_optimized.db'):
        self.db_path = db_path
        
        # Load camera GPS coordinates
        with open(camera_locations_file, 'r', encoding='utf-8') as f:
            self.camera_locations = json.load(f)
                
        # Count how many have valid GPS
        valid_gps = sum(1 for loc in self.camera_locations.values() 
                       if loc.get('lat') and loc.get('lon'))
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two GPS points in meters
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def create_simple_segments(self, max_distance_m: float = 200.0):
        conn = sqlite3.connect(self.db_path)

        # Get unique cameras from detections
        query = "SELECT DISTINCT camera_id, camera_name FROM detections"
        cameras_in_db = pd.read_sql_query(query, conn)
        conn.close()

        # Build camera list with GPS
        cameras = []
        for _, row in cameras_in_db.iterrows():
            cam_id = row["camera_id"]
            cam_name = row["camera_name"]

            loc = self.camera_locations.get(cam_id, {})
            lat = loc.get("lat")
            lon = loc.get("lon")

            cameras.append(
                {
                    "camera_id": cam_id,
                    "camera_name": cam_name,
                    "lat": lat,
                    "lon": lon,
                }
            )

        # Split into with/without GPS
        gps_cameras = [c for c in cameras if c["lat"] is not None and c["lon"] is not None]
        no_gps_cameras = [c for c in cameras if c["lat"] is None or c["lon"] is None]

        segments = []
        visited = set()
        seg_idx = 1

        # Helper to compute distance 
        def dist(c1, c2):
            return self.haversine_distance(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
        # Cluster GPS cameras by distance
        for cam in gps_cameras:
            cid = cam["camera_id"]
            if cid in visited:
                continue

            queue = [cam]
            visited.add(cid)
            cluster = []

            while queue:
                current = queue.pop()
                cluster.append(current)

                for other in gps_cameras:
                    oid = other["camera_id"]
                    if oid in visited:
                        continue

                    if dist(current, other) <= max_distance_m:
                        visited.add(oid)
                        queue.append(other)

            # Compute centroid
            lats = [c["lat"] for c in cluster]
            lons = [c["lon"] for c in cluster]
            centroid_lat = sum(lats) / len(lats)
            centroid_lon = sum(lons) / len(lons)

            segment_id = f"SEG_{seg_idx:04d}"
            seg_idx += 1

            segments.append(
                {
                    "segment_id": segment_id,
                    "segment_name": cluster[0]["camera_name"],  # can customize
                    "camera_ids": [c["camera_id"] for c in cluster],
                    "lat": centroid_lat,
                    "lon": centroid_lon,
                    "segment_type": "cluster_multi" if len(cluster) > 1 else "single_camera",
                }
            )

        # Add no-GPS cameras as individual segments
        for cam in no_gps_cameras:
            segment_id = f"SEG_NOGPS_{cam['camera_id']}"
            segments.append(
                {
                    "segment_id": segment_id,
                    "segment_name": cam["camera_name"],
                    "camera_ids": [cam["camera_id"]],
                    "lat": None,
                    "lon": None,
                    "segment_type": "no_gps",
                }
            )

        df_segments = pd.DataFrame(segments)

        # Print summary
        print(f"\n{'='*70}")
        print("SEGMENT MAPPING CREATED (CLUSTERED BY DISTANCE)")
        print(f"{'='*70}")
        print(f"Total cameras: {len(cameras)}")
        print(f"Total segments: {len(df_segments)}")
        print(f"With GPS: {len(gps_cameras)}")
        print(f"Without GPS: {len(no_gps_cameras)}")

        # Some basic stats on cluster sizes (only GPS segments)
        gps_seg_sizes = df_segments[df_segments["segment_type"] != "no_gps"]["camera_ids"].apply(
            len
        )
        if not gps_seg_sizes.empty:
            print(f"Avg cameras per GPS segment: {gps_seg_sizes.mean():.2f}")
            print(f"Max cameras in a segment: {gps_seg_sizes.max()}")

        return df_segments

    
    def save_segments(self, df_segments, output_file='segments.csv'):
        df_to_save = df_segments.copy()
        if "camera_ids" in df_to_save.columns:
            df_to_save["camera_ids"] = df_to_save["camera_ids"].apply(json.dumps)

        df_to_save.to_csv(output_file, index=False)


class SegmentAggregator:    
    def __init__(self, db_path='detections_optimized.db', 
                 segments_file='segments.csv'):
        self.db_path = db_path
        self.segments = pd.read_csv(segments_file)
        
        # Build camera_id -> segment_id mapping from segments.csv
        self.camera_to_segment = {}

        if 'camera_ids' in self.segments.columns:
            for _, row in self.segments.iterrows():
                seg_id = row['segment_id']
                raw = row['camera_ids']
                try:
                    cam_ids = json.loads(raw) if isinstance(raw, str) else []
                except json.JSONDecodeError:
                    # Fallback: treat as single id if not valid JSON
                    cam_ids = [raw]

                for cam_id in cam_ids:
                    if cam_id:  # avoid empty
                        self.camera_to_segment[str(cam_id)] = seg_id
        else:
            # Fallback: segment_id == camera_id (old behavior)
            for _, row in self.segments.iterrows():
                seg_id = str(row['segment_id'])
                self.camera_to_segment[seg_id] = seg_id
    
    def aggregate_to_time_windows(self, window_minutes=15):
        conn = sqlite3.connect(self.db_path)
        
        # Load all detections
        query = """
            SELECT 
                camera_id,
                timestamp_dt,
                total_vehicles,
                car_count,
                motorcycle_count,
                bus_count,
                truck_count
            FROM detections
            WHERE timestamp_dt IS NOT NULL
            ORDER BY camera_id, timestamp_dt
        """
    
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamp to datetime
        df["timestamp_dt"] = pd.to_datetime(df["timestamp_dt"], format="mixed", errors="coerce")


        # Map camera_id -> segment_id using precomputed mapping
        df['camera_id'] = df['camera_id'].astype(str)
        df['segment_id'] = df['camera_id'].map(self.camera_to_segment)

        # Fallback for cameras not present in segments.csv
        missing_mask = df['segment_id'].isna()
        if missing_mask.any():
            missing_cams = df.loc[missing_mask, 'camera_id'].nunique()
            print(f"⚠️ {missing_cams} cameras not in segments.csv, using camera_id as segment_id")
            df.loc[missing_mask, 'segment_id'] = df.loc[missing_mask, 'camera_id']

        # Create time windows (round down to nearest window_minutes)
        df['time_window'] = df['timestamp_dt'].dt.floor(f'{window_minutes}min')
        
        # Aggregate by segment and time window        
        agg_df = df.groupby(['segment_id', 'time_window']).agg({
            'total_vehicles': ['mean', 'std', 'min', 'max', 'count'],
            'car_count': 'mean',
            'motorcycle_count': 'mean',
            'bus_count': 'mean',
            'truck_count': 'mean'
        }).reset_index()
        
        # Flatten column names
        agg_df.columns = [
            'segment_id', 'time_window',
            'avg_vehicles', 'std_vehicles', 'min_vehicles', 'max_vehicles', 'sample_count',
            'avg_cars', 'avg_motorcycles', 'avg_buses', 'avg_trucks'
        ]
        
        # Add segment info (name + centroid lat/lon)
        agg_df = agg_df.merge(
            self.segments[['segment_id', 'segment_name', 'lat', 'lon']],
            on='segment_id',
            how='left'
        )
        
        # Add time features
        agg_df['hour'] = agg_df['time_window'].dt.hour
        agg_df['day_of_week'] = agg_df['time_window'].dt.dayofweek
        agg_df['is_weekend'] = (agg_df['day_of_week'] >= 5).astype(int)
        agg_df['is_rush_hour'] = (
            ((agg_df['hour'] >= 7) & (agg_df['hour'] <= 9)) |
            ((agg_df['hour'] >= 17) & (agg_df['hour'] <= 19))
        ).astype(int)
        
        print(f"\n{'='*70}")
        print(f"AGGREGATION COMPLETE")
        print(f"{'='*70}")
        print(f"Original detections: {len(df):,}")
        print(f"Aggregated time windows: {len(agg_df):,}")
        print(f"Unique segments: {agg_df['segment_id'].nunique()}")
        print(f"Time range: {agg_df['time_window'].min()} to {agg_df['time_window'].max()}")
        print(f"Average samples per window: {agg_df['sample_count'].mean():.1f}")
        
        return agg_df
    
    def save_aggregated_data(self, agg_df, output_file='segment_aggregated.csv'):
        agg_df.to_csv(output_file, index=False)
     
        return output_file


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":    
    # Map cameras to segments
    mapper = CameraToSegmentMapper(
        camera_locations_file='camera_locations.json',
        db_path='detections_optimized.db'
    )
    
    segments_df = mapper.create_simple_segments()
    mapper.save_segments(segments_df, 'segments.csv')
    
    # Aggregate to time windows
    aggregator = SegmentAggregator(
        db_path='detections_optimized.db',
        segments_file='segments.csv'
    )
    
    agg_df = aggregator.aggregate_to_time_windows(window_minutes=15)
    
    # Save final output (no congestion logic here)
    output_file = aggregator.save_aggregated_data(agg_df, 'segment_aggregated.csv')
    
    print(f"\n{'='*70}")
    print(f"✓ PURE AGGREGATION COMPLETE")
    print(f"{'='*70}")
    print(f"Output file: {output_file}")
    print(f"Ready for downstream congestion classification or model training.")
