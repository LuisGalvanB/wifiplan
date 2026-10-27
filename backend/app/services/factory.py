# \wifiplan\backend\app\services\factory.py

"""
Parser factory — detects file type and returns appropriate parser.
"""
from pathlib import Path
from typing import Optional, List
import logging

from app.services.parser_base import BaseParser, FloorPlanData
from app.services.raster_parser import RasterParser
from app.services.vector_parser import VectorParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory that selects the appropriate parser based on file type."""
    
    _parsers: List[BaseParser] = []
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        if not cls._initialized:
            cls._parsers = [
                VectorParser(),   # DXF
                RasterParser(),   # PNG, JPG, JPEG, PDF
            ]
            cls._initialized = True
    
    @classmethod
    def get_parser(cls, filename: str, content_type: Optional[str] = None) -> Optional[BaseParser]:
        """Get the appropriate parser for the given file."""
        cls._initialize()
        
        for parser in cls._parsers:
            if parser.supports(filename, content_type):
                return parser
        
        return None
    
    @classmethod
    def parse(cls, file_content: bytes, filename: str, content_type: Optional[str] = None) -> FloorPlanData:
        """Parse file content using the appropriate parser."""
        parser = cls.get_parser(filename, content_type)
        if parser is None:
            ext = Path(filename).suffix.lower()
            supported = cls.get_supported_extensions()
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {', '.join(supported)}"
            )
        
        logger.info(f"Using parser: {parser.__class__.__name__} for {filename}")
        return parser.parse(file_content, filename)
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported extensions."""
        cls._initialize()
        extensions = []
        for parser in cls._parsers:
            # Simple heuristic: check the supports method
            # We test with common extensions
            test_files = [
                "test.png", "test.jpg", "test.jpeg", "test.pdf",
                "test.dxf",
            ]
            for f in test_files:
                if parser.supports(f):
                    ext = Path(f).suffix
                    if ext not in extensions:
                        extensions.append(ext)
        return sorted(extensions)