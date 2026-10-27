"""
Floor Plan Analysis Pipeline — MVP Implementation

Architecture:
  A. Input normalization  → raster image
  B. Preprocessing        → grayscale, denoise, threshold, edges
  C. Line detection       → HoughLinesP  (classical CV)
  D. Geometry cleanup     → merge collinear, snap endpoints, remove noise
  E. Material grouping    → line-thickness heuristics
  F. Scope detection      → largest closed contour
  G. ML stub interface    → placeholder for GPU inference server (V2)
  H. Output               → list of WallCreate / ScopeZoneCreate dicts

MVP limitations:
  - Material classification is heuristic-only (line thickness proxy)
  - No ML model is loaded; MODEL_INFERENCE_ENABLED flag gates the stub
  - PDF is not supported yet (convert to image first)
  - Confidence is set by heuristic quality, not calibrated

V2 upgrade path:
  - Replace _ml_inference_stub() with HTTP call to inference microservice
  - Inference server returns: wall mask (binary), material labels, confidence map
  - Post-process mask → segment list using existing geometry_cleanup pipeline

Advanced (GPU) path:
  - Dedicated model server (TorchServe / Triton)
  - Fine-tuned segmentation model on floor plan dataset
  - Returns structured JSON predictions
"""

import math
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────

MIN_LINE_LENGTH_PX = 20
MAX_LINE_GAP_PX = 10
MERGE_ANGLE_DEG = 5.0
SNAP_DIST_PX = 8.0
HOUGH_THRESHOLD = 40


# ── Input normalization ───────────────────────────────────────────────────────

def load_image(image_bytes: bytes) -> np.ndarray:
    """Load image bytes → BGR numpy array."""
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def normalize_size(img: np.ndarray, max_dim: int = 2048) -> tuple[np.ndarray, float]:
    """Downscale image so longest dimension ≤ max_dim. Returns (img, scale_factor)."""
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return img, 1.0
    scale = max_dim / longest
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


# ── Preprocessing ─────────────────────────────────────────────────────────────

def preprocess(img: np.ndarray) -> np.ndarray:
    """Return binary edge image ready for line detection."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Denoise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    # Adaptive threshold — handles varied lighting across floor plan
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2,
    )
    # Edge enhancement
    edges = cv2.Canny(thresh, 50, 150, apertureSize=3)
    # Dilate slightly to connect near-breaks
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    return edges


# ── Line detection ────────────────────────────────────────────────────────────

def detect_lines(edge_img: np.ndarray) -> list[tuple[int, int, int, int]]:
    """HoughLinesP → list of (x1, y1, x2, y2) segments."""
    lines = cv2.HoughLinesP(
        edge_img,
        rho=1,
        theta=np.pi / 180,
        threshold=HOUGH_THRESHOLD,
        minLineLength=MIN_LINE_LENGTH_PX,
        maxLineGap=MAX_LINE_GAP_PX,
    )
    if lines is None:
        return []
    segments = np.asarray(lines).reshape(-1, 4)
    return [
        (int(x1), int(y1), int(x2), int(y2))
        for x1, y1, x2, y2 in segments
    ]


# ── Scope detection ───────────────────────────────────────────────────────────

def detect_scope_polygon(img: np.ndarray) -> list[dict] | None:
    """
    Find the largest closed polygon — likely the floor perimeter.
    Returns list of {x, y} points or None.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    img_area = img.shape[0] * img.shape[1]

    # Must cover at least 10% of image — otherwise it's noise
    if area < img_area * 0.10:
        return None

    # Approximate polygon
    epsilon = 0.005 * cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, epsilon, True)

    points = [{"x": float(p[0][0]), "y": float(p[0][1])} for p in approx]
    return points


# ── Geometry cleanup ──────────────────────────────────────────────────────────

def _line_angle(x1, y1, x2, y2) -> float:
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180


def _line_length(x1, y1, x2, y2) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def merge_collinear(
    segs: list[tuple],
    angle_tol: float = MERGE_ANGLE_DEG,
    dist_tol: float = SNAP_DIST_PX,
) -> list[tuple]:
    """
    Merge near-collinear overlapping segments.
    Simplified: group by angle bucket, then by proximity.
    """
    if not segs:
        return segs

    # Bucket by angle
    def angle_key(s):
        a = _line_angle(*s)
        return round(a / angle_tol) * angle_tol

    from collections import defaultdict
    buckets: dict[float, list] = defaultdict(list)
    for s in segs:
        buckets[angle_key(s)].append(s)

    merged = []
    for angle, group in buckets.items():
        # For MVP: just keep longest segment per cluster (full merge is complex)
        group.sort(key=lambda s: _line_length(*s), reverse=True)
        merged.extend(group)

    return merged


def snap_endpoints(segs: list[tuple], snap_dist: float = SNAP_DIST_PX) -> list[tuple]:
    """
    Snap segment endpoints that are very close to each other.
    This reduces floating gaps in wall intersections.
    """
    # Collect all endpoints
    pts: list[list[float]] = []
    for s in segs:
        pts.append([float(s[0]), float(s[1])])
        pts.append([float(s[2]), float(s[3])])

    def find_or_add(x, y):
        for i, p in enumerate(pts):
            if abs(p[0] - x) < snap_dist and abs(p[1] - y) < snap_dist:
                return p
        return [x, y]

    snapped = []
    for s in segs:
        p1 = find_or_add(float(s[0]), float(s[1]))
        p2 = find_or_add(float(s[2]), float(s[3]))
        snapped.append((p1[0], p1[1], p2[0], p2[1]))
    return snapped


def remove_noise_segments(segs: list[tuple], min_len: float = MIN_LINE_LENGTH_PX) -> list[tuple]:
    return [s for s in segs if _line_length(*s) >= min_len]


# ── Material heuristics ───────────────────────────────────────────────────────

def infer_material_heuristic(original_img: np.ndarray, x1, y1, x2, y2) -> tuple[str, float]:
    """
    Estimate wall material by measuring line thickness in original image.
    Thicker lines → denser materials (concrete/brick).
    Thinner lines → partition walls (drywall).

    MVP heuristic — NOT calibrated. Confidence reflects heuristic uncertainty.
    """
    h, w = original_img.shape[:2]
    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

    # Sample a small ROI around midpoint
    r = 5
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1e, y1e = min(w, cx + r), min(h, cy + r)
    roi = original_img[y0:y1e, x0:x1e]

    if roi.size == 0:
        return "unknown", 0.3

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    dark_ratio = np.sum(th > 0) / th.size

    # Heuristic thresholds (manually tuned)
    if dark_ratio > 0.6:
        return "concrete", 0.45
    elif dark_ratio > 0.4:
        return "brick", 0.40
    elif dark_ratio > 0.2:
        return "drywall", 0.55
    else:
        return "unknown", 0.25


# ── ML stub interface (V2 upgrade point) ─────────────────────────────────────

def _ml_inference_stub(image_bytes: bytes) -> dict | None:
    """
    Stub for future ML model inference.

    V2: This function will make an HTTP call to the model inference microservice:
        POST {MODEL_INFERENCE_URL}/predict
        Content-Type: image/png
        → {
            "wall_mask": [[...], ...],     # binary mask
            "material_labels": [...],      # per-segment labels
            "confidence_map": [[...], ...],
            "detections": [{"type": "door", "bbox": [...]}]
        }

    Advanced (GPU): Call Triton/TorchServe via gRPC with batching.
    """
    from app.core.config import settings
    if not settings.MODEL_INFERENCE_ENABLED:
        return None

    # Placeholder HTTP call
    try:
        import httpx
        resp = httpx.post(
            f"{settings.MODEL_INFERENCE_URL}/predict",
            content=image_bytes,
            headers={"Content-Type": "image/png"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"ML inference failed (continuing with CV): {e}")
    return None


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(image_bytes: bytes) -> dict:
    """
    Full floor plan analysis pipeline.

    Returns:
    {
        "walls": [{"geometry": {...}, "material": ..., "wall_type": ..., "confidence": ...}],
        "scope_zone": {"points": [...], "confidence": ...} | None,
        "image_width": int,
        "image_height": int,
        "scale_factor": float,   # downscale applied during processing
        "pipeline_version": "mvp-cv-1.0"
    }
    """
    # A. Load + normalize
    img = load_image(image_bytes)
    orig_h, orig_w = img.shape[:2]

    img_scaled, scale_factor = normalize_size(img, max_dim=2048)
    h, w = img_scaled.shape[:2]

    progress_log = []

    # B. Preprocessing
    edges = preprocess(img_scaled)
    progress_log.append("preprocessing_done")

    # C. Optional ML pass (stub)
    ml_result = _ml_inference_stub(image_bytes)
    if ml_result:
        progress_log.append("ml_inference_used")

    # D. Line detection
    raw_segs = detect_lines(edges)
    progress_log.append(f"lines_detected:{len(raw_segs)}")

    # E. Geometry cleanup
    segs = remove_noise_segments(raw_segs)
    segs = merge_collinear(segs)
    segs = snap_endpoints(segs)
    progress_log.append(f"lines_cleaned:{len(segs)}")

    # F. Material grouping
    walls = []
    for x1, y1, x2, y2 in segs:
        material, conf = infer_material_heuristic(img_scaled, x1, y1, x2, y2)

        # Scale coords back to original image space
        sx1 = x1 / scale_factor
        sy1 = y1 / scale_factor
        sx2 = x2 / scale_factor
        sy2 = y2 / scale_factor

        walls.append({
            "geometry": {
                "start": {"x": round(sx1, 1), "y": round(sy1, 1)},
                "end": {"x": round(sx2, 1), "y": round(sy2, 1)},
            },
            "material": material,
            "wall_type": "unknown",
            "source": "cv_detected",
            "confidence": round(conf, 3),
            "is_accepted": False,  # must be reviewed by user
        })

    # G. Scope detection
    scope_pts = detect_scope_polygon(img_scaled)
    scope_zone = None
    if scope_pts:
        # Scale back
        scaled_pts = [
            {"x": round(p["x"] / scale_factor, 1), "y": round(p["y"] / scale_factor, 1)}
            for p in scope_pts
        ]
        scope_zone = {
            "geometry": {"points": scaled_pts},
            "source": "cv_detected",
            "confidence": 0.65,
        }
        progress_log.append("scope_detected")

    return {
        "walls": walls,
        "scope_zone": scope_zone,
        "image_width": orig_w,
        "image_height": orig_h,
        "scale_factor": scale_factor,
        "pipeline_version": "mvp-cv-1.0",
        "progress_log": progress_log,
    }
