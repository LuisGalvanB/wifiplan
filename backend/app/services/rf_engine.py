"""
RF Engine — Simplified MVP implementation.

What this does:
- Log-distance path loss model (ITU indoor model variant)
- Wall attenuation accumulation using ray-casting per grid cell
- Band-dependent path loss exponents
- Per-AP RSSI contribution with max-combining across APs

What this does NOT do (future enterprise model):
- Multipath / reflection modeling
- Diffraction around obstacles
- Floor penetration loss
- 3D propagation
- Calibrated site-survey model
- MIMO beamforming simulation
- Channel planning / interference simulation

This engine is designed to be cleanly replaceable.
"""

import numpy as np
from dataclasses import dataclass
from typing import NamedTuple


# ── Band-specific parameters ─────────────────────────────────────────────────

@dataclass
class BandParams:
    freq_ghz: float
    path_loss_exp_los: float    # free-space-ish
    path_loss_exp_nlos: float   # typical indoor
    wall_loss_multiplier: float # extra multiplier for partial wall penetration angle


BAND_PARAMS: dict[str, BandParams] = {
    "2.4": BandParams(freq_ghz=2.45, path_loss_exp_los=2.0, path_loss_exp_nlos=3.0, wall_loss_multiplier=1.0),
    "5":   BandParams(freq_ghz=5.25, path_loss_exp_los=2.0, path_loss_exp_nlos=3.3, wall_loss_multiplier=1.1),
    "6":   BandParams(freq_ghz=6.2,  path_loss_exp_los=2.0, path_loss_exp_nlos=3.5, wall_loss_multiplier=1.2),
}

# Coverage thresholds (dBm RSSI)
RSSI_GOOD  = -65.0
RSSI_FAIR  = -75.0
RSSI_MIN   = -95.0   # treat as noise floor


# ── Geometry helpers ──────────────────────────────────────────────────────────

class Seg(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float
    attenuation_db: float


def _free_space_path_loss_db(dist_m: float, freq_ghz: float) -> float:
    """FSPL in dB. Clamped at minimum 1m to avoid log(0)."""
    d = max(dist_m, 0.5)
    return 20 * np.log10(d) + 20 * np.log10(freq_ghz * 1e9) - 147.55


def _segments_intersect(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) -> bool:
    """Returns True if segment A intersects segment B."""
    def cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    d1 = cross(bx1, by1, bx2, by2, ax1, ay1)
    d2 = cross(bx1, by1, bx2, by2, ax2, ay2)
    d3 = cross(ax1, ay1, ax2, ay2, bx1, by1)
    d4 = cross(ax1, ay1, ax2, ay2, bx2, by2)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    return False


def count_wall_intersections(
    ap_x: float, ap_y: float,
    rx_x: float, rx_y: float,
    wall_segs: list[Seg],
) -> float:
    """
    Ray-cast from AP to receiver point.
    Returns accumulated wall attenuation dB.
    """
    total_db = 0.0
    for w in wall_segs:
        if _segments_intersect(ap_x, ap_y, rx_x, rx_y, w.x1, w.y1, w.x2, w.y2):
            total_db += w.attenuation_db
    return total_db


# ── AP dataclass ──────────────────────────────────────────────────────────────

@dataclass
class APPoint:
    x_px: float
    y_px: float
    tx_power_dbm: float
    antenna_gain_dbi: float


# ── Main heatmap computation ──────────────────────────────────────────────────

def compute_heatmap(
    width_px: int,
    height_px: int,
    scale_px_per_m: float,
    aps: list[APPoint],
    wall_segs: list[Seg],
    band: str = "5",
    grid_res: int = 10,
) -> np.ndarray:
    """
    Compute RSSI heatmap.

    Returns ndarray shape (H_grid, W_grid) with RSSI dBm values.
    Cells outside any AP range are clamped to RSSI_MIN.

    grid_res: pixel stride — lower = more accurate, slower.
    """
    bp = BAND_PARAMS.get(band, BAND_PARAMS["5"])

    gw = (width_px + grid_res - 1) // grid_res
    gh = (height_px + grid_res - 1) // grid_res

    heatmap = np.full((gh, gw), RSSI_MIN, dtype=np.float32)

    for gi in range(gh):
        for gj in range(gw):
            rx_x = gj * grid_res + grid_res / 2
            rx_y = gi * grid_res + grid_res / 2

            best_rssi = RSSI_MIN

            for ap in aps:
                dist_px = np.sqrt((rx_x - ap.x_px) ** 2 + (rx_y - ap.y_px) ** 2)
                dist_m = max(dist_px / scale_px_per_m, 0.3)

                # Path loss
                fspl = _free_space_path_loss_db(dist_m, bp.freq_ghz)
                # Additional indoor scatter factor based on distance
                scatter_loss = max(0.0, (dist_m - 1.0) * (bp.path_loss_exp_nlos - 2.0) * 0.5)

                # Wall attenuation
                wall_db = count_wall_intersections(ap.x_px, ap.y_px, rx_x, rx_y, wall_segs)
                wall_db *= bp.wall_loss_multiplier

                rssi = ap.tx_power_dbm + ap.antenna_gain_dbi - fspl - scatter_loss - wall_db
                best_rssi = max(best_rssi, rssi)

            heatmap[gi, gj] = max(best_rssi, RSSI_MIN)

    return heatmap


def compute_coverage_stats(heatmap: np.ndarray) -> dict:
    total = heatmap.size
    if total == 0:
        return {"good": 0, "fair": 0, "poor": 0, "min": 0, "max": 0, "avg": 0}

    good  = float(np.sum(heatmap >= RSSI_GOOD) / total * 100)
    fair  = float(np.sum((heatmap >= RSSI_FAIR) & (heatmap < RSSI_GOOD)) / total * 100)
    poor  = float(np.sum(heatmap < RSSI_FAIR) / total * 100)

    return {
        "coverage_good_pct": round(good, 2),
        "coverage_fair_pct": round(fair, 2),
        "coverage_poor_pct": round(poor, 2),
        "min_rssi_dbm": float(np.min(heatmap)),
        "max_rssi_dbm": float(np.max(heatmap)),
        "avg_rssi_dbm": float(np.mean(heatmap)),
    }


def heatmap_to_rgba_png(heatmap: np.ndarray) -> bytes:
    """
    Convert RSSI heatmap to RGBA PNG bytes for frontend rendering.
    Color map: green (good) → yellow (fair) → red (poor) → transparent (noise)
    """
    from PIL import Image

    h, w = heatmap.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Normalize to 0–1 range within RSSI_FAIR..RSSI_GOOD
    t = np.clip((heatmap - RSSI_FAIR) / (RSSI_GOOD - RSSI_FAIR), 0.0, 1.0)

    # Channels — interpolate green→yellow→red
    mask_signal = heatmap > RSSI_MIN + 5  # hide truly dead zones

    rgba[..., 0] = np.where(mask_signal, (255 * (1 - t * 0.5)).astype(np.uint8), 0)   # R
    rgba[..., 1] = np.where(mask_signal, (200 * t).astype(np.uint8), 0)                # G
    rgba[..., 2] = 0                                                                    # B
    rgba[..., 3] = np.where(mask_signal, 160, 0).astype(np.uint8)                      # A

    img = Image.fromarray(rgba)
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
