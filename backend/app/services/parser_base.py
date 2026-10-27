# \wifiplan\backend\app\services\parser_base.py
"""
Abstract base class for floor plan parsers.
All parsers must return a normalized FloorPlanData structure.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class WallSourceType(str, Enum):
    VECTORIAL = "vectorial"
    RASTER = "raster"
    UNKNOWN = "unknown"


class WallClassification(str, Enum):
    LOAD_BEARING = "portante"
    PARTITION = "divisorio"
    UNKNOWN = "desconocido"


@dataclass
class ParsedWall:
    """Single wall entity extracted from any input format."""
    # Geometry in drawing coordinates (meters if available)
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    length_m: Optional[float] = None
    thickness_m: Optional[float] = None
    classification: WallClassification = WallClassification.UNKNOWN
    source_type: WallSourceType = WallSourceType.UNKNOWN
    confidence: float = 1.0  # 0.0–1.0
    layer_name: Optional[str] = None
    raw_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FloorPlanData:
    """Normalized output from any parser."""
    walls: List[ParsedWall]
    image_width_px: Optional[int] = None
    image_height_px: Optional[int] = None
    source_format: str = "unknown"
    drawing_unit: Optional[str] = None  # "mm", "cm", "m", "inches", "px"
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """Abstract parser interface."""
    
    @abstractmethod
    def parse(self, file_content: bytes, filename: str) -> FloorPlanData:
        """Parse file content and return normalized floor plan data."""
        pass
    
    @abstractmethod
    def supports(self, filename: str, content_type: Optional[str] = None) -> bool:
        """Check if this parser can handle the given file."""
        pass