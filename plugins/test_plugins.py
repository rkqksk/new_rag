"""
Plugin Integration and Test Examples for RAG Enterprise

This module demonstrates how to integrate domain expert plugins
into your RAG pipeline.
"""

from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from manufacturing_expert import ManufacturingExpertPlugin
from packaging_expert import PackagingExpertPlugin
from base_plugin import BaseDomainPlugin, ProcessingResult


class PluginManager:
    """
    Manages multiple domain expert plugins for document processing
    """
    
    def __init__(self):
        self.plugins: List[BaseDomainPlugin] = []
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all available plugins"""
        # Load manufacturing plugin
        try:
            mfg_plugin = ManufacturingExpertPlugin()
            self.plugins.append(mfg_plugin)
            print(f"✓ Loaded: Manufacturing Expert Plugin")
        except Exception as e:
            print(f"✗ Failed to load Manufacturing Plugin: {e}")
        
        # Load packaging plugin
        try:
            pkg_plugin = PackagingExpertPlugin()
            self.plugins.append(pkg_plugin)
            print(f"✓ Loaded: Packaging Expert Plugin")
        except Exception as e:
            print(f"✗ Failed to load Packaging Plugin: {e}")
    
    def process_document(self, document: Dict[str, Any]) -> ProcessingResult:
        """
        Process document with appropriate plugin
        
        Args:
            document: Document dict with 'content', 'filename', 'metadata'
            
        Returns:
            ProcessingResult from the best matching plugin
        """
        # Find best plugin
        best_plugin = None
        best_score = 0.0
        
        for plugin in self.plugins:
            if plugin.can_process(document):
                # Quick confidence check
                content = document.get('content', '')
                terminology = plugin.extract_terminology(content[:1000])  # Sample
                entities = plugin.extract_entities(content[:1000])
                score = plugin.calculate_confidence(document, terminology, entities)
                
                if score > best_score:
                    best_score = score
                    best_plugin = plugin
        
        if best_plugin:
            print(f"Processing with: {best_plugin.get_domain_name()} (confidence: {best_score:.2f})")
            return best_plugin.process_document(document)
        else:
            # No suitable plugin found
            return ProcessingResult(
                success=False,
                metadata=None,
                chunks=[],
                enriched_content="",
                errors=["No suitable plugin found for this document"]
            )
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """Get information about all loaded plugins"""
        return [
            {
                'domain': plugin.get_domain_name(),
                'class': plugin.__class__.__name__,
                'config_loaded': bool(plugin.config)
            }
            for plugin in self.plugins
        ]


# ========== Test Examples ==========

def test_manufacturing_sop():
    """Test with a manufacturing SOP document"""
    print("\n" + "="*60)
    print("TEST 1: Manufacturing SOP")
    print("="*60)
    
    document = {
        'filename': 'SOP-MFG-001_Equipment_Calibration.pdf',
        'content': """
        Standard Operating Procedure
        SOP-MFG-001
        Equipment Calibration Procedure
        
        1. Purpose
        This SOP describes the procedure for calibrating production equipment.
        
        2. Scope
        Applies to all manufacturing equipment requiring periodic calibration.
        
        3. Procedure
        3.1 Temperature Verification
        - Set temperature to 150°C ± 2°C
        - Allow 30 minutes stabilization
        - Verify with calibrated thermometer
        - Record actual temperature
        
        3.2 Pressure Check
        - Set pressure to 45 psi
        - Verify with calibrated gauge
        - Acceptance criteria: 43-47 psi
        
        4. Quality Metrics
        - Process Cpk must be ≥ 1.33
        - First pass yield target: 98%
        - OEE target: 85%
        
        5. References
        - ISO 9001:2015
        - FDA 21 CFR Part 11
        """,
        'metadata': {}
    }
    
    manager = PluginManager()
    result = manager.process_document(document)
    
    if result.success:
        print(f"\n✓ Success!")
        print(f"Document Type: {result.metadata.doc_type}")
        print(f"Domain: {result.metadata.domain}")
        print(f"Categories: {', '.join(result.metadata.categories)}")
        print(f"Confidence: {result.metadata.confidence:.2f}")
        print(f"\nTerminology extracted: {len(result.metadata.terminology)} terms")
        print(f"  Sample: {', '.join(result.metadata.terminology[:5])}")
        print(f"\nParameters extracted: {len(result.metadata.extracted_entities.get('parameters', []))}")
        for param in result.metadata.extracted_entities.get('parameters', [])[:3]:
            print(f"  - {param['type']}: {param['value']} {param.get('unit', '')}")
        print(f"\nChunks created: {len(result.chunks)}")
    else:
        print(f"\n✗ Failed: {result.errors}")


def test_packaging_spec():
    """Test with a packaging specification document"""
    print("\n" + "="*60)
    print("TEST 2: Packaging Material Specification")
    print("="*60)
    
    document = {
        'filename': 'PKG-SPEC-100ml-PET-Bottle.pdf',
        'content': """
        Material Specification
        100ml PET Bottle
        
        1. Material
        Resin: PET (Polyethylene Terephthalate)
        Grade: IV 0.80
        Supplier: ABC Polymers Inc.
        FDA Compliance: 21 CFR 177.1630
        
        2. Dimensions
        Height: 120 mm
        Diameter: 45 mm
        Wall thickness: 0.5 mm
        Volume: 100 ml
        Weight: 18 g
        
        3. Barrier Properties
        Oxygen transmission rate: 0.5 cc/m²/day
        Water vapor transmission: 2.0 g/m²/day
        
        4. Mechanical Properties
        Tensile strength: 55 MPa
        Elongation at break: 300%
        Drop test: Pass from 1.2 m height
        
        5. Optical Properties
        Clarity: Clear/Transparent
        Haze: < 5%
        
        6. Regulatory Compliance
        - FDA 21 CFR 177.1630
        - EU Regulation 10/2011
        - REACH compliant
        - RoHS compliant
        
        7. Sustainability
        - 25% PCR content
        - Recyclable (Resin Code 1)
        - BPA free
        """,
        'metadata': {}
    }
    
    manager = PluginManager()
    result = manager.process_document(document)
    
    if result.success:
        print(f"\n✓ Success!")
        print(f"Document Type: {result.metadata.doc_type}")
        print(f"Domain: {result.metadata.domain}")
        print(f"Categories: {', '.join(result.metadata.categories)}")
        print(f"Confidence: {result.metadata.confidence:.2f}")
        print(f"\nTerminology extracted: {len(result.metadata.terminology)} terms")
        print(f"  Sample: {', '.join(result.metadata.terminology[:8])}")
        print(f"\nMaterials extracted: {len(result.metadata.extracted_entities.get('materials', []))}")
        for mat in result.metadata.extracted_entities.get('materials', [])[:3]:
            print(f"  - {mat['type']}: {mat['value']}")
        print(f"\nDimensions extracted: {len(result.metadata.extracted_entities.get('dimensions', []))}")
        for dim in result.metadata.extracted_entities.get('dimensions', [])[:5]:
            print(f"  - {dim['type']}: {dim['value']} {dim['unit']}")
        print(f"\nChunks created: {len(result.chunks)}")
    else:
        print(f"\n✗ Failed: {result.errors}")


def test_plugin_manager():
    """Test the plugin manager"""
    print("\n" + "="*60)
    print("TEST 3: Plugin Manager Info")
    print("="*60)
    
    manager = PluginManager()
    info = manager.get_plugin_info()
    
    print(f"\nLoaded {len(info)} plugins:")
    for plugin_info in info:
        print(f"\n  Domain: {plugin_info['domain']}")
        print(f"  Class: {plugin_info['class']}")
        print(f"  Config loaded: {plugin_info['config_loaded']}")


# ========== RAG Integration Example ==========

def integrate_with_rag_pipeline(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example of how to integrate plugins into RAG pipeline
    
    This function would be called from your RAG orchestrator
    during document ingestion.
    """
    manager = PluginManager()
    result = manager.process_document(document)
    
    if result.success:
        # Return enriched content and metadata for vector storage
        return {
            'content': result.enriched_content,
            'chunks': result.chunks,
            'metadata': {
                'doc_type': result.metadata.doc_type,
                'domain': result.metadata.domain,
                'categories': result.metadata.categories,
                'terminology': result.metadata.terminology,
                'entities': result.metadata.extracted_entities,
                'confidence': result.metadata.confidence
            }
        }
    else:
        # Return original content if no plugin could process
        return {
            'content': document.get('content', ''),
            'chunks': [],
            'metadata': {},
            'errors': result.errors
        }


if __name__ == '__main__':
    print("\n" + "="*60)
    print("RAG Enterprise Domain Expert Plugins Test Suite")
    print("="*60)
    
    # Run tests
    test_plugin_manager()
    test_manufacturing_sop()
    test_packaging_spec()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
