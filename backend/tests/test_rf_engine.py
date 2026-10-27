import numpy as np
import pytest
from app.services.rf_engine import (
    compute_heatmap, compute_coverage_stats, heatmap_to_rgba_png,
    APPoint, Seg, RSSI_GOOD, RSSI_FAIR, RSSI_MIN, BAND_PARAMS,
    _free_space_path_loss_db, _segments_intersect, count_wall_intersections,
)


# ── Path loss ─────────────────────────────────────────────────────────────────

def test_fspl_increases_with_distance():
    pl1 = _free_space_path_loss_db(1, 5.25)
    pl10 = _free_space_path_loss_db(10, 5.25)
    assert pl10 > pl1


def test_fspl_increases_with_frequency():
    pl_2g = _free_space_path_loss_db(5, 2.45)
    pl_5g = _free_space_path_loss_db(5, 5.25)
    assert pl_5g > pl_2g


def test_fspl_minimum_clamp():
    # Should not crash at zero distance
    pl = _free_space_path_loss_db(0, 5.25)
    assert np.isfinite(pl)


# ── Intersection ──────────────────────────────────────────────────────────────

def test_segments_intersect_crossing():
    # + shaped cross
    assert _segments_intersect(0, 1, 2, 1,  1, 0, 1, 2) is True


def test_segments_no_intersection_parallel():
    assert _segments_intersect(0, 0, 10, 0,  0, 5, 10, 5) is False


def test_segments_no_intersection_collinear():
    assert _segments_intersect(0, 0, 5, 0,  6, 0, 10, 0) is False


# ── Wall attenuation accumulation ────────────────────────────────────────────

def test_wall_intersection_accumulates():
    walls = [
        Seg(50, 0, 50, 200, 5.0),   # vertical wall at x=50
        Seg(100, 0, 100, 200, 8.0), # vertical wall at x=100
    ]
    # Ray from (0,100) to (200,100) crosses both walls
    atten = count_wall_intersections(0, 100, 200, 100, walls)
    assert atten == pytest.approx(13.0)


def test_no_wall_intersection_zero_attenuation():
    walls = [Seg(200, 0, 200, 200, 5.0)]
    # Ray stays left of wall
    atten = count_wall_intersections(0, 50, 100, 50, walls)
    assert atten == 0.0


# ── Heatmap computation ───────────────────────────────────────────────────────

def test_heatmap_shape():
    ap = APPoint(x_px=100, y_px=100, tx_power_dbm=20, antenna_gain_dbi=3)
    hm = compute_heatmap(200, 200, 20.0, [ap], [], band="5", grid_res=20)
    assert hm.shape == (10, 10)  # 200/20 = 10 cells


def test_heatmap_peak_near_ap():
    """Cell nearest AP should have higher RSSI than far corner."""
    ap = APPoint(x_px=100, y_px=100, tx_power_dbm=20, antenna_gain_dbi=3)
    hm = compute_heatmap(200, 200, 20.0, [ap], [], band="5", grid_res=20)
    center_val = hm[5, 5]   # near AP
    corner_val = hm[0, 0]   # far corner
    assert center_val > corner_val


def test_heatmap_with_wall_attenuates():
    """Wall between AP and receiver should lower RSSI on far side."""
    ap = APPoint(x_px=10, y_px=100, tx_power_dbm=20, antenna_gain_dbi=3)
    wall = Seg(100, 0, 100, 200, 12.0)  # heavy wall in the middle
    hm_open = compute_heatmap(200, 200, 20.0, [ap], [], band="5", grid_res=20)
    hm_wall = compute_heatmap(200, 200, 20.0, [ap], [wall], band="5", grid_res=20)
    # Far side of wall should be lower with wall present
    assert hm_wall[5, 9] < hm_open[5, 9]


def test_heatmap_no_aps_returns_noise_floor():
    hm = compute_heatmap(200, 200, 20.0, [], [], band="5", grid_res=20)
    assert np.all(hm == RSSI_MIN)


def test_multiple_aps_max_combining():
    """Multiple APs: each cell should benefit from best AP."""
    ap1 = APPoint(x_px=20, y_px=100, tx_power_dbm=17, antenna_gain_dbi=3)
    ap2 = APPoint(x_px=180, y_px=100, tx_power_dbm=17, antenna_gain_dbi=3)
    hm_both = compute_heatmap(200, 200, 20.0, [ap1, ap2], [], band="5", grid_res=20)
    hm_ap1 = compute_heatmap(200, 200, 20.0, [ap1], [], band="5", grid_res=20)
    # With two APs, minimum RSSI should be higher
    assert np.min(hm_both) >= np.min(hm_ap1)


# ── Coverage stats ────────────────────────────────────────────────────────────

def test_coverage_stats_all_good():
    hm = np.full((10, 10), RSSI_GOOD, dtype=np.float32)
    stats = compute_coverage_stats(hm)
    assert stats["coverage_good_pct"] == pytest.approx(100.0)
    assert stats["coverage_poor_pct"] == pytest.approx(0.0)


def test_coverage_stats_empty():
    stats = compute_coverage_stats(np.array([]).reshape(0, 0))
    assert stats["good"] == 0


def test_coverage_stats_mixed():
    hm = np.array([[RSSI_GOOD, RSSI_FAIR, RSSI_MIN]], dtype=np.float32)
    stats = compute_coverage_stats(hm)
    assert stats["coverage_good_pct"] > 0
    assert stats["coverage_poor_pct"] > 0


# ── PNG export ────────────────────────────────────────────────────────────────

def test_heatmap_to_png_returns_bytes():
    ap = APPoint(x_px=50, y_px=50, tx_power_dbm=20, antenna_gain_dbi=3)
    hm = compute_heatmap(100, 100, 20.0, [ap], [], band="5", grid_res=10)
    png = heatmap_to_rgba_png(hm)
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


# ── Band params ───────────────────────────────────────────────────────────────

def test_all_bands_defined():
    for band in ["2.4", "5", "6"]:
        assert band in BAND_PARAMS
        bp = BAND_PARAMS[band]
        assert bp.freq_ghz > 0
        assert bp.path_loss_exp_nlos > bp.path_loss_exp_los
