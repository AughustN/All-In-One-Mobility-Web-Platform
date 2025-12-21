import modal
from pathlib import Path
import base64
import numpy as np

app = modal.App("hcm-yolo-detector")

image = (
    modal.Image.debian_slim()
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install([
        "ultralytics",
        "opencv-python-headless",
        "numpy",
        "Pillow",
        "torch",
        "torchvision",
        "fastapi[standard]",
        "requests"
    ])
)

# Persistent volume for model storage
model_volume = modal.Volume.from_name("yolo-models", create_if_missing=True)
WEIGHTS_PATH = Path("/models/yolo11l.pt")
WEIGHTS_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt"

def ensure_weights():
    import requests
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not WEIGHTS_PATH.exists():
        print(f"Downloading YOLO weights to {WEIGHTS_PATH} ...")
        r = requests.get(WEIGHTS_URL, timeout=300)
        r.raise_for_status()
        WEIGHTS_PATH.write_bytes(r.content)
        model_volume.commit()
        print("Download complete.")

MODEL = None
def get_model():
    from ultralytics import YOLO
    global MODEL
    if MODEL is None:
        ensure_weights()
        MODEL = YOLO(str(WEIGHTS_PATH))
        print("YOLO model loaded.")
    return MODEL

@app.function(
    image=image,
    gpu="T4",
    timeout=600,
    volumes={"/models": model_volume}
)
@modal.fastapi_endpoint(method="POST")
def detect_images_batch_api(images_b64: list[str], camera_ids: list[str]):
    # Thin endpoint, better error surfacing
    from fastapi import HTTPException
    try:
        return detect_images_batch(images_b64, camera_ids)
    except Exception as e:
        import traceback
        print("Modal endpoint error:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

def detect_images_batch(images_b64: list[str], camera_ids: list[str]):
    """
    Run YOLO detection on a batch of images.
    """
    from io import BytesIO
    from PIL import Image

    if not images_b64 or not camera_ids or len(images_b64) != len(camera_ids):
        raise ValueError("images_b64 and camera_ids must be non-empty and same length")

    model = get_model()
    results = []

    for img_b64, cam_id in zip(images_b64, camera_ids):
        try:
            img_bytes = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(img)

            det = model.predict(img_np, conf=0.20, iou=0.45, verbose=False)

            detection_data = {"camera_id": cam_id, "detections": []}
            if det and det[0].boxes is not None:
                boxes = det[0].boxes
                for box in boxes:
                    detection_data["detections"].append({
                        "class_id": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "bbox": [float(v) for v in box.xyxy[0].tolist()]
                    })
            results.append(detection_data)
        except Exception as e:
            results.append({"camera_id": cam_id, "error": str(e)})

    return results


# @app.local_entrypoint()
# def main():
#     import base64
#     from pathlib import Path

#     root = Path("./camera_frames")
#     images_b64 = []
#     camera_ids = []

#     for cam_dir in sorted(root.iterdir()):
#         if cam_dir.is_dir():
#             jpgs = sorted(cam_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
#             if jpgs:
#                 with open(jpgs[0], "rb") as f:
#                     images_b64.append(base64.b64encode(f.read()).decode())
#                 camera_ids.append(cam_dir.name)

#     if not images_b64:
#         print("No .jpg images found in ./camera_frames")
#         return

#     # Invoke the function in a Modal container
#     results = detect_images_batch.remote(images_b64, camera_ids)
#     print("Detection results:", results)
