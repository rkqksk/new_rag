#!/usr/bin/env python3
"""
Auto-generate pytest tests from Python code
"""
import argparse
import ast
from pathlib import Path
from typing import List, Dict

TEST_TEMPLATE = """import pytest
from {module_path} import {class_name}

class Test{class_name}:
    @pytest.fixture
    def {fixture_name}(self):
        return {class_name}()

{test_methods}
"""

METHOD_TEMPLATE = """    def test_{method_name}(self, {fixture_name}):
        \"\"\"Test {method_name}\"\"\"
        # TODO: Add test implementation
        result = {fixture_name}.{method_name}()
        assert result is not None
"""

def analyze_class(source_code: str) -> Dict:
    """
    Extract class and methods from Python source
    """
    tree = ast.parse(source_code)

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if not item.name.startswith('_'):  # Skip private
                        methods.append({
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args if arg.arg != 'self']
                        })

            classes.append({
                'name': node.name,
                'methods': methods
            })

    return classes

def generate_test_file(source_file: Path, output_file: Path):
    """
    Generate pytest test file from source
    """
    source_code = source_file.read_text()
    classes = analyze_class(source_code)

    if not classes:
        print(f"No classes found in {source_file}")
        return

    # Get module path
    module_path = str(source_file).replace('/', '.').replace('.py', '')
    if module_path.startswith('.'):
        module_path = module_path[1:]

    for cls in classes:
        class_name = cls['name']
        fixture_name = class_name.lower().replace('service', '').replace('manager', '') or 'instance'

        # Generate test methods
        test_methods = []
        for method in cls['methods']:
            test_methods.append(METHOD_TEMPLATE.format(
                method_name=method['name'],
                fixture_name=fixture_name
            ))

        # Generate test file
        test_code = TEST_TEMPLATE.format(
            module_path=module_path,
            class_name=class_name,
            fixture_name=fixture_name,
            test_methods='\n'.join(test_methods)
        )

        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(test_code)

        print(f"✅ Generated: {output_file}")
        print(f"   Class: {class_name}")
        print(f"   Methods: {len(cls['methods'])}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate pytest tests")
    parser.add_argument('--source', required=True, help='Source Python file')
    parser.add_argument('--output', help='Output test file')

    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"Error: {source} not found")
        exit(1)

    # Generate output path
    if args.output:
        output = Path(args.output)
    else:
        # tests/unit/test_<filename>.py
        output = Path("tests/unit") / f"test_{source.name}"

    generate_test_file(source, output)
    print()
    print(f"Run tests with: pytest {output} -v")
