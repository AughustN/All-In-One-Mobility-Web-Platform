    import requests
    import hashlib
    import time
    from datetime import datetime
    from pathlib import Path
    import json
    import signal
    import sys

    class HCMCCameraCrawler:
        def __init__(self, camera_id, camera_name, output_dir="./camera_frames"):
            self.camera_id = camera_id
            self.camera_name = camera_name
            self.base_url = "https://giaothong.hochiminhcity.gov.vn/render/ImageHandler.ashx"
            self.output_dir = Path(output_dir) / camera_id
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Browser headers
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Referer': 'https://giaothong.hochiminhcity.gov.vn/',
                'Connection': 'keep-alive',
            }
            
            # Deduplication
            self.previous_hash = None
            self.consecutive_duplicates = 0
            
            # Statistics
            self.stats = {
                'total_attempts': 0,
                'successful_fetches': 0,
                'failed_fetches': 0,
                'duplicates_skipped': 0,
                'images_saved': 0,
                'start_time': datetime.now()
            }
            
            print(f"✓ Initialized crawler for: {camera_name}")
            print(f"  Camera ID: {camera_id}")
            print(f"  Output: {self.output_dir}")
        
        def fetch_image(self, timeout=60):
            """Fetch current image from camera endpoint"""
            timestamp_ms = int(time.time() * 1000)
            url = f"{self.base_url}?id={self.camera_id}&t={timestamp_ms}"
            
            try:
                session = requests.Session()
                response = session.get(
                    url, 
                    headers=self.headers,
                    timeout=timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'image' not in content_type and len(response.content) < 1000:
                        print(f"  ✗ Invalid response (not an image)")
                        return None
                    
                    return response.content
                else:
                    print(f"  ✗ HTTP {response.status_code}")
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"  ✗ Timeout (>{timeout}s)")
                return None
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request error: {e}")
                return None
        
        def compute_hash(self, image_data):
            """Compute SHA256 hash for deduplication"""
            hasher = hashlib.sha256()
            hasher.update(image_data)
            return hasher.hexdigest()
        
        def is_duplicate(self, image_hash):
            """Check if image is duplicate of previous frame"""
            if image_hash == self.previous_hash:
                self.consecutive_duplicates += 1
                return True
            else:
                self.consecutive_duplicates = 0
                return False
        
        def save_image(self, image_data):
            """Save image with metadata"""
            image_hash = self.compute_hash(image_data)
            
            # Deduplication check
            if self.is_duplicate(image_hash):
                self.stats['duplicates_skipped'] += 1
                print(f"  ⊗ Duplicate #{self.consecutive_duplicates} (skipped)")
                return None
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.camera_id}_{timestamp}_{image_hash[:8]}.jpg"
            image_path = self.output_dir / filename
            
            # Save image
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Save metadata
            meta = {
                "camera_id": self.camera_id,
                "camera_name": self.camera_name,
                "timestamp": timestamp,
                "timestamp_iso": datetime.now().isoformat(),
                "hash": image_hash,
                "file_size": len(image_data),
                "filename": filename,
                # TODO: Add from camera database
                "segment_id": None,
                "gps_lat": None,
                "gps_lon": None,
                "bearing": None,
                "lane_schema": None
            }
            
            meta_path = image_path.with_suffix('.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            self.previous_hash = image_hash
            self.stats['images_saved'] += 1
            
            print(f"  ✓ Saved: {filename} ({len(image_data):,} bytes)")
            return image_path
        
        def crawl_once(self):
            """Perform one crawl cycle"""
            self.stats['total_attempts'] += 1
            
            # Fetch image
            image_data = self.fetch_image()
            
            if not image_data:
                self.stats['failed_fetches'] += 1
                return False
            
            self.stats['successful_fetches'] += 1
            
            # Save with deduplication
            saved_path = self.save_image(image_data)
            return saved_path is not None
        
        def print_stats(self):
            """Print current statistics"""
            runtime = datetime.now() - self.stats['start_time']
            hours, remainder = divmod(runtime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            print(f"\n{'='*60}")
            print(f"Statistics - Runtime: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            print(f"{'='*60}")
            print(f"  Total attempts:      {self.stats['total_attempts']}")
            print(f"  Successful fetches:  {self.stats['successful_fetches']}")
            print(f"  Failed fetches:      {self.stats['failed_fetches']}")
            print(f"  Images saved:        {self.stats['images_saved']}")
            print(f"  Duplicates skipped:  {self.stats['duplicates_skipped']}")
            
            if self.stats['total_attempts'] > 0:
                success_rate = (self.stats['successful_fetches'] / self.stats['total_attempts']) * 100
                print(f"  Success rate:        {success_rate:.1f}%")
            
            print(f"{'='*60}\n")


    class ContinuousCrawler:
        """Manages continuous polling with graceful shutdown"""
        
        def __init__(self, crawler, interval_seconds=120):
            self.crawler = crawler
            self.interval = interval_seconds
            self.running = False
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
        
        def signal_handler(self, signum, frame):
            """Handle Ctrl+C gracefully"""
            print("\n\n🛑 Shutdown signal received...")
            self.running = False
        
        def run(self):
            """Run continuous polling loop"""
            self.running = True
            
            print(f"\n{'='*60}")
            print(f"Starting continuous polling")
            print(f"{'='*60}")
            print(f"  Camera: {self.crawler.camera_name}")
            print(f"  Interval: {self.interval} seconds")
            print(f"  Press Ctrl+C to stop")
            print(f"{'='*60}\n")
            
            cycle_count = 0
            
            try:
                while self.running:
                    cycle_count += 1
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"[Cycle #{cycle_count}] {current_time}")
                    
                    # Crawl once
                    success = self.crawler.crawl_once()
                    
                    if not self.running:
                        break
                    
                    # Wait for next cycle
                    print(f"  ⏳ Waiting {self.interval}s until next fetch...")
                    
                    # Sleep in 1-second intervals to allow quick shutdown
                    for i in range(self.interval):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                    print()  # Blank line between cycles
                    
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
            
            finally:
                # Print final statistics
                print("\n🛑 Stopping crawler...")
                self.crawler.print_stats()
                print("✓ Crawler stopped gracefully\n")


    # ============================================
    # MAIN: Continuous polling
    # ============================================

    if __name__ == "__main__":
        # Configuration
        CAMERA_ID = "5deb576d1dc17d7c5515ad03"
        CAMERA_NAME = "Nam Kỳ Khởi Nghĩa - Nguyễn Đình Chiểu"
        INTERVAL_SECONDS = 120  # As per your spec
        
        print("="*60)
        print("HCMC Traffic Camera - Continuous Crawler")
        print("="*60)
        
        # Initialize camera crawler
        camera_crawler = HCMCCameraCrawler(CAMERA_ID, CAMERA_NAME)
        
        # Initialize continuous polling manager
        continuous = ContinuousCrawler(camera_crawler, interval_seconds=INTERVAL_SECONDS)
        
        # Start continuous polling
        continuous.run()