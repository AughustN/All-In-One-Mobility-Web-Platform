import requests
import json
import time
from pathlib import Path
from collections import OrderedDict

class CameraLocationBuilder:    
    def __init__(self, tomtom_api_key):
        self.api_key = tomtom_api_key
        self.base_url = "https://api.tomtom.com/search/2/search"
        
    def extract_unique_cameras(self, data_dir, max_scan=2000):
        data_dir = Path(data_dir)
        cameras = OrderedDict()
        
        json_files = list(data_dir.rglob("*.json"))
        print(f"Found {len(json_files)} metadata files")
        print(f"Scanning first {min(max_scan, len(json_files))} to extract cameras...")
        
        for json_file in json_files[:max_scan]:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cam_id = data.get('camera_id')
                    cam_name = data.get('camera_name')
                    
                    if cam_id and cam_name and cam_id not in cameras:
                        cameras[cam_id] = cam_name
                        
                        if len(cameras) % 50 == 0:
                            print(f"  Found {len(cameras)} unique cameras so far...")
            except Exception as e:
                continue
        
        print(f"\nExtracted {len(cameras)} unique cameras")
        return cameras
    
    def geocode_camera(self, camera_name):
        clean_name = camera_name.split('(')[0].strip()
        
        # Build query
        query = f"{clean_name}, Ho Chi Minh City, Vietnam"
        url = f"{self.base_url}/{query}.json"
        
        params = {
            'key': self.api_key,
            'limit': 1,
            'countrySet': 'VN',
            'language': 'vi-VN'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    position = result.get('position', {})
                    
                    return {
                        'lat': position.get('lat'),
                        'lon': position.get('lon'),
                        'display_name': result.get('address', {}).get('freeformAddress', ''),
                        'source': 'tomtom'
                    }
            
            # API error
            if response.status_code == 429:
                print(f"Rate limited, waiting...")
                time.sleep(60)
                return self.geocode_camera(camera_name)  # Retry
            
            return None
            
        except requests.Timeout:
            print(f"Timeout")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def batch_geocode(self, cameras_dict, output_file="camera_locations.json", 
                     checkpoint_interval=50):
        total = len(cameras_dict)
        results = {}
        
        # Load existing results if resuming
        output_path = Path(output_file)
        if output_path.exists():
            print(f"Found existing results file, loading...")
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            print(f"  Loaded {len(results)} previous results")
        
        print(f"\n{'='*70}")
        print(f"Starting TomTom Geocoding: {total} cameras")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        success_count = 0
        
        for i, (cam_id, cam_name) in enumerate(cameras_dict.items(), 1):
            if cam_id in results and results[cam_id].get('lat') is not None:
                success_count += 1
                continue
            
            # Progress
            print(f"[{i}/{total}] {cam_name[:55]:<55}", end=' ')
            
            # Geocode
            location = self.geocode_camera(cam_name)
            
            if location and location.get('lat'):
                results[cam_id] = {
                    'camera_name': cam_name,
                    **location
                }
                success_count += 1
                print(f"✓ ({location['lat']:.6f}, {location['lon']:.6f}) [{location['confidence']}]")
            else:
                results[cam_id] = {
                    'camera_name': cam_name,
                    'lat': None,
                    'lon': None,
                    'source': 'failed',
                    'error': 'geocoding_failed'
                }
                print(f"✗ Failed")
            
            # Checkpoint save
            if i % checkpoint_interval == 0:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (total - i) / rate if rate > 0 else 0
                
                print(f"\n  → Checkpoint: {i}/{total} ({i/total*100:.1f}%) | "
                      f"Success: {success_count} | "
                      f"ETA: {remaining/60:.1f} min\n")
            
            # Rate limiting (TomTom free tier: 2500 requests/day)
            # Safe rate: ~1 request per 2 seconds
            time.sleep(2)
        
        # Final save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Summary
        elapsed = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"Geocoding Complete!")
        print(f"{'='*70}")
        print(f"Total cameras:        {total}")
        print(f"Successfully geocoded: {success_count} ({success_count/total*100:.1f}%)")
        print(f"Failed:               {total - success_count}")
        print(f"Time elapsed:         {elapsed/60:.1f} minutes")
        print(f"Results saved to:     {output_file}")
        print(f"{'='*70}\n")
        
        return results
    
    def validate_results(self, results_file="camera_locations.json"):
        """
        Check geocoding results quality
        """
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"\n{'='*70}")
        print(f"VALIDATION REPORT")
        print(f"{'='*70}")
        
        total = len(results)
        has_coords = sum(1 for r in results.values() if r.get('lat') is not None)
        high_conf = sum(1 for r in results.values() if r.get('confidence') == 'high')
        med_conf = sum(1 for r in results.values() if r.get('confidence') == 'medium')
        low_conf = sum(1 for r in results.values() if r.get('confidence') == 'low')
        
        print(f"Total cameras:     {total}")
        print(f"Has coordinates:   {has_coords} ({has_coords/total*100:.1f}%)")
        print(f"  High confidence: {high_conf}")
        print(f"  Med confidence:  {med_conf}")
        print(f"  Low confidence:  {low_conf}")
        print(f"Missing coords:    {total - has_coords}")
        
        # Show examples
        print(f"\n--- SAMPLE RESULTS ---")
        for i, (cam_id, data) in enumerate(list(results.items())[:5]):
            if data.get('lat'):
                print(f"{i+1}. {data['camera_name'][:50]}")
                print(f"   → ({data['lat']:.6f}, {data['lon']:.6f}) [{data.get('confidence', 'N/A')}]")
        
        # Check coordinate bounds (HCMC approximate bounds)
        hcmc_bounds = {
            'lat_min': 10.3, 'lat_max': 11.2,
            'lon_min': 106.3, 'lon_max': 107.0
        }
        
        out_of_bounds = 0
        for data in results.values():
            if data.get('lat'):
                if not (hcmc_bounds['lat_min'] <= data['lat'] <= hcmc_bounds['lat_max'] and
                       hcmc_bounds['lon_min'] <= data['lon'] <= hcmc_bounds['lon_max']):
                    out_of_bounds += 1
        
        if out_of_bounds > 0:
            print(f"\n⚠️  WARNING: {out_of_bounds} cameras outside HCMC bounds (may be errors)")
        else:
            print(f"\n✓ All coordinates within HCMC bounds")


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    # STEP 1: Configure
    TOMTOM_API_KEY = "dcS4AgK0puDJlKhUT8zOfIUA5VK0pKsi"
    DATA_DIR = "./camera_frames"
    OUTPUT_FILE = "camera_locations.json"
    
    # STEP 2: Initialize
    builder = CameraLocationBuilder(TOMTOM_API_KEY)
    
    # STEP 3: Extract unique cameras
    cameras = builder.extract_unique_cameras(DATA_DIR, max_scan=2000)
    
    # STEP 4: Batch geocode (THIS WILL TAKE 1-2 HOURS)
    print(f"\n⏰ This will take approximately {len(cameras) * 2 / 60:.1f} minutes")
    print(f"   (2 seconds per camera × {len(cameras)} cameras)")
    
    input("\nPress ENTER to start geocoding (or Ctrl+C to cancel)...")
    
    results = builder.batch_geocode(
        cameras, 
        output_file=OUTPUT_FILE,
        checkpoint_interval=50
    )
    
    # STEP 5: Validate
    builder.validate_results(OUTPUT_FILE)
    
    print("\n✓ Camera location database ready!")
    print(f"   Use '{OUTPUT_FILE}' in your detection pipeline")