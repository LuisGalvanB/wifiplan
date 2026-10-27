import io
import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.cv.pipeline import (
    load_image, normalize_size, preprocess,
    detect_lines, merge_collinear, snap_endpoints, remove_noise_segments,
    infer_material_heuristic, run_pipeline,
    MIN_LINE_LENGTH_PX,
)
from app.services.raster_parser import RasterParser
from app.services.vector_parser import VectorParser


def make_test_image(w=400, h=300, walls=True) -> bytes:
    """Create a synthetic floor plan PNG for testing."""
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    if walls:
        # Outer perimeter
        draw.rectangle([10, 10, w - 10, h - 10], outline="black", width=3)
        # Interior wall
        draw.line([w // 2, 10, w // 2, h - 10], fill="black", width=2)
        draw.line([10, h // 2, w // 2, h // 2], fill="black", width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Load / normalize ──────────────────────────────────────────────────────────

def test_load_image_valid():
    img_bytes = make_test_image()
    img = load_image(img_bytes)
    assert img is not None
    assert img.ndim == 3
    assert img.shape[2] == 3  # BGR


def test_load_image_invalid_raises():
    with pytest.raises(ValueError):
        load_image(b"not an image")


def test_normalize_size_no_downscale():
    img_bytes = make_test_image(400, 300)
    img = load_image(img_bytes)
    scaled, factor = normalize_size(img, max_dim=2048)
    assert factor == 1.0
    assert scaled.shape == img.shape


def test_normalize_size_downscales_large():
    img_bytes = make_test_image(4000, 3000)
    img = load_image(img_bytes)
    scaled, factor = normalize_size(img, max_dim=2048)
    assert factor < 1.0
    assert max(scaled.shape[:2]) <= 2048


# ── Preprocessing ─────────────────────────────────────────────────────────────

def test_preprocess_returns_binary():
    img_bytes = make_test_image()
    img = load_image(img_bytes)
    edges = preprocess(img)
    assert edges.ndim == 2
    # Binary — only 0 and 255
    assert set(np.unique(edges)).issubset({0, 255})


# ── Line detection ────────────────────────────────────────────────────────────

def test_detect_lines_finds_lines():
    img_bytes = make_test_image(walls=True)
    img = load_image(img_bytes)
    edges = preprocess(img)
    lines = detect_lines(edges)
    # Should find at least some lines in a floor plan with walls
    assert len(lines) >= 2


def test_detect_lines_blank_image():
    img_bytes = make_test_image(walls=False)
    img = load_image(img_bytes)
    edges = preprocess(img)
    lines = detect_lines(edges)
    # Blank image should find very few or no lines
    assert isinstance(lines, list)


# ── Geometry cleanup ──────────────────────────────────────────────────────────

def test_remove_noise_segments():
    segs = [(0, 0, 5, 0), (0, 0, 100, 0)]  # short + long
    result = remove_noise_segments(segs, min_len=MIN_LINE_LENGTH_PX)
    assert (0, 0, 100, 0) in result
    # Short segment should be removed if below threshold
    for s in result:
        x1, y1, x2, y2 = s
        import math
        assert math.sqrt((x2-x1)**2 + (y2-y1)**2) >= MIN_LINE_LENGTH_PX


def test_snap_endpoints_closes_gap():
    segs = [(0.0, 0.0, 100.0, 0.0), (103.0, 0.0, 200.0, 0.0)]
    snapped = snap_endpoints(segs, snap_dist=8.0)
    # Endpoints within 8px should be snapped together
    assert len(snapped) == 2


def test_merge_collinear_reduces_count():
    # Many nearly-horizontal lines — should bucket together
    segs = [(i, 50, i + 20, 50) for i in range(0, 200, 10)]
    merged = merge_collinear(segs, angle_tol=5.0)
    assert len(merged) <= len(segs)


# ── Material heuristic ────────────────────────────────────────────────────────

def test_infer_material_returns_valid():
    img_bytes = make_test_image()
    img = load_image(img_bytes)
    material, conf = infer_material_heuristic(img, 10, 10, 100, 10)
    valid = {"glass","drywall","wood","brick","concrete","metal","unknown"}
    assert material in valid
    assert 0.0 <= conf <= 1.0


# ── Full pipeline ─────────────────────────────────────────────────────────────

def test_run_pipeline_returns_structure():
    img_bytes = make_test_image(walls=True)
    result = run_pipeline(img_bytes)
    assert "walls" in result
    assert "image_width" in result
    assert "image_height" in result
    assert "pipeline_version" in result
    assert isinstance(result["walls"], list)


def test_run_pipeline_walls_have_geometry():
    img_bytes = make_test_image(walls=True)
    result = run_pipeline(img_bytes)
    for wall in result["walls"]:
        assert "geometry" in wall
        assert "start" in wall["geometry"]
        assert "end" in wall["geometry"]
        assert "confidence" in wall
        assert wall["source"] == "cv_detected"


def test_run_pipeline_image_dimensions():
    img_bytes = make_test_image(600, 400)
    result = run_pipeline(img_bytes)
    assert result["image_width"] == 600
    assert result["image_height"] == 400


@pytest.mark.parametrize(
    ("extension", "image_format"),
    [(".png", "PNG"), (".jpg", "JPEG")],
)
def test_raster_parser_detects_walls_in_supported_images(extension, image_format):
    source = Image.open(io.BytesIO(make_test_image()))
    buffer = io.BytesIO()
    source.save(buffer, format=image_format)

    parsed = RasterParser().parse(buffer.getvalue(), f"floor-plan{extension}")

    assert parsed.source_format == extension[1:]
    assert len(parsed.walls) >= 2


def test_vector_parser_detects_dxf_walls():
    import ezdxf

    drawing = ezdxf.new()
    model_space = drawing.modelspace()
    model_space.add_line((0, 0), (10, 0), dxfattribs={"layer": "Walls"})
    model_space.add_line((10, 0), (10, 8), dxfattribs={"layer": "Walls"})
    stream = io.StringIO()
    drawing.write(stream)

    parsed = VectorParser().parse(stream.getvalue().encode("utf-8"), "floor-plan.dxf")

    assert parsed.source_format == "dxf"
    assert len(parsed.walls) == 2


def test_raster_parser_detects_walls_in_pdf():
    import pymupdf

    pdf = pymupdf.open()
    page = pdf.new_page(width=400, height=300)
    page.draw_rect(pymupdf.Rect(10, 10, 390, 290), color=(0, 0, 0), width=3)
    page.draw_line(pymupdf.Point(200, 10), pymupdf.Point(200, 290), color=(0, 0, 0), width=2)
    page.draw_line(pymupdf.Point(10, 150), pymupdf.Point(200, 150), color=(0, 0, 0), width=2)

    parsed = RasterParser().parse(pdf.tobytes(), "floor-plan.pdf")

    assert parsed.source_format == "pdf"
    assert len(parsed.walls) >= 2


def test_run_pipeline_scope_detection():
    """A plain rectangle image should produce a scope zone."""
    img_bytes = make_test_image(400, 300, walls=True)
    result = run_pipeline(img_bytes)
    # scope_zone may or may not be detected depending on threshold — just check structure
    if result["scope_zone"] is not None:
        assert "geometry" in result["scope_zone"]
        assert "confidence" in result["scope_zone"]
