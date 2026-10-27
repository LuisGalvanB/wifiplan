# wifiplan/backend/app/services/raster_parser.py

"""
Parser for raster floor plans: PNG, JPG, JPEG, and PDF (converted to image).
Uses OpenCV pipeline for wall detection.
"""
import io
import logging
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np

from app.services.parser_base import (
    BaseParser, FloorPlanData, ParsedWall,
    WallSourceType, WallClassification
)

logger = logging.getLogger(__name__)


class RasterParser(BaseParser):
    """Parser for raster image files."""
    
    # Configuration for wall detection
    MIN_LINE_LENGTH_PX = 30
    MAX_LINE_GAP_PX = 15
    HOUGH_THRESHOLD = 50
    MAX_IMAGE_DIM = 2048
    
    def supports(self, filename: str, content_type: Optional[str] = None) -> bool:
        ext = Path(filename).suffix.lower()
        image_exts = [".png", ".jpg", ".jpeg", ".pdf"]
        return ext in image_exts
    
    def parse(self, file_content: bytes, filename: str) -> FloorPlanData:
        ext = Path(filename).suffix.lower()
        
        # Convert PDF to image if needed
        if ext == ".pdf":
            image_bytes = self._pdf_to_image(file_content)
        else:
            image_bytes = file_content
        
        # Load image
        img, img_width, img_height = self._load_image(image_bytes)
        
        # Run CV pipeline
        walls = self._detect_walls(img)
        
        # Convertir paredes detectadas (coordenadas en píxeles)
        parsed_walls = []
        for w in walls:
            parsed_wall = ParsedWall(
                start_x=float(w.start_x),
                start_y=float(w.start_y),
                end_x=float(w.end_x),
                end_y=float(w.end_y),
                length_m=None,  # Desconocido hasta calibración
                thickness_m=self._estimate_thickness_px(img, w.start_x, w.start_y, w.end_x, w.end_y),
                classification=w.classification,
                source_type=WallSourceType.RASTER,
                confidence=w.confidence,
                raw_properties={
                    "coordinate_system": "pixels",
                    "pixel_length": self._distance(
                        w.start_x, w.start_y,
                        w.end_x, w.end_y,
                    ),
                }
            )
            parsed_walls.append(parsed_wall)
        
        return FloorPlanData(
            walls=parsed_walls,
            image_width_px=img_width,
            image_height_px=img_height,
            source_format=ext[1:] if ext.startswith(".") else ext,
            drawing_unit="px",  # Pixels until calibrated
            metadata={
                "filename": filename,
                "detected_walls": len(parsed_walls),
                "pipeline_version": "cv-2.0",
            }
        )
    
    def _pdf_to_image(self, pdf_content: bytes) -> bytes:
        """Convert first page of PDF to PNG image."""
        try:
            import pymupdf as fitz
            
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            if len(doc) == 0:
                raise ValueError("PDF has no pages")
            
            # Use first page
            page = doc[0]
            # Render at 150 DPI for good quality
            zoom = 150 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            doc.close()
            return img_bytes
            
        except ImportError:
            # Fallback to pdf2image if PyMuPDF not available
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(pdf_content, first_page=1, last_page=1, dpi=150)
                if not images:
                    raise ValueError("PDF has no pages")
                img = images[0]
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                return img_bytes.getvalue()
            except ImportError:
                raise ImportError(
                    "Please install PyMuPDF or pdf2image: "
                    "pip install pymupdf  # or pip install pdf2image"
                )
    
    def _load_image(self, image_bytes: bytes) -> tuple[np.ndarray, int, int]:
        """Load image bytes into OpenCV format."""
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")
        
        h, w = img.shape[:2]
        
        # Resize if too large
        if max(h, w) > self.MAX_IMAGE_DIM:
            scale = self.MAX_IMAGE_DIM / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]
        
        return img, w, h
    
    def _detect_walls(self, img: np.ndarray) -> List[ParsedWall]:
        """
        Detect walls using OpenCV pipeline.
        Returns list of ParsedWall with estimated confidence.
        """
        # Preprocess
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Dilation to connect broken edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Hough Line Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.HOUGH_THRESHOLD,
            minLineLength=self.MIN_LINE_LENGTH_PX,
            maxLineGap=self.MAX_LINE_GAP_PX,
        )
        
        # Obtener altura de la imagen para invertir el eje Y
        img_height = img.shape[0]
        
        walls = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Skip very short lines
                length = self._distance(x1, y1, x2, y2)
                if length < self.MIN_LINE_LENGTH_PX:
                    continue
                
                # Estimate wall type and confidence
                wall_type, confidence = self._classify_wall_segment(img, x1, y1, x2, y2)
                
                # 🔧 INVERTIR EL EJE Y para que coincida con el canvas del frontend
                # OpenCV usa (0,0) en esquina superior izquierda, Y hacia abajo
                # El frontend usa Y hacia arriba, por eso invertimos
                walls.append(ParsedWall(
                    start_x=float(x1),
                    start_y=float(img_height - y1),  # ← Invertido
                    end_x=float(x2),
                    end_y=float(img_height - y2),    # ← Invertido
                    length_m=None,
                    thickness_m=None,  # Se estima después
                    classification=wall_type,
                    source_type=WallSourceType.RASTER,
                    confidence=confidence,
                ))
        
        # Filter and deduplicate
        filtered = self._filter_overlapping_walls(walls)
        return filtered
    
    def _classify_wall_segment(self, img: np.ndarray, x1, y1, x2, y2) -> tuple[WallClassification, float]:
        """
        Classify wall type and estimate confidence based on line thickness and context.
        """
        h, w = img.shape[:2]
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        
        # Sample a small ROI around midpoint
        roi_size = 10
        x0, y0 = max(0, cx - roi_size), max(0, cy - roi_size)
        x1e, y1e = min(w, cx + roi_size), min(h, cy + roi_size)
        roi = img[y0:y1e, x0:x1e]
        
        if roi.size == 0:
            return WallClassification.UNKNOWN, 0.3
        
        # Count dark pixels (wall pixels)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = np.sum(th > 0) / th.size
        
        # Estimate thickness from ROI
        thickness_px = self._estimate_thickness_px(img, x1, y1, x2, y2)
        
        # Classification heuristics
        if thickness_px and thickness_px > 8:
            # Thick lines → likely load-bearing
            confidence = min(0.8, 0.6 + (thickness_px - 8) * 0.02)
            return WallClassification.LOAD_BEARING, round(confidence, 2)
        elif thickness_px and thickness_px > 3:
            # Medium lines → partition walls
            confidence = min(0.7, 0.5 + (thickness_px - 3) * 0.05)
            return WallClassification.PARTITION, round(confidence, 2)
        else:
            # Thin lines → could be either
            if dark_ratio > 0.5:
                return WallClassification.PARTITION, 0.45
            else:
                return WallClassification.UNKNOWN, 0.30
    
    def _estimate_thickness_px(self, img: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> Optional[float]:
        """Estimate wall thickness in pixels from line segment."""
        if x1 is None or x2 is None:
            return None
        
        # Simple: use length of perpendicular sample
        # For MVP, use a fixed heuristic based on line length
        length = self._distance(x1, y1, x2, y2)
        if length < 50:
            return 3.0
        elif length < 200:
            return 5.0
        else:
            return 8.0
    
    def _filter_overlapping_walls(self, walls: List[ParsedWall], distance_threshold: float = 15.0) -> List[ParsedWall]:
        """Keep the longest representative of each duplicate wall segment."""
        if len(walls) < 2:
            return walls

        filtered = []
        for wall in sorted(
            walls,
            key=lambda item: self._distance(
                item.start_x, item.start_y, item.end_x, item.end_y
            ),
            reverse=True,
        ):
            duplicate = any(
                (
                    self._distance(
                        wall.start_x, wall.start_y, kept.start_x, kept.start_y
                    ) < distance_threshold
                    and self._distance(
                        wall.end_x, wall.end_y, kept.end_x, kept.end_y
                    ) < distance_threshold
                )
                or (
                    self._distance(
                        wall.start_x, wall.start_y, kept.end_x, kept.end_y
                    ) < distance_threshold
                    and self._distance(
                        wall.end_x, wall.end_y, kept.start_x, kept.start_y
                    ) < distance_threshold
                )
                for kept in filtered
            )
            if not duplicate:
                filtered.append(wall)
        
        return filtered
    
    @staticmethod
    def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5