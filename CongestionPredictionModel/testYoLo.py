"""Test a single image and return an output image with bounding boxes.

This script reuses the same model settings and class-specific thresholds
as `OptimizedBatchDetector` in `detector_batch.py`.

Run:
  python test_single_image_bbox.py --image ./sample.jpg --out ./sample_annotated.jpg

Optional:
  --model yolo11l.pt
  --preprocess            (apply CLAHE+denoise like detector_batch.py)
  --tta                   (Ultralytics augment=True)
  --imgsz 960             (default matches detector_batch.py)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from ultralytics import YOLO


VEHICLE_CLASSES: Dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Same per-class thresholds as detector_batch.py
CLASS_THRESHOLDS: Dict[int, float] = {
    2: 0.25,  # car
    3: 0.15,  # motorcycle
    5: 0.38,  # bus
    7: 0.30,  # truck
}


def build_clahe() -> cv2.CLAHE:
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))


def preprocess_image_bgr(img_bgr: np.ndarray, clahe: cv2.CLAHE) -> np.ndarray:
    """Apply CLAHE on L channel (LAB) + mild denoising."""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 7, 7, 7, 21)
    return enhanced


def draw_box(
    img: np.ndarray,
    xyxy: Tuple[int, int, int, int],
    label: str,
    conf: float,
) -> None:
    x1, y1, x2, y2 = xyxy

    # Box
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Label background
    text = f"{label} {conf:.2f}"
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    y_text = max(y1, th + 4)
    cv2.rectangle(img, (x1, y_text - th - 6), (x1 + tw + 6, y_text + baseline - 2), (0, 255, 0), -1)

    # Label text
    cv2.putText(
        img,
        text,
        (x1 + 3, y_text - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 0),
        2,
        lineType=cv2.LINE_AA,
    )


def run(
    image_path: Path,
    out_path: Path,
    model_name: str,
    preprocess: bool,
    tta: bool,
    imgsz: int,
    base_conf: float,
    iou: float,
) -> Dict[str, int]:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Failed to read image with OpenCV: {image_path}")

    if preprocess:
        img = preprocess_image_bgr(img, build_clahe())

    model = YOLO(model_name)
    try:
        model.to("cuda")
    except Exception:
        # OK: keep CPU
        pass

    results = model.predict(
        img,
        conf=base_conf,
        iou=iou,
        imgsz=imgsz,
        classes=list(VEHICLE_CLASSES.keys()),
        augment=tta,
        verbose=False,
        half=False,
    )

    annotated = img.copy()
    counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0}

    if results and len(results[0].boxes) > 0:
        boxes = results[0].boxes
        for b in boxes:
            conf = float(b.conf[0])
            cls = int(b.cls[0])

            thr = CLASS_THRESHOLDS.get(cls, base_conf)
            if conf < thr:
                continue

            label = VEHICLE_CLASSES.get(cls, str(cls))
            counts[label] = counts.get(label, 0) + 1

            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            draw_box(annotated, (x1, y1, x2, y2), label, conf)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out_path), annotated)
    if not ok:
        raise IOError(f"Failed to write output image: {out_path}")

    return counts


def main() -> None:
    p = argparse.ArgumentParser(description="Run YOLO on one image and save bounding-box output.")
    p.add_argument("--image", required=True, help="Path to the input image (jpg/png/etc.)")
    p.add_argument("--out", default=None, help="Output image path (default: <image>_bbox.jpg)")
    p.add_argument("--model", default="yolo11l.pt", help="Ultralytics model path/name")
    p.add_argument("--preprocess", action="store_true", help="Apply CLAHE+denoise preprocessing")
    p.add_argument("--tta", action="store_true", help="Enable test-time augmentation (augment=True)")
    p.add_argument("--imgsz", type=int, default=960, help="Inference image size")
    p.add_argument("--conf", type=float, default=0.20, help="Base confidence (YOLO conf=...)")
    p.add_argument("--iou", type=float, default=0.50, help="IoU threshold")

    args = p.parse_args()

    image_path = Path(args.image)
    out_path = Path(args.out) if args.out else image_path.with_name(image_path.stem + "_bbox.jpg")

    counts = run(
        image_path=image_path,
        out_path=out_path,
        model_name=args.model,
        preprocess=args.preprocess,
        tta=args.tta,
        imgsz=args.imgsz,
        base_conf=args.conf,
        iou=args.iou,
    )

    total = sum(counts.values())
    print("Done!")
    print(f"Input : {image_path}")
    print(f"Output: {out_path}")
    print(f"Total vehicles: {total}")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
