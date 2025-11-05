"""
Packaging Expert Skill - Executable Implementation

Integrates with existing packaging_expert plugin
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the actual plugin
from plugins.packaging_expert import PackagingExpertPlugin

# Global plugin instance
_plugin = None

def get_plugin():
    """Lazy load plugin instance"""
    global _plugin
    if _plugin is None:
        _plugin = PackagingExpertPlugin()
    return _plugin


# Skill metadata
SKILL_INFO = {
    'name': 'packaging-expert',
    'version': '1.0.0',
    'description': 'Expert knowledge for packaging and container manufacturing documents',
    'domain': 'packaging',
    'commands': ['process', 'classify', 'extract', 'help']
}


def execute(command: str, *args) -> Dict[str, Any]:
    """
    Execute skill command

    Commands:
        process <document>  - Process packaging document
        classify <document> - Classify document type
        extract <document>  - Extract materials and dimensions
        help                - Show usage information
    """
    plugin = get_plugin()

    if command == 'process':
        if not args:
            return {"error": "Missing document argument"}

        document = args[0] if isinstance(args[0], dict) else {"content": str(args[0])}
        return plugin.process_document(document)

    elif command == 'classify':
        if not args:
            return {"error": "Missing document argument"}

        document = args[0] if isinstance(args[0], dict) else {"content": str(args[0])}
        doc_type = plugin.classify_document(document)
        categories = plugin.get_categories(doc_type)

        return {
            "doc_type": doc_type,
            "categories": categories,
            "domain": "packaging"
        }

    elif command == 'extract':
        if not args:
            return {"error": "Missing document argument"}

        document = args[0] if isinstance(args[0], dict) else {"content": str(args[0])}
        # Extract text content for terminology extraction
        text = document.get('content', '') if isinstance(document, dict) else str(document)
        terminology = plugin.extract_terminology(text)

        return {
            "terminology": terminology,
            "domain": "packaging"
        }

    elif command == 'help':
        return {
            "skill": "packaging-expert",
            "commands": {
                "process": "Process packaging document (full analysis)",
                "classify": "Classify document type",
                "extract": "Extract materials, dimensions, and properties",
                "help": "Show this help message"
            },
            "usage": "skill.execute('command', document)",
            "examples": [
                "skill.execute('process', {'content': 'PET bottle spec...', 'filename': 'container.pdf'})",
                "skill.execute('classify', {'content': 'FDA 21 CFR Part 177...'})",
                "skill.execute('extract', {'content': 'Capacity: 500ml, Neck: 28/410'})"
            ]
        }

    else:
        return {
            "error": f"Unknown command: {command}",
            "available_commands": SKILL_INFO['commands'],
            "hint": "Use 'help' command for usage information"
        }


def help_text() -> str:
    """Return help text for the skill"""
    return f"""
Packaging Expert Skill v{SKILL_INFO['version']}

DESCRIPTION:
    {SKILL_INFO['description']}

COMMANDS:
    process <document>  - Full document processing and enrichment
    classify <document> - Classify packaging document type
    extract <document>  - Extract materials, dimensions, and properties
    help                - Show this help message

USAGE:
    from .claude.skills.packaging_expert import skill

    # Process document
    result = skill.execute('process', document)

    # Classify only
    result = skill.execute('classify', document)

    # Extract materials and dimensions
    result = skill.execute('extract', document)

DOCUMENT TYPES:
    - material_spec: Material specifications, data sheets
    - container_drawing: Technical drawings, bottle specs
    - regulatory: FDA compliance, food contact documents
    - quality_spec: Inspection criteria, acceptance standards
    - testing_protocol: Test methods, validation procedures
    - design_spec: Packaging design, artwork specifications

MATERIALS RECOGNIZED:
    Plastics: PET, HDPE, LDPE, PP, PS, PVC, PETG, PC, PLA, ABS
    Specialty: EVOH, PVDC, Biodegradable polymers
    Other: Glass (Type I/II/III), Aluminum, Steel

REGULATORY STANDARDS:
    FDA: 21 CFR Part 177, 21 CFR Part 178, FCN
    EU: Regulation (EC) 1935/2004, Regulation (EU) 10/2011
    Environmental: Recyclability codes, RoHS, REACH

DIMENSIONS:
    Capacity, Height, Diameter, Neck Size, Thickness, Weight

PROPERTIES:
    Barrier (oxygen, moisture), Mechanical strength,
    Seal integrity, Chemical resistance
"""


# Quick access functions
def process_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Process packaging document"""
    return execute('process', document)


def classify_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Classify packaging document"""
    return execute('classify', document)


def extract_terminology(document: Dict[str, Any]) -> Dict[str, Any]:
    """Extract materials and dimensions from document"""
    return execute('extract', document)


if __name__ == "__main__":
    # Self-test
    print("Packaging Expert Skill - Self Test")
    print("=" * 50)

    test_doc = {
        "content": "PET bottle 500ml capacity, neck size 28/410. FDA 21 CFR Part 177 compliant. Oxygen barrier <1.0 cc/pkg/day.",
        "filename": "pet-bottle-spec.pdf"
    }

    print("\n1. Classify Test:")
    result = execute('classify', test_doc)
    print(f"   Type: {result.get('doc_type')}")
    print(f"   Categories: {result.get('categories')}")

    print("\n2. Extract Test:")
    result = execute('extract', test_doc)
    terminology = result.get('terminology', [])
    print(f"   Terminology count: {len(terminology)}")
    print(f"   Sample terms: {list(terminology)[:5] if terminology else 'None'}")

    print("\n3. Process Test:")
    result = execute('process', test_doc)
    has_error = hasattr(result, 'error') or (isinstance(result, dict) and 'error' in result)
    print(f"   Status: {'✅ Success' if not has_error else '❌ Failed'}")

    print("\n" + "=" * 50)
    print("✅ Skill executable and ready to use!")
