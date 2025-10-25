"""
Packaging Expert Plugin for RAG Enterprise

Specialized knowledge for processing packaging and container manufacturing documents.
"""

import re
from typing import Dict, List, Any
from pathlib import Path

from plugins.base_plugin import BaseDomainPlugin


class PackagingExpertPlugin(BaseDomainPlugin):
    """
    Expert plugin for packaging and container documents
    
    Handles:
    - Material specifications
    - Container drawings and specs
    - Regulatory compliance docs
    - Quality control procedures
    - Packaging design documents
    """
    
    def _default_config_path(self) -> Path:
        return Path(__file__).parent / "config"
    
    def _initialize(self):
        """Load packaging-specific patterns and terminology"""
        self.materials_db = self.config.get('materials', {})
        self.standards_db = self.config.get('standards', {})
        self.extraction_patterns = self.config.get('patterns', {})
    
    def get_domain_name(self) -> str:
        return "packaging"
    
    def can_process(self, document: Dict[str, Any]) -> bool:
        """Check if document is packaging-related"""
        content = document.get('content', '').lower()
        filename = document.get('filename', '').lower()
        
        # Packaging indicators
        indicators = [
            'packaging', 'container', 'bottle', 'closure',
            'label', 'carton', 'box', 'pouch', 'film',
            'material spec', 'barrier properties',
            'fda', 'food contact', 'migration',
            'recyclability', 'sustainability',
            'drop test', 'burst strength', 'seal integrity'
        ]
        
        matches = sum(1 for ind in indicators if ind in content or ind in filename)
        return matches >= 2
    
    def classify_document(self, document: Dict[str, Any]) -> str:
        """Classify packaging document type"""
        content = document.get('content', '').lower()
        filename = document.get('filename', '').lower()
        
        doc_types = {
            'material_spec': ['material specification', 'material data sheet', 'resin spec'],
            'container_drawing': ['container drawing', 'bottle spec', 'technical drawing'],
            'regulatory': ['fda', 'food contact', 'compliance', 'migration', 'regulation'],
            'quality_spec': ['quality specification', 'inspection criteria', 'acceptance'],
            'testing_protocol': ['test method', 'testing protocol', 'test procedure'],
            'design_spec': ['design specification', 'packaging design', 'artwork spec']
        }
        
        scores = {}
        for doc_type, keywords in doc_types.items():
            score = sum(1 for kw in keywords if kw in content or kw in filename)
            if score > 0:
                scores[doc_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'general_packaging'
    
    def get_categories(self, doc_type: str) -> List[str]:
        """Get categories for document type"""
        category_map = {
            'material_spec': ['materials', 'specifications', 'technical'],
            'container_drawing': ['design', 'engineering', 'specifications'],
            'regulatory': ['compliance', 'regulatory', 'safety'],
            'quality_spec': ['quality', 'inspection', 'acceptance'],
            'testing_protocol': ['testing', 'quality', 'validation'],
            'design_spec': ['design', 'artwork', 'brand']
        }
        
        return category_map.get(doc_type, ['general'])
    
    def extract_terminology(self, text: str) -> List[str]:
        """Extract packaging-specific terminology"""
        terms = set()
        
        # Material types
        materials = [
            'pet', 'hdpe', 'ldpe', 'pp', 'ps', 'pvc',
            'glass', 'aluminum', 'steel', 'paper', 'cardboard',
            'multilayer', 'coextruded', 'laminated'
        ]
        
        for material in materials:
            if re.search(rf'\b{material}\b', text, re.IGNORECASE):
                terms.add(material.upper() if len(material) <= 4 else material.lower())
        
        # Packaging types
        packaging_types = [
            'bottle', 'jar', 'container', 'closure', 'cap', 'lid',
            'label', 'carton', 'box', 'pouch', 'bag', 'film',
            'tray', 'blister', 'clamshell', 'tube'
        ]
        
        for pkg_type in packaging_types:
            if re.search(rf'\b{pkg_type}\b', text, re.IGNORECASE):
                terms.add(pkg_type.lower())
        
        # Properties
        properties = [
            'barrier', 'permeability', 'opacity', 'clarity',
            'strength', 'flexibility', 'rigidity',
            'recyclable', 'biodegradable', 'compostable'
        ]
        
        for prop in properties:
            if re.search(rf'\b{prop}\w*\b', text, re.IGNORECASE):
                terms.add(prop.lower())
        
        # Standards
        standards = [
            'fda', 'cfr', 'eu 10/2011', 'reach', 'rohs',
            'astm', 'iso', 'din'
        ]
        
        for standard in standards:
            if re.search(rf'\b{standard}\b', text, re.IGNORECASE):
                terms.add(standard.upper())
        
        return list(terms)
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract packaging-specific entities"""
        entities = {
            'materials': [],
            'dimensions': [],
            'properties': [],
            'standards': [],
            'tests': []
        }
        
        # Extract materials with specifications
        material_patterns = {
            'resin': r'(pet|hdpe|ldpe|pp|ps|pvc)\s*(?:resin)?\s*-?\s*([A-Z0-9]+)?',
            'grade': r'grade\s*[=:]?\s*([A-Z0-9-]+)',
            'supplier': r'(?:supplier|manufacturer)\s*[=:]?\s*([A-Za-z\s&]+)'
        }
        
        for material_type, pattern in material_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['materials'].append({
                    'type': material_type,
                    'value': match.group(1) if len(match.groups()) >= 1 else match.group(0),
                    'context': match.group(0)
                })
        
        # Extract dimensions
        dimension_patterns = {
            'height': r'height\s*[=:]?\s*([\d.]+)\s*(mm|cm|inch|in)',
            'diameter': r'diameter\s*[=:]?\s*([\d.]+)\s*(mm|cm|inch|in)',
            'width': r'width\s*[=:]?\s*([\d.]+)\s*(mm|cm|inch|in)',
            'thickness': r'(?:thickness|gauge)\s*[=:]?\s*([\d.]+)\s*(mm|mil|micron|μm)',
            'volume': r'(?:volume|capacity)\s*[=:]?\s*([\d.]+)\s*(ml|l|oz|gal)'
        }
        
        for dim_type, pattern in dimension_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['dimensions'].append({
                    'type': dim_type,
                    'value': float(match.group(1)),
                    'unit': match.group(2),
                    'context': match.group(0)
                })
        
        # Extract barrier properties
        property_patterns = {
            'oxygen': r'(?:oxygen|o2)\s*(?:transmission|permeability)\s*[=:]?\s*([\d.]+)\s*(cc/m2/day)?',
            'moisture': r'(?:moisture|water|wvtr)\s*(?:transmission|permeability)\s*[=:]?\s*([\d.]+)\s*(g/m2/day)?',
            'strength': r'(?:tensile|burst|drop)\s*strength\s*[=:]?\s*([\d.]+)\s*(psi|mpa|kg)?'
        }
        
        for prop_type, pattern in property_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['properties'].append({
                    'type': prop_type,
                    'value': float(match.group(1)),
                    'unit': match.group(2) if len(match.groups()) > 1 else None,
                    'context': match.group(0)
                })
        
        # Extract regulatory standards
        standard_patterns = [
            r'fda\s*(?:21\s*cfr)?\s*([\d.]+)?',
            r'eu\s*(?:regulation)?\s*([\d/]+)',
            r'(?:astm|iso|din)\s*([A-Z0-9-]+)'
        ]
        
        for pattern in standard_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['standards'].append({
                    'standard': match.group(0),
                    'reference': match.group(1) if len(match.groups()) > 0 else None
                })
        
        return entities
    
    def enrich_content(self, text: str, metadata: Any) -> str:
        """Enrich content with packaging context"""
        enriched = text
        
        # Add document type context
        prefix = f"[PACKAGING DOCUMENT - {metadata.doc_type.upper()}]\n"
        prefix += f"[CATEGORIES: {', '.join(metadata.categories)}]\n\n"
        
        # Add terminology summary
        if metadata.terminology:
            prefix += f"[KEY TERMS: {', '.join(metadata.terminology[:10])}]\n\n"
        
        # Add materials summary
        materials = metadata.extracted_entities.get('materials', [])
        if materials:
            prefix += "[MATERIALS DETECTED]\n"
            for mat in materials[:5]:
                prefix += f"  - {mat['type']}: {mat['value']}\n"
            prefix += "\n"
        
        # Add dimension summary
        dimensions = metadata.extracted_entities.get('dimensions', [])
        if dimensions:
            prefix += "[DIMENSIONS]\n"
            for dim in dimensions[:5]:
                prefix += f"  - {dim['type']}: {dim['value']} {dim['unit']}\n"
            prefix += "\n"
        
        enriched = prefix + enriched
        
        return enriched
