"""
Image Matching Services
Shape recognition, contour extraction, and visual similarity
"""

from .background_remover import BackgroundRemover
from .contour_extractor import ContourExtractor
from .shape_descriptor import ShapeDescriptor
from .shape_embedder import ShapeEmbedder

__all__ = ["BackgroundRemover", "ContourExtractor", "ShapeDescriptor", "ShapeEmbedder"]
