# backend/app/services/parsers/wall_conversion.py

"""
Helpers para convertir entre tipos de parser y modelos de base de datos.
Estas funciones se usan cuando se guardan paredes detectadas desde archivos
vectoriales o raster en la base de datos.
"""

from app.services.parser_base import WallClassification, WallSourceType
from app.models.geometry import WallType, GeometrySourceType


def classification_to_wall_type(classif: WallClassification) -> WallType:
    """
    Convert parser classification to model WallType.
    
    Args:
        classif: Clasificación del parser (LOAD_BEARING, PARTITION, UNKNOWN)
    
    Returns:
        WallType: Tipo de pared para la base de datos
    """
    mapping = {
        WallClassification.LOAD_BEARING: WallType.exterior,
        WallClassification.PARTITION: WallType.partition,
        WallClassification.UNKNOWN: WallType.unknown,
    }
    return mapping.get(classif, WallType.unknown)


def wall_type_to_classification(wall_type: WallType) -> WallClassification:
    """
    Convert model WallType to parser classification (inverso).
    
    Args:
        wall_type: Tipo de pared del modelo
    
    Returns:
        WallClassification: Clasificación para el parser
    """
    mapping = {
        WallType.exterior: WallClassification.LOAD_BEARING,
        WallType.interior: WallClassification.PARTITION,
        WallType.partition: WallClassification.PARTITION,
        WallType.column: WallClassification.UNKNOWN,
        WallType.unknown: WallClassification.UNKNOWN,
    }
    return mapping.get(wall_type, WallClassification.UNKNOWN)


def source_type_to_string(source: WallSourceType) -> str:
    """
    Convert parser source type to string for database.
    
    Args:
        source: Tipo de fuente del parser (VECTORIAL, RASTER, UNKNOWN)
    
    Returns:
        str: Valor para guardar en la columna 'source_type'
    """
    mapping = {
        WallSourceType.VECTORIAL: "vectorial",
        WallSourceType.RASTER: "raster",
        WallSourceType.UNKNOWN: "manual",
    }
    return mapping.get(source, "manual")


def string_to_source_type(source_str: str) -> WallSourceType:
    """
    Convert database source_type string to parser source type (inverso).
    
    Args:
        source_str: Valor de la columna 'source_type' en la base de datos
    
    Returns:
        WallSourceType: Tipo de fuente para el parser
    """
    mapping = {
        "vectorial": WallSourceType.VECTORIAL,
        "raster": WallSourceType.RASTER,
        "manual": WallSourceType.UNKNOWN,
        "cv_detected": WallSourceType.RASTER,
        "ml_detected": WallSourceType.RASTER,
        "imported": WallSourceType.UNKNOWN,
    }
    return mapping.get(source_str, WallSourceType.UNKNOWN)


def geometry_source_to_string(source: GeometrySourceType) -> str:
    """
    Convert GeometrySourceType to string for database.
    
    Args:
        source: Tipo de fuente de geometría
    
    Returns:
        str: Valor para la columna 'source_type'
    """
    mapping = {
        GeometrySourceType.manual: "manual",
        GeometrySourceType.cv_detected: "raster",
        GeometrySourceType.ml_detected: "raster",
        GeometrySourceType.imported: "manual",
        GeometrySourceType.vectorial: "vectorial",  # Nuevo
        GeometrySourceType.raster: "raster",        # Nuevo
    }
    return mapping.get(source, "manual")


def create_parser_from_wall(wall) -> dict:
    """
    Crear un diccionario con la información del parser a partir de un Wall.
    Útil para exportar o enviar al frontend.
    
    Args:
        wall: Instancia de Wall (SQLAlchemy)
    
    Returns:
        dict: Datos del parser
    """
    return {
        "id": str(wall.id),
        "start_x": wall.geometry.get("start", {}).get("x", 0),
        "start_y": wall.geometry.get("start", {}).get("y", 0),
        "end_x": wall.geometry.get("end", {}).get("x", 0),
        "end_y": wall.geometry.get("end", {}).get("y", 0),
        "classification": wall_type_to_classification(wall.wall_type),
        "source_type": string_to_source_type(getattr(wall, "source_type", "manual")),
        "confidence": wall.confidence,
        "thickness_m": wall.thickness_m,
    }