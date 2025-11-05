"""
Manufacturing Expert Skill - Executable Implementation

Integrates with existing manufacturing_expert plugin
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the actual plugin
from plugins.manufacturing_expert import ManufacturingExpertPlugin

# Global plugin instance
_plugin = None

def get_plugin():
    """Lazy load plugin instance"""
    global _plugin
    if _plugin is None:
        _plugin = ManufacturingExpertPlugin()
    return _plugin


# Skill metadata
SKILL_INFO = {
    'name': 'manufacturing-expert',
    'version': '1.0.0',
    'description': 'Expert knowledge for manufacturing and production documents',
    'domain': 'manufacturing',
    'commands': ['process', 'classify', 'extract', 'help']
}


def execute(command: str, *args) -> Dict[str, Any]:
    """
    Execute skill command

    Commands:
        process <document>  - Process manufacturing document
        classify <document> - Classify document type
        extract <document>  - Extract terminology and metrics
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
            "domain": "manufacturing"
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
            "domain": "manufacturing"
        }

    elif command == 'help':
        return {
            "skill": "manufacturing-expert",
            "commands": {
                "process": "Process manufacturing document (full analysis)",
                "classify": "Classify document type",
                "extract": "Extract terminology and metrics",
                "help": "Show this help message"
            },
            "usage": "skill.execute('command', document)",
            "examples": [
                "skill.execute('process', {'content': 'SOP-001...', 'filename': 'sop.pdf'})",
                "skill.execute('classify', {'content': 'FMEA analysis...'})",
                "skill.execute('extract', {'content': 'Cpk: 1.33, OEE: 85%'})"
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
Manufacturing Expert Skill v{SKILL_INFO['version']}

DESCRIPTION:
    {SKILL_INFO['description']}

COMMANDS:
    process <document>  - Full document processing and enrichment
    classify <document> - Classify manufacturing document type
    extract <document>  - Extract terminology and quality metrics
    help                - Show this help message

USAGE:
    from .claude.skills.manufacturing_expert import skill

    # Process document
    result = skill.execute('process', document)

    # Classify only
    result = skill.execute('classify', document)

    # Extract terminology
    result = skill.execute('extract', document)

DOCUMENT TYPES:
    - sop: Standard Operating Procedures
    - equipment_spec: Equipment Specifications
    - control_plan: Process Control Plans, FMEA
    - defect_analysis: Root Cause Analysis, 8D Reports
    - maintenance: Maintenance Procedures
    - batch_record: Production Records
    - deviation: Deviation Reports, NCRs

QUALITY METRICS:
    Cpk, Cp, OEE, PPM, MTBF, MTTR, Yield, FPY

STANDARDS:
    ISO 9001, ISO 13485, ISO 14001, IATF 16949
    FDA 21 CFR Part 11, Part 820, GMP
"""


# Quick access functions
def process_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Process manufacturing document"""
    return execute('process', document)


def classify_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Classify manufacturing document"""
    return execute('classify', document)


def extract_terminology(document: Dict[str, Any]) -> Dict[str, Any]:
    """Extract terminology from document"""
    return execute('extract', document)


if __name__ == "__main__":
    # Self-test
    print("Manufacturing Expert Skill - Self Test")
    print("=" * 50)

    test_doc = {
        "content": "SOP-001: Injection Molding Process. Cpk: 1.33, OEE: 85%. ISO 9001:2015 compliant.",
        "filename": "sop-injection-molding.pdf"
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
