import json
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import requests
import time
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class PercentileThresholdCalculator:    
    def __init__(self, aggregated_csv='segment_aggregated.csv', 
                 output_file='segment_thresholds.json'):
        self.aggregated_csv = aggregated_csv
        self.output_file = output_file
        self.thresholds = {}
        
    def calculate_thresholds(self, min_samples=20):
        # Load historical data
        df = pd.read_csv(self.aggregated_csv)
        print(f"Loaded {len(df)} aggregated time windows")
        print(f"Date range: {df['time_window'].min()} to {df['time_window'].max()}")
        
        # Convert time_window to datetime
        df['time_window'] = pd.to_datetime(df['time_window'])
        
        segments = df['segment_id'].unique()
        print(f"Unique segments: {len(segments)}")
        
        # Calculate thresholds per segment
        valid_segments = 0
        insufficient_data = []
        
        for seg_id in segments:
            seg_data = df[df['segment_id'] == seg_id]['avg_vehicles']
            
            if len(seg_data) < min_samples:
                insufficient_data.append(seg_id)
                # Use fallback thresholds
                self.thresholds[seg_id] = {
                    'p50': 12.0,  # Fallback
                    'p80': 23.0,  # Fallback
                    'sample_count': len(seg_data),
                    'method': 'fallback'
                }
                continue
            
            # Calculate percentiles
            p50 = float(np.percentile(seg_data, 50))
            p80 = float(np.percentile(seg_data, 80))
            
            # Store thresholds
            self.thresholds[seg_id] = {
                'p50': round(p50, 2),
                'p80': round(p80, 2),
                'min': float(seg_data.min()),
                'max': float(seg_data.max()),
                'mean': float(seg_data.mean()),
                'sample_count': len(seg_data),
                'method': 'percentile'
            }
            valid_segments += 1
        
        # Summary
        print(f"\nThreshold Calculation Results:")
        print(f"  Valid segments (>={min_samples} samples): {valid_segments}")
        print(f"  Insufficient data (using fallback): {len(insufficient_data)}")
        
        if valid_segments > 0:
            all_p50 = [t['p50'] for t in self.thresholds.values() if t['method'] == 'percentile']
            all_p80 = [t['p80'] for t in self.thresholds.values() if t['method'] == 'percentile']
            print(f"\nGlobal Statistics:")
            print(f"  Average P50: {np.mean(all_p50):.2f} vehicles")
            print(f"  Average P80: {np.mean(all_p80):.2f} vehicles")
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.thresholds, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Thresholds saved to: {self.output_file}")
        return self.thresholds
    
    def classify_congestion(self, segment_id: str, vehicle_count: float) -> str:
        """
        Classify congestion level based on thresholds.
        
        Returns: 'green', 'yellow', or 'red'
        """
        if segment_id not in self.thresholds:
            # Use global average if segment not found
            p50 = 15.0
            p80 = 30.0
        else:
            p50 = self.thresholds[segment_id]['p50']
            p80 = self.thresholds[segment_id]['p80']
        
        if vehicle_count <= p50:
            return 'green'
        elif vehicle_count <= p80:
            return 'yellow'
        else:
            return 'red'


class GoongRoadGeometryFetcher:
    """
    Fetch road geometries using Goong Maps Directions API.
    Creates buffered routes around segment centroids.
    """
    
    def __init__(self, segments_csv='segments.csv', 
                 output_geojson='segment_geometries.geojson',
                 goong_api_key='w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY'):
        self.segments_csv = segments_csv
        self.output_geojson = output_geojson
        self.goong_api_key = goong_api_key
        self.directions_url = "https://rsapi.goong.io/Direction"
        
    def create_route_polygon(self, route_coords: List[List[float]], 
                            buffer_degrees: float = 0.0002) -> List[List[List[float]]]:
        """
        Create a buffered polygon around route coordinates.
        
        Args:
            route_coords: List of [lon, lat] pairs
            buffer_degrees: Buffer in degrees (~20-30m at HCMC latitude)
        
        Returns:
            Polygon coordinates for GeoJSON
        """
        if len(route_coords) < 2:
            # Fallback: create small square around single point
            lon, lat = route_coords[0]
            return [[
                [lon - buffer_degrees, lat - buffer_degrees],
                [lon + buffer_degrees, lat - buffer_degrees],
                [lon + buffer_degrees, lat + buffer_degrees],
                [lon - buffer_degrees, lat + buffer_degrees],
                [lon - buffer_degrees, lat - buffer_degrees]
            ]]
        
        # Extract bounding box with buffer
        lons = [c[0] for c in route_coords]
        lats = [c[1] for c in route_coords]
        
        min_lon = min(lons) - buffer_degrees
        max_lon = max(lons) + buffer_degrees
        min_lat = min(lats) - buffer_degrees
        max_lat = max(lats) + buffer_degrees
        
        # Return bounding box polygon
        return [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    
    def fetch_nearby_route(self, lat: float, lon: float, 
                          radius_km: float = 0.5) -> Dict:
        """
        Fetch a small route near the segment centroid to get road geometry.
        Uses a point 500m away in a cardinal direction.
        
        Args:
            lat, lon: Segment centroid
            radius_km: Distance to nearby point
        
        Returns:
            Route data from Goong API
        """
        # Create a nearby destination point (500m east)
        # At HCMC latitude: 1 degree lon ≈ 111km, so 0.5km ≈ 0.0045 degrees
        offset = radius_km / 111.0
        dest_lon = lon + offset
        dest_lat = lat
        
        params = {
            'origin': f"{lat},{lon}",
            'destination': f"{dest_lat},{dest_lon}",
            'vehicle': 'car',
            'api_key': self.goong_api_key
        }
        
        try:
            response = requests.get(
                self.directions_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'routes' in data and len(data['routes']) > 0:
                    route = data['routes'][0]
                    
                    # Extract polyline coordinates
                    if 'overview_polyline' in route and 'points' in route['overview_polyline']:
                        # Decode polyline
                        coords = self.decode_polyline(route['overview_polyline']['points'])
                        return {
                            'success': True,
                            'coordinates': coords,
                            'distance': route.get('legs', [{}])[0].get('distance', {}).get('value', 0),
                            'route_name': route.get('legs', [{}])[0].get('summary', 'Unknown')
                        }
                
                return {'success': False, 'error': 'No routes found'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decode_polyline(self, polyline_str: str) -> List[List[float]]:
        """
        Decode Google-style polyline encoding.
        Returns list of [lon, lat] pairs.
        """
        coords = []
        index = 0
        lat = 0
        lng = 0
        
        while index < len(polyline_str):
            # Decode latitude
            shift = 0
            result = 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat
            
            # Decode longitude
            shift = 0
            result = 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            
            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lng += dlng
            
            coords.append([lng / 1e5, lat / 1e5])  # [lon, lat]
        
        return coords
    
    def fetch_all_geometries(self, rate_limit_delay=0.5):
        """
        Fetch geometries for all segments with GPS coordinates.
        
        Args:
            rate_limit_delay: Seconds between API calls (Goong is faster than OSM)
        """
        print(f"\n{'='*70}")
        print("FETCHING ROAD GEOMETRIES VIA GOONG MAPS API")
        print(f"{'='*70}")
        
        # Load segments
        segments = pd.read_csv(self.segments_csv)
        
        # Parse camera_ids if stored as JSON string
        if 'camera_ids' in segments.columns:
            segments['camera_ids'] = segments['camera_ids'].apply(
                lambda x: json.loads(x) if isinstance(x, str) else x
            )
        
        # Filter segments with GPS
        gps_segments = segments[
            segments['lat'].notna() & 
            segments['lon'].notna()
        ].copy()
        
        print(f"Total segments: {len(segments)}")
        print(f"Segments with GPS: {len(gps_segments)}")
        print(f"Rate limit: {rate_limit_delay}s per request")
        print(f"Estimated time: {len(gps_segments) * rate_limit_delay / 60:.1f} minutes\n")
        
        # Build GeoJSON
        features = []
        success_count = 0
        
        for idx, row in gps_segments.iterrows():
            seg_id = row['segment_id']
            lat = row['lat']
            lon = row['lon']
            
            print(f"[{idx+1}/{len(gps_segments)}] Fetching {seg_id}...", end=' ')
            
            # Fetch route near this point
            route_data = self.fetch_nearby_route(lat, lon, radius_km=0.5)
            
            if route_data['success']:
                coords = route_data['coordinates']
                
                # Create polygon
                polygon_coords = self.create_route_polygon(coords, buffer_degrees=0.0002)
                
                feature = {
                    'type': 'Feature',
                    'properties': {
                        'segment_id': seg_id,
                        'segment_name': row['segment_name'],
                        'lat': lat,
                        'lon': lon,
                        'route_name': route_data.get('route_name', 'Unknown'),
                        'route_distance': route_data.get('distance', 0),
                        'congestion_level': 'green',  # Default
                        'data_source': 'goong_api'
                    },
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': polygon_coords
                    }
                }
                features.append(feature)
                success_count += 1
                print(f"✓ ({len(coords)} points)")
            else:
                # Fallback: create circle around centroid
                print(f"⚠️  ({route_data.get('error', 'unknown error')})")
                
                # Create small polygon around point
                buffer = 0.0015  # ~150m
                feature = {
                    'type': 'Feature',
                    'properties': {
                        'segment_id': seg_id,
                        'segment_name': row['segment_name'],
                        'lat': lat,
                        'lon': lon,
                        'fallback': True,
                        'congestion_level': 'green',
                        'data_source': 'centroid_fallback'
                    },
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [lon - buffer, lat - buffer],
                            [lon + buffer, lat - buffer],
                            [lon + buffer, lat + buffer],
                            [lon - buffer, lat + buffer],
                            [lon - buffer, lat - buffer]
                        ]]
                    }
                }
                features.append(feature)
            
            # Rate limiting
            time.sleep(rate_limit_delay)
        
        # Create GeoJSON
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        # Save
        with open(self.output_geojson, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*70}")
        print(f"✓ GEOMETRIES SAVED")
        print(f"{'='*70}")
        print(f"Success: {success_count}/{len(gps_segments)}")
        print(f"Fallback polygons: {len(gps_segments) - success_count}")
        print(f"Output: {self.output_geojson}")
        print(f"File size: {Path(self.output_geojson).stat().st_size / 1024:.1f} KB")
        
        return geojson


class CongestionClassifier:
    """
    Main classifier that combines percentile thresholds with real-time data.
    """
    
    def __init__(self, thresholds_file='segment_thresholds.json',
                 aggregated_csv='segment_aggregated.csv',
                 geometries_file='segment_geometries.geojson'):
        self.thresholds_file = thresholds_file
        self.aggregated_csv = aggregated_csv
        self.geometries_file = geometries_file
        
        # Load thresholds
        if Path(thresholds_file).exists():
            with open(thresholds_file, 'r', encoding='utf-8') as f:
                self.thresholds = json.load(f)
        else:
            print(f"⚠️  Thresholds file not found: {thresholds_file}")
            self.thresholds = {}
    
    def classify_latest_data(self, output_csv='segment_congestion_classified.csv'):
        """
        Apply classification to aggregated data and save.
        """
        print(f"\n{'='*70}")
        print("APPLYING CONGESTION CLASSIFICATION")
        print(f"{'='*70}")
        
        # Load data
        df = pd.read_csv(self.aggregated_csv)
        print(f"Loaded {len(df)} time windows")
        
        # Apply classification
        df['congestion_level'] = df.apply(
            lambda row: self._classify_row(row['segment_id'], row['avg_vehicles']),
            axis=1
        )
        
        # Add color codes for frontend
        color_map = {'green': '#00C851', 'yellow': '#ffbb33', 'red': '#ff4444'}
        df['congestion_color'] = df['congestion_level'].map(color_map)
        
        # Summary
        counts = df['congestion_level'].value_counts()
        print(f"\nCongestion Distribution:")
        for level in ['green', 'yellow', 'red']:
            count = counts.get(level, 0)
            pct = (count / len(df) * 100) if len(df) > 0 else 0
            print(f"  {level.upper()}: {count:,} ({pct:.1f}%)")
        
        # Save
        df.to_csv(output_csv, index=False)
        print(f"\n✓ Classified data saved to: {output_csv}")
        
        return df
    
    def _classify_row(self, segment_id: str, vehicle_count: float) -> str:
        """Helper to classify a single row."""
        if pd.isna(vehicle_count):
            return 'green'
        
        if segment_id not in self.thresholds:
            # Global fallback
            if vehicle_count <= 15:
                return 'green'
            elif vehicle_count <= 30:
                return 'yellow'
            else:
                return 'red'
        
        thresh = self.thresholds[segment_id]
        if vehicle_count <= thresh['p50']:
            return 'green'
        elif vehicle_count <= thresh['p80']:
            return 'yellow'
        else:
            return 'red'
    
    def update_geojson_with_congestion(self, classified_csv='segment_congestion_classified.csv',
                                       output_geojson='segment_geometries_with_congestion.geojson'):
        """
        Update GeoJSON properties with latest congestion levels.
        """
        print(f"\n{'='*70}")
        print("UPDATING GEOJSON WITH CONGESTION DATA")
        print(f"{'='*70}")
        
        # Load classified data (get latest per segment)
        df = pd.read_csv(classified_csv)
        df['time_window'] = pd.to_datetime(df['time_window'])
        
        # Get latest record per segment
        latest = df.sort_values('time_window').groupby('segment_id').last().reset_index()
        
        # Load GeoJSON
        with open(self.geometries_file, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
        
        # Update properties
        updated_count = 0
        for feature in geojson['features']:
            seg_id = feature['properties']['segment_id']
            
            seg_data = latest[latest['segment_id'] == seg_id]
            if not seg_data.empty:
                row = seg_data.iloc[0]
                feature['properties'].update({
                    'congestion_level': row['congestion_level'],
                    'congestion_color': row['congestion_color'],
                    'avg_vehicles': float(row['avg_vehicles']),
                    'avg_cars': float(row['avg_cars']),
                    'avg_motorcycles': float(row['avg_motorcycles']),
                    'avg_buses': float(row['avg_buses']),
                    'avg_trucks': float(row['avg_trucks']),
                    'last_update': str(row['time_window'])
                })
                updated_count += 1
        
        # Save
        with open(output_geojson, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Updated {updated_count} segments")
        print(f"✓ Output: {output_geojson}")
        
        return geojson


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("╔" + "="*68 + "╗")
    print("║" + " PERCENTILE-BASED CONGESTION CLASSIFIER (GOONG MAPS) ".center(68) + "║")
    print("╚" + "="*68 + "╝")
    
    # Step 1: Calculate percentile thresholds
    # print("\n[STEP 1/4] Loading Static Thresholds...")
    # print("Using static thresholds from segment_thresholds.json")
    
    # # Load thresholds to display summary
    # with open('segment_thresholds.json', 'r', encoding='utf-8') as f:
    #     thresholds = json.load(f)
    
    # percentile_segments = sum(1 for t in thresholds.values() if t.get('method') == 'percentile')
    # fallback_segments = sum(1 for t in thresholds.values() if t.get('method') == 'fallback')

    print("\n[STEP 1/4] Calculating Percentile Thresholds...")
    threshold_calc = PercentileThresholdCalculator(
        aggregated_csv='segment_aggregated.csv',
        output_file='segment_thresholds.json'
    )
    thresholds = threshold_calc.calculate_thresholds(min_samples=20)


    # Step 2: Fetch road geometries via Goong API
    print("\n[STEP 2/4] Fetching Road Geometries via Goong Maps...")
    print("⏱️  This will take 3-8 minutes depending on segment count...")
    goong_fetcher = GoongRoadGeometryFetcher(
        segments_csv='segments.csv',
        output_geojson='segment_geometries.geojson',
        goong_api_key='w6UXzsXLNcwmP5pRQdbHALGm2jK3nxj8OhNrJlQY'
    )
    geometries = goong_fetcher.fetch_all_geometries(rate_limit_delay=0.5)
    
    # Step 3: Classify current data
    print("\n[STEP 3/4] Classifying Current Data...")
    classifier = CongestionClassifier(
        thresholds_file='segment_thresholds.json',
        aggregated_csv='segment_aggregated.csv',
        geometries_file='segment_geometries.geojson'
    )
    classified_df = classifier.classify_latest_data(
        output_csv='segment_congestion_classified.csv'
    )
    
    # Step 4: Update GeoJSON with congestion
    print("\n[STEP 4/4] Updating GeoJSON with Congestion Levels...")
    final_geojson = classifier.update_geojson_with_congestion(
        classified_csv='segment_congestion_classified.csv',
        output_geojson='segment_geometries_with_congestion.geojson'
    )
    
    print("\n" + "="*70)
    print("✓ COMPLETE! Ready for API and Frontend Integration")
    print("="*70)
    print("\nGenerated Files:")
    print("  1. segment_thresholds.json                    - Percentile thresholds")
    print("  2. segment_geometries.geojson                 - Road shapes from Goong")
    print("  3. segment_congestion_classified.csv          - Classified traffic data")
    print("  4. segment_geometries_with_congestion.geojson - Map-ready GeoJSON")
    print("\nNext: Mini-Step 1.2 - Flask API with Goong Maps frontend")