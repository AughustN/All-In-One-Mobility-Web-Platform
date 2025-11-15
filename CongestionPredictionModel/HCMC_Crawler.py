# multi_camera_loop.py
# Run: python multi_camera_loop.py --cameras-file ./cameras.json --interval 120 --max-workers 16 --output-dir ./camera_frames
import argparse
import concurrent.futures
import json
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import hashlib

def utc_now():
    return datetime.now(timezone.utc)

# ---------- Lightweight adapted HCMCCameraCrawler (persistent session) ----------
class HCMCCameraCrawler:
    def __init__(self, camera_id, camera_name, output_dir="./camera_frames", headers=None, timeout=60):
        self.camera_id = camera_id
        self.camera_name = camera_name or camera_id
        self.base_url = "https://giaothong.hochiminhcity.gov.vn/render/ImageHandler.ashx"
        self.output_dir = Path(output_dir) / camera_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # persistent session per crawler (keeps HTTP keep-alive)
        self.session = requests.Session()
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Referer': 'https://giaothong.hochiminhcity.gov.vn/',
            'Connection': 'keep-alive',
        }

        self.timeout = timeout

        # Deduplication
        self.previous_hash = None
        self.consecutive_duplicates = 0

        # Stats
        self.stats = {
        'total_attempts': 0,
        'successful_fetches': 0,
        'failed_fetches': 0,
        'duplicates_skipped': 0,
        'images_saved': 0,
        'start_time': utc_now()  # was: datetime.now()
    }


    def fetch_image(self):
        timestamp_ms = int(time.time() * 1000)
        url = f"{self.base_url}?id={self.camera_id}&t={timestamp_ms}"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type and len(response.content) < 1000:
                    # not an image or tiny response
                    return None
                return response.content
            else:
                return None
        except requests.Timeout:
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def compute_hash(image_data):
        h = hashlib.sha256()
        h.update(image_data)
        return h.hexdigest()

    def is_duplicate(self, image_hash):
        if image_hash == self.previous_hash:
            self.consecutive_duplicates += 1
            return True
        else:
            self.consecutive_duplicates = 0
            return False

    def save_image(self, image_data):
        image_hash = self.compute_hash(image_data)
        if self.is_duplicate(image_hash):
            self.stats['duplicates_skipped'] += 1
            return None

        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")  # was: datetime.utcnow()
        filename = f"{self.camera_id}_{timestamp}_{image_hash[:8]}.jpg"
        image_path = self.output_dir / filename
        with open(image_path, 'wb') as f:
            f.write(image_data)

        meta = {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "timestamp": timestamp,
            "timestamp_iso": utc_now().isoformat().replace("+00:00", "Z"),  # was: datetime.utcnow().isoformat()+"Z"
            "hash": image_hash,
            "file_size": len(image_data),
            "filename": filename,
            "segment_id": None,
            "gps_lat": None,
            "gps_lon": None,
            "bearing": None,
            "lane_schema": None
        }
        with open(image_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        self.previous_hash = image_hash
        self.stats['images_saved'] += 1
        return image_path

    def crawl_once(self):
        self.stats['total_attempts'] += 1
        data = self.fetch_image()
        if not data:
            self.stats['failed_fetches'] += 1
            return False
        self.stats['successful_fetches'] += 1
        saved = self.save_image(data)
        return saved is not None

    def print_stats(self):
        rt = utc_now() - self.stats['start_time']  
        print(f"  {self.camera_id} | attempts={self.stats['total_attempts']:4} ok={self.stats['successful_fetches']:3} "
            f"fail={self.stats['failed_fetches']:3} saved={self.stats['images_saved']:3} dups={self.stats['duplicates_skipped']:3} "
            f"uptime={rt}")

# ---------- Manager for multi-camera loop ----------
class MultiCameraLoop:
    def __init__(self, camera_entries, interval_seconds=120, max_workers=16, output_dir="./camera_frames"):
        # camera_entries: list of dicts with at least 'id' and optionally 'name'
        self.interval = max(5, int(interval_seconds))
        self.max_workers = max(1, int(max_workers))
        self.output_dir = Path(output_dir)
        self.crawlers = []
        for e in camera_entries:
            cid = e.get('id') or e.get('Id') or e.get('ID') or e.get('code')
            name = e.get('name') or e.get('code') or e.get('location') or ''
            if not cid:
                continue
            self.crawlers.append(HCMCCameraCrawler(str(cid), str(name), output_dir=self.output_dir))

        self._stop = threading.Event()

    def signal_handler(self, signum, frame):
        print("\n🛑 Stop signal received; finishing current cycle then exiting...")
        self._stop.set()

    def run(self):
        # register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        try:
            signal.signal(signal.SIGTERM, self.signal_handler)
        except Exception:
            pass  # windows may raise

        total_cams = len(self.crawlers)
        print(f"Starting loop: {total_cams} cameras, interval={self.interval}s, workers={self.max_workers}")
        cycle = 0
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                while not self._stop.is_set():
                    cycle += 1
                    start = time.time()
                    print("\n" + "=" * 70)
                    print(f"[Cycle {cycle}] start {utc_now().isoformat().replace('+00:00','Z')}")
                    print("=" * 70)

                    # submit crawl tasks
                    futures = []
                    for c in self.crawlers:
                        futures.append(ex.submit(c.crawl_once))

                    # wait for all (with a large timeout to avoid hanging forever)
                    concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)

                    # aggregate stats
                    total_attempts = total_ok = total_fail = total_saved = total_dups = 0
                    for c in self.crawlers:
                        s = c.stats
                        total_attempts += s['total_attempts']
                        total_ok += s['successful_fetches']
                        total_fail += s['failed_fetches']
                        total_saved += s['images_saved']
                        total_dups += s['duplicates_skipped']

                    elapsed = time.time() - start
                    print(f"\nCycle done in {elapsed:.1f}s. cameras={total_cams} attempts={total_attempts} "
                        f"ok={total_ok} fail={total_fail} saved={total_saved} dups={total_dups}")
                    print("Per-camera summary (sample first 10):")
                    for c in self.crawlers[:10]:
                        c.print_stats()

                    # sleep until next cycle, but allow quick shutdown (1s slices)
                    wait_for = max(0, self.interval - elapsed)
                    for _ in range(int(wait_for)):
                        if self._stop.is_set():
                            break
                        time.sleep(1)
                    # small remainder
                    if not self._stop.is_set():
                        rem = wait_for - int(wait_for)
                        if rem > 0:
                            time.sleep(rem)
        finally:
            print("\nFinal stats:")
            for c in self.crawlers[:50]:  # print first 50 for brevity
                c.print_stats()
            print("Exiting.")

# ---------- CLI bootstrap ----------
def load_cameras(file_path):
    p = Path(file_path)
    data = json.loads(p.read_text(encoding='utf-8'))
    # Expect list-of-objects; tolerant to wrapper { value: [...] }
    if isinstance(data, dict) and 'value' in data and isinstance(data['value'], list):
        return data['value']
    if isinstance(data, list):
        return data
    # fallback: try common fields
    return []

def parse_args():
    import argparse, os

    p = argparse.ArgumentParser(
        description="Fetch frames from multiple HCMC traffic cameras on a loop."
    )
    p.add_argument(
        "--cameras-file",
        required=True,
        help="Path to JSON file with camera array (each object has 'id' and optional 'name').",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Seconds between cycles (min 5s; values below are clamped).",
    )
    p.add_argument(
        "--max-workers",
        type=int,
        default=16,
        help="Max concurrent workers (threads) for fetching.",
    )
    p.add_argument(
        "--output-dir",
        default="./camera_frames",
        help="Root output directory for saved images and metadata.",
    )
    args = p.parse_args()

    if not os.path.exists(args.cameras_file):
        p.error(f"--cameras-file not found: {args.cameras_file}")
    if args.interval <= 0:
        p.error("--interval must be > 0")
    if args.max_workers <= 0:
        p.error("--max-workers must be > 0")

    return args

def main():
    args = parse_args()
    cams = load_cameras(args.cameras_file)
    if not cams:
        print("No cameras found in file:", args.cameras_file)
        sys.exit(1)

    mgr = MultiCameraLoop(
        cams,
        interval_seconds=args.interval,
        max_workers=args.max_workers,
        output_dir=args.output_dir,
    )
    mgr.run()

if __name__ == "__main__":
    main()
