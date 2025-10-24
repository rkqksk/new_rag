"""
Manufacturing Expert Plugin for RAG Enterprise

Specialized knowledge for processing manufacturing and production engineering documents.
"""

import re
from typing import Dict, List, Any
from pathlib import Path

from base_plugin import BaseDomainPlugin


class ManufacturingExpertPlugin(BaseDomainPlugin):
    """
    Expert plugin for manufacturing and production documents
    
    Handles:
    - SOPs and work instructions
    - Equipment specifications
    - Process control plans
    - Defect analysis reports
    - Maintenance procedures
    """
    
    def _default_config_path(self) -> Path:
        return Path(__file__).parent / "config"
    
    def _initialize(self):
        """Load manufacturing-specific patterns and terminology"""
        # Load patterns from config
        self.doc_patterns = self.config.get('document_types', {})
        self.terminology_db = self.config.get('terminology', {})
        self.extraction_patterns = self.config.get('patterns', {})
    
    def get_domain_name(self) -> str:
        return "manufacturing"
    
    def can_process(self, document: Dict[str, Any]) -> bool:
        """Check if document is manufacturing-related"""
        content = document.get('content', '').lower()
        filename = document.get('filename', '').lower()
        
        # Manufacturing indicators
        indicators = [
            'sop', 'standard operating procedure',
            'work instruction', 'process flow',
            'equipment', 'machine', 'production',
            'defect', 'fmea', 'quality control',
            'maintenance', 'oee', 'cpk', 'ppm',
            'batch record', 'deviation',
            'iso 9001', 'iso 13485', 'gmp'
        ]
        
        # Check content and filename
        matches = sum(1 for ind in indicators if ind in content or ind in filename)
        
        return matches >= 2
    
    def classify_document(self, document: Dict[str, Any]) -> str:
        """Classify manufacturing document type"""
        content = document.get('content', '').lower()
        filename = document.get('filename', '').lower()
        
        # Document type patterns
        doc_types = {
            'sop': ['sop', 'standard operating procedure', 'work instruction'],
            'equipment_spec': ['equipment specification', 'machine manual', 'technical data sheet'],
            'control_plan': ['control plan', 'fmea', 'process fmea'],
            'defect_analysis': ['defect analysis', 'root cause', 'rca', '8d report'],
            'maintenance': ['maintenance procedure', 'pm schedule', 'preventive maintenance'],
            'batch_record': ['batch record', 'production record', 'lot record'],
            'deviation': ['deviation report', 'non-conformance', 'ncr']
        }
        
        # Score each type
        scores = {}
        for doc_type, keywords in doc_types.items():
            score = sum(1 for kw in keywords if kw in content or kw in filename)
            if score > 0:
                scores[doc_type] = score
        
        # Return highest scoring type
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'general_manufacturing'
    
    def get_categories(self, doc_type: str) -> List[str]:
        """Get categories for document type"""
        category_map = {
            'sop': ['process', 'quality', 'compliance'],
            'equipment_spec': ['equipment', 'technical'],
            'control_plan': ['quality', 'process', 'risk'],
            'defect_analysis': ['quality', 'analysis', 'improvement'],
            'maintenance': ['equipment', 'maintenance', 'reliability'],
            'batch_record': ['production', 'traceability', 'compliance'],
            'deviation': ['quality', 'compliance', 'investigation']
        }
        
        return category_map.get(doc_type, ['general'])
    
    def extract_terminology(self, text: str) -> List[str]:
        """Extract manufacturing-specific terminology"""
        terms = set()
        
        # Quality metrics patterns
        quality_patterns = [
            r'\b(cpk|ppk|cp|pp)\s*[=:><=]\s*[\d.]+',
            r'\b(ppm|dpmo|dpu)\s*[=:]\s*[\d.]+',
            r'\b(oee|availability|performance|quality)\s*[=:]\s*[\d.]+%?',
            r'\b(first\s+pass\s+yield|fpy)\s*[=:]\s*[\d.]+%?'
        ]
        
        for pattern in quality_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                terms.add(match.group(0))
        
        # Process operations
        process_terms = [
            'setup', 'changeover', 'validation', 'cleaning',
            'calibration', 'qualification', 'verification',
            'iq', 'oq', 'pq', 'commissioning'
        ]
        
        for term in process_terms:
            if re.search(rf'\b{term}\b', text, re.IGNORECASE):
                terms.add(term.lower())
        
        # Equipment terms
        equipment_terms = [
            'actuator', 'sensor', 'plc', 'hmi', 'scada',
            'controller', 'interlock', 'servo', 'motor'
        ]
        
        for term in equipment_terms:
            if re.search(rf'\b{term}\b', text, re.IGNORECASE):
                terms.add(term.lower())
        
        # Standards
        standards = [
            'iso 9001', 'iso 13485', 'iso 14001',
            'gmp', 'fda 21 cfr part 11',
            'six sigma', 'lean manufacturing'
        ]
        
        for standard in standards:
            if re.search(rf'\b{standard}\b', text, re.IGNORECASE):
                terms.add(standard.lower())
        
        return list(terms)
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract manufacturing-specific entities"""
        entities = {
            'parameters': [],
            'equipment': [],
            'quality_metrics': [],
            'standards': [],
            'processes': []
        }
        
        # Extract process parameters (temp, pressure, time, etc)
        param_patterns = {
            'temperature': r'(?:temp(?:erature)?|°[CF])\s*[=:]\s*([\d.-]+)\s*°?([CF])?',
            'pressure': r'pressure\s*[=:]\s*([\d.-]+)\s*(psi|bar|kpa|mpa)?',
            'time': r'(?:time|duration)\s*[=:]\s*([\d.-]+)\s*(min|hr|sec|hours?|minutes?)?',
            'speed': r'speed\s*[=:]\s*([\d.-]+)\s*(rpm|m/s|ft/min)?',
            'flow_rate': r'flow\s*(?:rate)?\s*[=:]\s*([\d.-]+)\s*(l/min|gpm|cfm)?'
        }
        
        for param_type, pattern in param_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['parameters'].append({
                    'type': param_type,
                    'value': match.group(1),
                    'unit': match.group(2) if len(match.groups()) > 1 else None,
                    'context': match.group(0)
                })
        
        # Extract quality metrics
        quality_patterns = {
            'cpk': r'cpk\s*[=:]\s*([\d.]+)',
            'oee': r'oee\s*[=:]\s*([\d.]+)%?',
            'yield': r'(?:yield|fpy)\s*[=:]\s*([\d.]+)%?',
            'defect_rate': r'(?:defect\s*rate|ppm)\s*[=:]\s*([\d.]+)'
        }
        
        for metric_type, pattern in quality_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities['quality_metrics'].append({
                    'type': metric_type,
                    'value': float(match.group(1)),
                    'context': match.group(0)
                })
        
        # Extract equipment names (simplified)
        equipment_keywords = ['machine', 'equipment', 'unit', 'system', 'line']
        for keyword in equipment_keywords:
            pattern = rf'(?:^|\n)\s*([A-Z][A-Za-z0-9\s-]+{keyword}[A-Za-z0-9\s-]*)'
            matches = re.finditer(pattern, text)
            for match in matches:
                entities['equipment'].append(match.group(1).strip())
        
        return entities
    
    def enrich_content(self, text: str, metadata: Any) -> str:
        """Enrich content with manufacturing context"""
        enriched = text
        
        # Add document type context at the beginning
        prefix = f"[MANUFACTURING DOCUMENT - {metadata.doc_type.upper()}]\n"
        prefix += f"[CATEGORIES: {', '.join(metadata.categories)}]\n\n"
        
        # Add extracted terminology summary
        if metadata.terminology:
            prefix += f"[KEY TERMS: {', '.join(metadata.terminology[:10])}]\n\n"
        
        # Add parameter summary
        if metadata.extracted_entities.get('parameters'):
            prefix += "[PROCESS PARAMETERS DETECTED]\n"
            for param in metadata.extracted_entities['parameters'][:5]:
                prefix += f"  - {param['type']}: {param['value']} {param.get('unit', '')}\n"
            prefix += "\n"
        
        enriched = prefix + enriched
        
        return enriched
