# wifiplan/backend/app/services/vector_parser.py

"""Parser for vector floor plans in DXF format."""
import logging
import tempfile
from typing import Optional, List
from pathlib import Path

from app.services.parser_base import (
    BaseParser, FloorPlanData, ParsedWall, 
    WallSourceType, WallClassification
)

logger = logging.getLogger(__name__)

# Layer names commonly used for walls in architectural drawings
WALL_LAYER_PATTERNS = [
    "wall", "walls", "muro", "muros", 
    "structure", "estructural", "load_bearing",
    "partition", "divisorio",
    "a-wall", "a-walls", "arch-wall",
]

# Threshold for merging near-collinear segments (in drawing units)
MERGE_THRESHOLD = 0.01
# Minimum wall length to consider (in drawing units)
MIN_WALL_LENGTH = 0.05


class VectorParser(BaseParser):
    """Parser for DXF files."""
    
    def supports(self, filename: str, content_type: Optional[str] = None) -> bool:
        ext = Path(filename).suffix.lower()
        return ext == ".dxf"
    
    def parse(self, file_content: bytes, filename: str) -> FloorPlanData:
        ext = Path(filename).suffix.lower()
        
        if ext == ".dxf":
            return self._parse_dxf_content(file_content, filename)
        raise ValueError(f"Unsupported vector format: {ext}")
    
    def _parse_dxf_content(self, dxf_content: bytes, filename: str) -> FloorPlanData:
        """Parse DXF content and extract walls."""
        import ezdxf

        # ezdxf.readfile detects the DXF encoding and supports both ASCII and binary files.
        try:
            with tempfile.TemporaryDirectory(prefix="wifiplan-dxf-") as temp_dir:
                dxf_path = Path(temp_dir) / "floor-plan.dxf"
                dxf_path.write_bytes(dxf_content)
                doc = ezdxf.readfile(dxf_path)
        except Exception as e:
            raise ValueError(f"Invalid DXF file: {e}")
        
        # Get modelspace
        msp = doc.modelspace()
        
        # Detect drawing units
        unit = self._detect_unit(doc)
        
        # Extract all lines and polylines
        raw_walls: List[ParsedWall] = []
        
        # Process LINE entities
        for entity in msp.query("LINE"):
            wall = self._line_to_wall(entity, doc)
            if wall:
                raw_walls.append(wall)
        
        # Process LWPOLYLINE entities (explode into segments)
        for entity in msp.query("LWPOLYLINE"):
            segments = self._polyline_to_walls(entity, doc)
            raw_walls.extend(segments)
        
        # Process POLYLINE entities (3D polylines)
        for entity in msp.query("POLYLINE"):
            segments = self._polyline_to_walls(entity, doc)
            raw_walls.extend(segments)
        
        # Filter and merge
        filtered = self._filter_walls(raw_walls)
        merged = self._merge_collinear_walls(filtered)
        
        # Classify walls by thickness and layer
        classified = self._classify_walls(merged)
        
        return FloorPlanData(
            walls=classified,
            source_format="dxf",
            drawing_unit=unit,
            metadata={
                "filename": filename,
                "entity_count": len(raw_walls),
                "layer_count": len(set(w.layer_name for w in raw_walls if w.layer_name)),
            }
        )
    
    def _detect_unit(self, doc) -> Optional[str]:
        """Detect drawing unit from DXF header."""
        try:
            # INSUNITS: 1=inches, 4=mm, 6=m
            insunits = doc.header.get("$INSUNITS", 0)
            unit_map = {
                1: "inches",
                4: "mm",
                6: "m",
            }
            return unit_map.get(insunits, None)
        except Exception:
            return None
    
    def _line_to_wall(self, entity, doc) -> Optional[ParsedWall]:
        """Convert a LINE entity to ParsedWall."""
        try:
            start = entity.dxf.start
            end = entity.dxf.end
            
            x1, y1 = start.x, start.y
            x2, y2 = end.x, end.y
            
            length = self._distance(x1, y1, x2, y2)
            if length < MIN_WALL_LENGTH:
                return None
            
            thickness = self._estimate_thickness(entity, doc)
            
            # 🔧 INVERTIR EL EJE Y para que coincida con el canvas del frontend
            # DXF usa sistema cartesiano (Y hacia arriba)
            # El frontend usa Y hacia abajo
            return ParsedWall(
                start_x=x1,
                start_y=-y1,  # ← Invertido
                end_x=x2,
                end_y=-y2,    # ← Invertido
                length_m=length,
                thickness_m=thickness,
                layer_name=entity.dxf.layer,
                source_type=WallSourceType.VECTORIAL,
                confidence=1.0,
                raw_properties={
                    "color": entity.dxf.color,
                    "linetype": entity.dxf.linetype,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to parse LINE entity: {e}")
            return None
    
    def _polyline_to_walls(self, entity, doc) -> List[ParsedWall]:
        """Convert a polyline to list of wall segments."""
        walls = []
        try:
            # Get points as list of (x, y)
            if hasattr(entity, "vertices"):  # POLYLINE
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            else:  # LWPOLYLINE
                points = [(p[0], p[1]) for p in entity.get_points()]
            
            if len(points) < 2:
                return []
            
            # Create wall for each segment
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                length = self._distance(x1, y1, x2, y2)
                
                if length < MIN_WALL_LENGTH:
                    continue
                
                thickness = self._estimate_thickness(entity, doc)
                
                # 🔧 INVERTIR EL EJE Y
                wall = ParsedWall(
                    start_x=x1,
                    start_y=-y1,  # ← Invertido
                    end_x=x2,
                    end_y=-y2,    # ← Invertido
                    length_m=length,
                    thickness_m=thickness,
                    layer_name=entity.dxf.layer,
                    source_type=WallSourceType.VECTORIAL,
                    confidence=1.0,
                )
                walls.append(wall)
            
            # If closed polyline, also close the loop
            if hasattr(entity, "closed") and entity.closed:
                if len(points) >= 3:
                    x1, y1 = points[-1]
                    x2, y2 = points[0]
                    length = self._distance(x1, y1, x2, y2)
                    if length >= MIN_WALL_LENGTH:
                        # 🔧 INVERTIR EL EJE Y
                        wall = ParsedWall(
                            start_x=x1,
                            start_y=-y1,  # ← Invertido
                            end_x=x2,
                            end_y=-y2,    # ← Invertido
                            length_m=length,
                            thickness_m=self._estimate_thickness(entity, doc),
                            layer_name=entity.dxf.layer,
                            source_type=WallSourceType.VECTORIAL,
                            confidence=1.0,
                        )
                        walls.append(wall)
            
            return walls
        except Exception as e:
            logger.warning(f"Failed to parse POLYLINE: {e}")
            return []
    
    def _estimate_thickness(self, entity, doc) -> Optional[float]:
        """
        Estimate wall thickness from entity properties.
        In DXF, thickness can be in:
        - Line weight (lineweight property)
        - Elevation / extrusion
        - Layer properties
        """
        try:
            # Try lineweight (0.01mm units, -1 = default)
            lw = getattr(entity.dxf, "lineweight", -1)
            if lw > 0 and lw < 200:
                # Convert from 0.01mm to mm
                return lw * 0.01 / 1000  # to meters
            
            # Try to infer from layer name patterns
            layer = entity.dxf.layer.lower()
            if "thick" in layer or "bearing" in layer:
                return 0.30  # Typical load-bearing wall
            elif "partition" in layer:
                return 0.15  # Typical partition wall
            elif "muro" in layer:
                return 0.25  # Generic wall
        except Exception:
            pass
        
        return None  # Unknown
    
    def _filter_walls(self, walls: List[ParsedWall]) -> List[ParsedWall]:
        """Filter out walls that are too short or on non-wall layers."""
        filtered = []
        
        for w in walls:
            # Skip very short walls (likely annotation lines)
            if w.length_m and w.length_m < MIN_WALL_LENGTH:
                continue
            
            filtered.append(w)
        
        return filtered
    
    def _merge_collinear_walls(self, walls: List[ParsedWall]) -> List[ParsedWall]:
        """
        Merge walls that are collinear and close to each other.
        Simplified implementation — groups by angle and proximity.
        """
        if len(walls) < 2:
            return walls
        
        # Group by angle buckets
        from collections import defaultdict
        groups = defaultdict(list)
        
        for w in walls:
            angle = self._line_angle(w.start_x, w.start_y, w.end_x, w.end_y)
            # Round angle to nearest 5 degrees
            bucket = round(angle / 5) * 5
            groups[bucket].append(w)
        
        merged = []
        for _, group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
                continue
            
            # Sort by x-coordinate
            group.sort(key=lambda w: min(w.start_x, w.end_x))
            
            # Merge overlapping segments
            current = group[0]
            for next_w in group[1:]:
                # Check if endpoints are close
                dist = self._distance(
                    current.end_x, current.end_y,
                    next_w.start_x, next_w.start_y
                )
                if dist < MERGE_THRESHOLD:
                    # Extend current
                    current.end_x = next_w.end_x
                    current.end_y = next_w.end_y
                    current.length_m = self._distance(
                        current.start_x, current.start_y,
                        current.end_x, current.end_y
                    )
                else:
                    merged.append(current)
                    current = next_w
            
            merged.append(current)
        
        return merged
    
    def _classify_walls(self, walls: List[ParsedWall]) -> List[ParsedWall]:
        """
        Classify each wall as load-bearing, partition, or unknown.
        Based on thickness and layer name patterns.
        """
        for w in walls:
            layer = (w.layer_name or "").lower()
            
            # Determine classification
            if w.thickness_m is not None:
                if w.thickness_m >= 0.25:  # >25cm
                    w.classification = WallClassification.LOAD_BEARING
                elif w.thickness_m >= 0.10:  # 10-25cm
                    w.classification = WallClassification.PARTITION
            else:
                # Use layer name patterns
                if any(term in layer for term in ["bearing", "estructural", "load", "carga"]):
                    w.classification = WallClassification.LOAD_BEARING
                elif any(term in layer for term in ["partition", "divisorio", "interior"]):
                    w.classification = WallClassification.PARTITION
                else:
                    w.classification = WallClassification.UNKNOWN
        
        return walls
    
    @staticmethod
    def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    
    @staticmethod
    def _line_angle(x1: float, y1: float, x2: float, y2: float) -> float:
        import math
        return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180