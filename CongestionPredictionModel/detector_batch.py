import cv2
import os
from ultralytics import YOLO
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import time
from tqdm import tqdm
import pandas as pd
import numpy as np
class OptimizedBatchDetector:
    
    def __init__(self, model_name='yolov11l.pt', db_path='detections.db', 
                 use_preprocessing=True, use_tta=False):
        print(f"Initializing Optimized Batch Detector...")
        self.model = YOLO(model_name)
        self.model.to("cuda")
        self.db_path = db_path
        self.use_preprocessing = use_preprocessing
        self.use_tta = use_tta
        
        # Vehicle classes
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }
        
        # Class-specific thresholds (from optimization)
        self.class_thresholds = {
            2: 0.25,  # car
            3: 0.15,  # motorcycle - lower threshold helps!
            5: 0.38,  # bus
            7: 0.30   # truck
        }
        
        # CLAHE for preprocessing
        if use_preprocessing:
            self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        
        # Initialize database
        self._init_database()
        
        print(f"✓ Model loaded: {model_name}")
        print(f"✓ Preprocessing: {use_preprocessing}")
        print(f"✓ TTA: {use_tta}")
        print(f"✓ Database: {db_path}")
    
    def _init_database(self):
        """Create optimized database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL UNIQUE,
                camera_id TEXT NOT NULL,
                camera_name TEXT,
                timestamp TEXT NOT NULL,
                timestamp_dt DATETIME,
                total_vehicles INTEGER DEFAULT 0,
                car_count INTEGER DEFAULT 0,
                motorcycle_count INTEGER DEFAULT 0,
                bus_count INTEGER DEFAULT 0,
                truck_count INTEGER DEFAULT 0,
                processing_time REAL,
                optimization_used TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_camera_timestamp ON detections(camera_id, timestamp_dt)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_camera_id ON detections(camera_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp_dt ON detections(timestamp_dt)')
        
        conn.commit()
        conn.close()
    
    def preprocess_image(self, img):
        """Apply CLAHE + denoising"""
        if not self.use_preprocessing:
            return img
        
        # LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE on L channel
        l = self.clahe.apply(l)
        
        # Merge back
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Mild denoising
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 7, 7, 7, 21)
        
        return enhanced
    
    def load_metadata(self, image_path):
        """Load companion JSON metadata"""
        json_path = image_path.with_suffix('.json')
        
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def parse_timestamp(self, timestamp_str):
        """Parse timestamp to datetime"""
        try:
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except:
            return None
    
    def detect_image(self, image_path):
        """
        Detect vehicles with optimization
        """
        start_time = time.time()
        
        # Load metadata
        metadata = self.load_metadata(image_path)
        
        if metadata:
            camera_id = metadata.get('camera_id', 'unknown')
            camera_name = metadata.get('camera_name')
            timestamp_str = metadata.get('timestamp') or metadata.get('timestamp_iso')
        else:
            camera_id = image_path.parent.name
            camera_name = None
            timestamp_str = image_path.stem.split('_')[1] + '_' + image_path.stem.split('_')[2]
        
        timestamp_dt = self.parse_timestamp(timestamp_str)
        
        # Load and preprocess image
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        
        if self.use_preprocessing:
            img = self.preprocess_image(img)
        
        # Run detection
        results = self.model.predict(
            img,
            conf=0.20,
            iou=0.5,
            imgsz=960,
            classes=list(self.vehicle_classes.keys()),
            augment=self.use_tta,
            verbose=False,
            half=False  # CPU doesn't support FP16
        )
        
        # Parse and filter by class thresholds
        vehicle_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            
            for box in boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                # Apply class-specific threshold
                threshold = self.class_thresholds.get(cls, 0.20)
                
                if conf >= threshold:
                    vehicle_type = self.vehicle_classes[cls]
                    vehicle_counts[vehicle_type] += 1
        
        processing_time = time.time() - start_time
        
        opt_config = f"preprocess={self.use_preprocessing},tta={self.use_tta}"
        
        return {
            'image_path': str(image_path),
            'camera_id': camera_id,
            'camera_name': camera_name,
            'timestamp': timestamp_str,
            'timestamp_dt': timestamp_dt,
            'total_vehicles': sum(vehicle_counts.values()),
            'car_count': vehicle_counts['car'],
            'motorcycle_count': vehicle_counts['motorcycle'],
            'bus_count': vehicle_counts['bus'],
            'truck_count': vehicle_counts['truck'],
            'processing_time': processing_time,
            'optimization_used': opt_config
        }
    
    def save_detection(self, detection_data):
        """Save to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO detections 
                (image_path, camera_id, camera_name, timestamp, timestamp_dt,
                 total_vehicles, car_count, motorcycle_count, bus_count, truck_count,
                 processing_time, optimization_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                detection_data['image_path'],
                detection_data['camera_id'],
                detection_data['camera_name'],
                detection_data['timestamp'],
                detection_data['timestamp_dt'],
                detection_data['total_vehicles'],
                detection_data['car_count'],
                detection_data['motorcycle_count'],
                detection_data['bus_count'],
                detection_data['truck_count'],
                detection_data['processing_time'],
                detection_data['optimization_used']
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error saving: {e}")
        finally:
            conn.close()
    
    def batch_process(self, data_dir, resume=True):
        """Process all images"""
        data_dir = Path(data_dir)
        image_files = list(data_dir.rglob("*.jpg"))
        
        print(f"\n{'='*70}")
        print(f"Starting Batch Processing")
        print(f"{'='*70}")
        print(f"Total images: {len(image_files)}")
        print(f"Optimization: preprocess={self.use_preprocessing}, tta={self.use_tta}")
        
        # Check already processed
        processed = set()
        if resume:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT image_path FROM detections")
            processed = set(row[0] for row in cursor.fetchall())
            conn.close()
            print(f"Already processed: {len(processed)}")
        
        remaining = [img for img in image_files if str(img) not in processed]
        print(f"To process: {len(remaining)}")
        
        if len(remaining) == 0:
            print("✓ All done!")
            return
        
        # Estimate
        estimated_hours = (len(remaining) * 0.73) / 3600  # Based on benchmark
        print(f"Estimated time: {estimated_hours:.1f} hours\n")
        
        # Process
        start_time = time.time()
        success = 0
        
        for img_path in tqdm(remaining, desc="Processing"):
            try:
                result = self.detect_image(img_path)
                if result:
                    self.save_detection(result)
                    success += 1
            except Exception as e:
                if success % 500 == 0:
                    print(f"\nWarning: {e}")
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"Batch Complete!")
        print(f"{'='*70}")
        print(f"Processed: {success}")
        print(f"Time: {elapsed/3600:.2f} hours")
        print(f"Speed: {success/elapsed:.2f} img/s")
        print(f"Database: {self.db_path}")



# Cleanup function
def cleanup_frames(base_dir="./camera_frames"):
    for cam in os.listdir(base_dir):
        path = os.path.join(base_dir, cam)
        if os.path.isdir(path):
            for f in os.listdir(path):
                try:
                    os.remove(os.path.join(path, f))
                except:
                    pass
    print("🧹 Deleted frames after detection.")

# MAIN
if __name__ == "__main__":
    DATA_DIR = "./camera_frames"
    DB_PATH = "detections_optimized.db"
    
    # Initialize with PREPROCESSING ONLY (recommended)
    detector = OptimizedBatchDetector(
        model_name='yolo11l.pt',
        db_path=DB_PATH,
        use_preprocessing=True,   
        use_tta=False              
    )
    
    # Process
    detector.batch_process(DATA_DIR, resume=True)
    time.sleep(30)
    cleanup_frames("./camera_frames")