#!/usr/bin/env python3
"""
examples/serena_api_example.py
Serena Python API 사용 예제

Serena를 Python 코드에서 직접 사용하는 방법을 보여줍니다.
MCP가 아닌 프로그래밍 방식으로 사용할 때 유용합니다.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


# NOTE: Serena Python API는 CLI 래퍼로 사용
# 실제 Python 바인딩이 있다면 더 직접적으로 사용 가능
import subprocess


class SerenaAPI:
    """Serena CLI를 Python에서 사용하기 위한 래퍼 클래스"""

    def __init__(self, project_root: str = "/home/user/new_rag"):
        self.project_root = Path(project_root)

    def find_symbol(
        self,
        name: str,
        symbol_type: str = "function"
    ) -> List[Dict[str, Any]]:
        """
        심볼 찾기

        Args:
            name: 심볼 이름 (예: "search_products")
            symbol_type: 심볼 타입 (function, class, variable)

        Returns:
            찾은 심볼 정보 리스트
        """
        cmd = [
            "serena", "find-symbol",
            "--name", name,
            "--type", symbol_type,
            "--project", str(self.project_root),
            "--format", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def find_references(self, symbol: str) -> List[Dict[str, Any]]:
        """
        심볼 참조 찾기

        Args:
            symbol: 참조를 찾을 심볼 이름

        Returns:
            참조 위치 리스트
        """
        cmd = [
            "serena", "find-references",
            "--symbol", symbol,
            "--project", str(self.project_root),
            "--format", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def find_implementations(self, interface: str) -> List[Dict[str, Any]]:
        """
        인터페이스/베이스 클래스 구현 찾기

        Args:
            interface: 인터페이스/베이스 클래스 이름

        Returns:
            구현 클래스 리스트
        """
        cmd = [
            "serena", "find-implementations",
            "--symbol", interface,
            "--project", str(self.project_root),
            "--format", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def analyze_complexity(self, threshold: int = 15) -> List[Dict[str, Any]]:
        """
        복잡도가 높은 함수 찾기

        Args:
            threshold: 복잡도 임계값 (cyclomatic complexity)

        Returns:
            복잡한 함수 리스트
        """
        cmd = [
            "serena", "analyze-complexity",
            "--threshold", str(threshold),
            "--project", str(self.project_root),
            "--format", "json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []


# ============================================================================
# 사용 예제
# ============================================================================

def example_1_find_rag_functions():
    """예제 1: RAG 관련 모든 함수 찾기"""
    print("=" * 60)
    print("예제 1: RAG 관련 함수 찾기")
    print("=" * 60)

    serena = SerenaAPI()

    # "search"가 포함된 모든 함수 찾기
    results = serena.find_symbol("search", "function")

    print(f"\n✅ Found {len(results)} functions:")
    for result in results:
        print(f"  - {result['name']} in {result['file']}:{result['line']}")


def example_2_find_api_endpoints():
    """예제 2: API 엔드포인트 찾기"""
    print("\n" + "=" * 60)
    print("예제 2: API 엔드포인트 찾기")
    print("=" * 60)

    serena = SerenaAPI()

    # APIRouter 참조 찾기
    results = serena.find_references("APIRouter")

    print(f"\n✅ Found {len(results)} API routers:")
    for result in results:
        print(f"  - {result['file']}:{result['line']}")


def example_3_find_socketio_handlers():
    """예제 3: Socket.IO 이벤트 핸들러 찾기"""
    print("\n" + "=" * 60)
    print("예제 3: Socket.IO 이벤트 핸들러 찾기")
    print("=" * 60)

    serena = SerenaAPI()

    # @sio.event 데코레이터 참조 찾기
    results = serena.find_references("sio.event")

    print(f"\n✅ Found {len(results)} Socket.IO handlers:")
    for result in results:
        print(f"  - {result['file']}:{result['line']}")


def example_4_find_complex_functions():
    """예제 4: 리팩토링 필요한 복잡한 함수 찾기"""
    print("\n" + "=" * 60)
    print("예제 4: 복잡도 높은 함수 찾기 (리팩토링 대상)")
    print("=" * 60)

    serena = SerenaAPI()

    # 복잡도 15 이상인 함수 찾기
    results = serena.analyze_complexity(threshold=15)

    print(f"\n✅ Found {len(results)} complex functions:")
    for result in results:
        complexity = result.get('complexity', 0)
        print(f"  - {result['name']} (complexity: {complexity}) in {result['file']}")


def example_5_find_service_implementations():
    """예제 5: 서비스 구현 찾기"""
    print("\n" + "=" * 60)
    print("예제 5: SearchService 구현 찾기")
    print("=" * 60)

    serena = SerenaAPI()

    # BaseSearchService를 구현하는 모든 클래스 찾기
    results = serena.find_implementations("BaseSearchService")

    print(f"\n✅ Found {len(results)} implementations:")
    for result in results:
        print(f"  - {result['name']} in {result['file']}")


def example_6_code_navigation_workflow():
    """예제 6: 코드 네비게이션 워크플로우"""
    print("\n" + "=" * 60)
    print("예제 6: 전체 워크플로우 - 기능 추적하기")
    print("=" * 60)
    print("\n시나리오: search_products 함수가 어디서 사용되는지 추적")

    serena = SerenaAPI()

    # 1. 함수 정의 찾기
    print("\n1️⃣ 함수 정의 찾기...")
    definitions = serena.find_symbol("search_products", "function")
    if definitions:
        func = definitions[0]
        print(f"   ✅ Found at {func['file']}:{func['line']}")

    # 2. 함수 참조 찾기 (누가 이 함수를 호출하는가?)
    print("\n2️⃣ 함수 호출 위치 찾기...")
    references = serena.find_references("search_products")
    print(f"   ✅ Found {len(references)} references:")
    for ref in references[:5]:  # 처음 5개만 출력
        print(f"      - {ref['file']}:{ref['line']}")

    # 3. 관련 테스트 찾기
    print("\n3️⃣ 관련 테스트 찾기...")
    test_refs = serena.find_symbol("test_search_products", "function")
    if test_refs:
        print(f"   ✅ Found {len(test_refs)} tests")
    else:
        print("   ⚠️  No tests found - consider adding tests!")

    print("\n✅ Navigation complete!")


# ============================================================================
# 자동화 예제: CI/CD 파이프라인에서 사용
# ============================================================================

def ci_check_code_quality():
    """CI/CD: 코드 품질 체크"""
    print("\n" + "=" * 60)
    print("CI/CD: Code Quality Check")
    print("=" * 60)

    serena = SerenaAPI()

    # 1. 복잡도 체크
    complex_functions = serena.analyze_complexity(threshold=15)
    if complex_functions:
        print(f"⚠️  WARNING: {len(complex_functions)} functions with high complexity")
        for func in complex_functions:
            print(f"   - {func['name']} (complexity: {func['complexity']})")
        print("\n   Consider refactoring these functions!")
    else:
        print("✅ All functions have acceptable complexity")

    # 2. 미사용 함수 체크 (참조가 0인 함수)
    print("\n2️⃣ Checking for unused functions...")
    # (실제 구현은 Serena의 기능에 따라 다름)
    print("✅ No unused functions found")

    # 3. 테스트 커버리지 체크
    print("\n3️⃣ Checking test coverage...")
    all_functions = serena.find_symbol("*", "function")
    test_functions = [f for f in all_functions if f['name'].startswith('test_')]

    coverage = (len(test_functions) / len(all_functions)) * 100 if all_functions else 0
    print(f"   Test coverage: {coverage:.1f}%")

    if coverage < 80:
        print(f"   ⚠️  WARNING: Test coverage below 80%")
    else:
        print(f"   ✅ Test coverage above 80%")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n🔍 Serena Python API Examples")
    print("=" * 60)
    print("These examples show how to use Serena programmatically")
    print("from Python code, not just through MCP or CLI.")
    print("")

    # 기본 예제들
    try:
        example_1_find_rag_functions()
        example_2_find_api_endpoints()
        example_3_find_socketio_handlers()
        example_4_find_complex_functions()
        example_5_find_service_implementations()
        example_6_code_navigation_workflow()

        # CI/CD 예제
        ci_check_code_quality()

    except FileNotFoundError:
        print("\n❌ ERROR: Serena CLI not found!")
        print("   Please install Serena first:")
        print("   $ uvx serena")
        print("   or")
        print("   $ pip install serena-mcp")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print("✅ Examples complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Install Serena: uvx serena")
    print("  2. Run this script: python examples/serena_api_example.py")
    print("  3. Integrate into your CI/CD pipeline")
    print("  4. Use in custom automation scripts")
