"""Entity Recognition for Product Fields"""
import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Single extracted entity"""
    field: str
    value: str
    confidence: float
    pattern: str  # Which pattern matched


class EntityRecognizer:
    """
    Extract product entities from OCR text.
    
    Entities:
    - Product code (CODE, ITEM, 제품코드)
    - Product name (제품명, 품명)
    - Capacity (용량: 50ml, 100ml)
    - Neck size (넥: 20파이, 24파이)
    - Material (재질: PET, PP, PE)
    - MOQ (최소주문: 5000개)
    - Price (가격, 단가)
    - Supplier (업체, 제조사)
    """
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize regex patterns for each entity type"""
        return {
            'product_code': [
                {'pattern': r'(?:제품)?코드[:\s]*([A-Z0-9-]+)', 'confidence': 0.9},
                {'pattern': r'ITEM[:\s]*([A-Z0-9-]+)', 'confidence': 0.9},
                {'pattern': r'CODE[:\s]*([A-Z0-9-]+)', 'confidence': 0.9},
                {'pattern': r'품번[:\s]*([A-Z0-9-]+)', 'confidence': 0.8},
            ],
            'product_name': [
                {'pattern': r'제품명[:\s]*(.+?)(?:\n|$)', 'confidence': 0.9},
                {'pattern': r'품명[:\s]*(.+?)(?:\n|$)', 'confidence': 0.9},
                {'pattern': r'NAME[:\s]*(.+?)(?:\n|$)', 'confidence': 0.8},
            ],
            'capacity': [
                {'pattern': r'용량[:\s]*(\d+(?:\.\d+)?(?:ml|ML|L|ℓ))', 'confidence': 0.95},
                {'pattern': r'(\d+(?:\.\d+)?(?:ml|ML|L|ℓ))', 'confidence': 0.7},  # Standalone
                {'pattern': r'CAPACITY[:\s]*(\d+(?:\.\d+)?(?:ml|ML|L))', 'confidence': 0.9},
            ],
            'neck': [
                {'pattern': r'넥[:\s]*(\d+파이)', 'confidence': 0.95},
                {'pattern': r'NECK[:\s]*(\d+파이)', 'confidence': 0.9},
                {'pattern': r'(\d+)파이', 'confidence': 0.7},  # Standalone
                {'pattern': r'Ø\s*(\d+)', 'confidence': 0.85},  # Diameter symbol
                {'pattern': r'내경\s*Ø\s*(\d+)', 'confidence': 0.9},
            ],
            'material': [
                {'pattern': r'재질[:\s]*(PET|PP|PE|PETG|HDPE|LDPE|PS|PVC)', 'confidence': 0.95},
                {'pattern': r'MATERIAL[:\s]*(PET|PP|PE|PETG|HDPE|LDPE|PS|PVC)', 'confidence': 0.9},
                {'pattern': r'\b(PET|PP|PE|PETG|HDPE|LDPE|PS|PVC)\b', 'confidence': 0.75},  # Standalone
            ],
            'moq': [
                {'pattern': r'최소주문[:\s]*(\d+[,\d]*)개', 'confidence': 0.95},
                {'pattern': r'MOQ[:\s]*(\d+[,\d]*)(?:ea|개)?', 'confidence': 0.9},
                {'pattern': r'최소\s*(\d+[,\d]*)개', 'confidence': 0.8},
                {'pattern': r'(\d+[,\d]+)개\s*단위', 'confidence': 0.85},
            ],
            'price': [
                {'pattern': r'가격[:\s]*([\d,]+)원', 'confidence': 0.95},
                {'pattern': r'단가[:\s]*([\d,]+)원', 'confidence': 0.95},
                {'pattern': r'PRICE[:\s]*([\d,]+)', 'confidence': 0.9},
                {'pattern': r'([\d,]+)원/개', 'confidence': 0.85},
            ],
            'supplier': [
                {'pattern': r'업체[:\s]*(.+?)(?:\n|$)', 'confidence': 0.9},
                {'pattern': r'제조사[:\s]*(.+?)(?:\n|$)', 'confidence': 0.9},
                {'pattern': r'SUPPLIER[:\s]*(.+?)(?:\n|$)', 'confidence': 0.85},
            ],
        }
    
    def extract_entities(self, text: str) -> Dict[str, ExtractedEntity]:
        """
        Extract all entities from text.
        
        Args:
            text: OCR text
            
        Returns:
            Dictionary of entity_type -> ExtractedEntity
        """
        entities = {}
        
        for entity_type, patterns in self.patterns.items():
            entity = self._extract_entity(text, entity_type, patterns)
            if entity:
                entities[entity_type] = entity
        
        return entities
    
    def _extract_entity(
        self,
        text: str,
        entity_type: str,
        patterns: List[Dict]
    ) -> Optional[ExtractedEntity]:
        """
        Extract single entity type using multiple patterns.
        
        Args:
            text: OCR text
            entity_type: Entity type name
            patterns: List of pattern dicts
            
        Returns:
            ExtractedEntity if found, None otherwise
        """
        for pattern_dict in patterns:
            pattern = pattern_dict['pattern']
            confidence = pattern_dict['confidence']
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # Clean up value
                value = self._clean_value(entity_type, value)
                
                logger.debug(f"Extracted {entity_type}: {value} (confidence: {confidence})")
                
                return ExtractedEntity(
                    field=entity_type,
                    value=value,
                    confidence=confidence,
                    pattern=pattern
                )
        
        return None
    
    def _clean_value(self, entity_type: str, value: str) -> str:
        """Clean extracted value based on entity type"""
        value = value.strip()
        
        if entity_type in ['moq', 'price']:
            # Remove commas from numbers
            value = value.replace(',', '')
        
        if entity_type == 'neck':
            # Normalize neck size format
            if '파이' not in value:
                value = f"{value}파이"
        
        if entity_type == 'capacity':
            # Normalize to lowercase ml
            value = value.replace('ML', 'ml').replace('L', 'L')
        
        return value
    
    def extract_from_ocr_result(self, ocr_result) -> Dict[str, ExtractedEntity]:
        """
        Extract entities from OCRResult object.
        
        Args:
            ocr_result: OCRResult from MultiEngineOCR
            
        Returns:
            Dictionary of entities
        """
        return self.extract_entities(ocr_result.full_text)
    
    def to_product_dict(self, entities: Dict[str, ExtractedEntity]) -> Dict[str, str]:
        """
        Convert extracted entities to product dictionary.
        
        Args:
            entities: Dictionary of ExtractedEntity objects
            
        Returns:
            Flat dictionary of field -> value
        """
        product = {}
        
        for entity_type, entity in entities.items():
            product[entity_type] = entity.value
            product[f"{entity_type}_confidence"] = entity.confidence
        
        return product
