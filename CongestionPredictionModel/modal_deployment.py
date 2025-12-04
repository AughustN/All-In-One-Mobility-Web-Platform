import modal
from pathlib import Path
import base64

app = modal.App("hcm-yolo-detector")

image = (
    modal.Image.debian_slim()
    .pip_install([
        "ultralytics",
        "opencv-python-headless",
        "numpy",
        "Pillow",
        "torch",
        "torchvision"
    ])
)

# Create persistent volume for model storage
model_volume = modal.Volume.from_name("yolo-models", create_if_missing=True)

@app.function(
    image=image,
    gpu="T4",
    timeout=600,
    volumes={"/models": model_volume}  # Mount persistent storage
)
def detect_images_batch(images_b64: list[str], camera_ids: list[str]):
    """
    Run YOLO detection on a batch of images.
    
    Args:
        images_b64: List of base64-encoded images
        camera_ids: List of corresponding camera IDs
        
    Returns:
        List of detection results
    """
    from ultralytics.models import YOLO
    import cv2
    import numpy as np
    import base64
    from io import BytesIO
    from PIL import Image
    
    # Load model from persistent volume (cached after first run)
    model_path = "/models/yolo11l.pt"
    try:
        model = YOLO(model_path)
    except:
        # Download model on first run
        model = YOLO("yolo11l.pt")
        model.save(model_path)
        model_volume.commit()  # Save to persistent storage
    
    results = []
    
    for img_b64, cam_id in zip(images_b64, camera_ids):
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_bytes))
            img_np = np.array(img)
            
            # Run detection
            detections = model.predict(
                img_np,
                conf=0.20,
                iou=0.45,
                verbose=False
            )
            
            # Extract detection data
            detection_data = {
                "camera_id": cam_id,
                "detections": []
            }
            
            if len(detections) > 0 and detections[0].boxes is not None:
                boxes = detections[0].boxes
                for box in boxes:
                    detection_data["detections"].append({
                        "class_id": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })
            
            results.append(detection_data)
            
        except Exception as e:
            print(f"Error processing camera {cam_id}: {e}")
            results.append({
                "camera_id": cam_id,
                "error": str(e)
            })
    
    return results


@app.local_entrypoint()
def main():
    """Test the Modal function locally"""
    import base64
    
    # Read test images and encode to base64
    test_image_paths = [
        "./camera_frames/5875cef0b807da0011e33d14/2024-01-15_10-30-00.jpg",
        "./camera_frames/5a8267fe5058170011f6eae1/2024-01-15_10-30-00.jpg"
    ]
    
    images_b64 = []
    for path in test_image_paths:
        with open(path, "rb") as f:
            images_b64.append(base64.b64encode(f.read()).decode())
    
    camera_ids = ["5875cef0b807da0011e33d14", "5a8267fe5058170011f6eae1"]
    
    results = detect_images_batch.remote(images_b64, camera_ids)
    print("Detection results:", results)