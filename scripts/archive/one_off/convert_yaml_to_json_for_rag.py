"""
YAML 설정을 JSON으로 변환 - RAG 데이터 생성

목적:
1. plugins/의 YAML 설정을 JSON으로 변환
2. data/ 폴더에 RAG용 데이터로 저장
3. 두 군데 저장 전략 검증 (plugins + data)

이유:
- plugins/: 코드 실행용 (Python이 YAML 로드)
- data/: RAG 검색용 (벡터 DB 인덱싱용)
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any
import sys

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def convert_yaml_to_json(yaml_file: Path, output_dir: Path) -> Dict[str, Any]:
    """YAML 파일을 JSON으로 변환"""

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # JSON 파일 이름 생성
    json_filename = yaml_file.stem + '.json'
    json_path = output_dir / json_filename

    # JSON 저장
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Converted: {yaml_file.name} → {json_path}")

    return data


def create_rag_metadata(plugin_name: str, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """RAG 검색을 위한 메타데이터 생성"""

    metadata = {
        "source": f"plugins/{plugin_name}/config",
        "plugin": plugin_name,
        "data_type": data_type,
        "format": "json",
        "created_from": "yaml_config",
        "purpose": "rag_indexing",
        "searchable": True,
        "domain": plugin_name.replace('_expert', ''),
        "total_entries": len(data) if isinstance(data, (dict, list)) else 1
    }

    return metadata


def process_manufacturing_expert():
    """Manufacturing Expert 플러그인 YAML → JSON 변환"""

    print("\n" + "=" * 80)
    print("🏭 Manufacturing Expert - YAML to JSON Conversion")
    print("=" * 80)

    # 경로 설정
    plugin_config_dir = project_root / 'plugins' / 'manufacturing_expert' / 'config'
    output_dir = project_root / 'data' / 'rag_knowledge' / 'manufacturing'
    output_dir.mkdir(parents=True, exist_ok=True)

    yaml_files = list(plugin_config_dir.glob('*.yaml'))

    print(f"\n📁 Source: {plugin_config_dir}")
    print(f"📁 Output: {output_dir}")
    print(f"📄 Files to convert: {len(yaml_files)}\n")

    results = {}

    for yaml_file in yaml_files:
        data = convert_yaml_to_json(yaml_file, output_dir)
        data_type = yaml_file.stem

        # RAG 메타데이터 생성
        metadata = create_rag_metadata('manufacturing_expert', data, data_type)

        # 메타데이터와 함께 저장
        enriched_data = {
            "metadata": metadata,
            "data": data
        }

        enriched_path = output_dir / f"{yaml_file.stem}_with_metadata.json"
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)

        print(f"   + Metadata: {enriched_path.name}")

        results[data_type] = {
            'original_yaml': str(yaml_file),
            'json_output': str(output_dir / f"{yaml_file.stem}.json"),
            'enriched_output': str(enriched_path),
            'entries': len(data) if isinstance(data, (dict, list)) else 1
        }

    return results


def process_packaging_expert():
    """Packaging Expert 플러그인 YAML → JSON 변환"""

    print("\n" + "=" * 80)
    print("📦 Packaging Expert - YAML to JSON Conversion")
    print("=" * 80)

    # 경로 설정
    plugin_config_dir = project_root / 'plugins' / 'packaging_expert' / 'config'
    output_dir = project_root / 'data' / 'rag_knowledge' / 'packaging'
    output_dir.mkdir(parents=True, exist_ok=True)

    yaml_files = list(plugin_config_dir.glob('*.yaml'))

    print(f"\n📁 Source: {plugin_config_dir}")
    print(f"📁 Output: {output_dir}")
    print(f"📄 Files to convert: {len(yaml_files)}\n")

    results = {}

    for yaml_file in yaml_files:
        data = convert_yaml_to_json(yaml_file, output_dir)
        data_type = yaml_file.stem

        # RAG 메타데이터 생성
        metadata = create_rag_metadata('packaging_expert', data, data_type)

        # 메타데이터와 함께 저장
        enriched_data = {
            "metadata": metadata,
            "data": data
        }

        enriched_path = output_dir / f"{yaml_file.stem}_with_metadata.json"
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)

        print(f"   + Metadata: {enriched_path.name}")

        results[data_type] = {
            'original_yaml': str(yaml_file),
            'json_output': str(output_dir / f"{yaml_file.stem}.json"),
            'enriched_output': str(enriched_path),
            'entries': len(data) if isinstance(data, (dict, list)) else 1
        }

    return results


def generate_summary_report(manufacturing_results: Dict, packaging_results: Dict):
    """변환 결과 요약 리포트"""

    print("\n" + "=" * 80)
    print("📊 Conversion Summary Report")
    print("=" * 80)

    print("\n🏭 Manufacturing Expert:")
    print(f"   Total files converted: {len(manufacturing_results)}")
    for data_type, info in manufacturing_results.items():
        print(f"   - {data_type}: {info['entries']} entries")

    print("\n📦 Packaging Expert:")
    print(f"   Total files converted: {len(packaging_results)}")
    for data_type, info in packaging_results.items():
        print(f"   - {data_type}: {info['entries']} entries")

    # 요약 JSON 저장
    summary = {
        "conversion_date": "2025-01-25",
        "purpose": "RAG knowledge base creation from plugin configs",
        "strategy": "dual_storage",
        "locations": {
            "source": "plugins/*/config/*.yaml (code execution)",
            "target": "data/rag_knowledge/*/*.json (RAG indexing)"
        },
        "manufacturing_expert": manufacturing_results,
        "packaging_expert": packaging_results
    }

    summary_path = project_root / 'data' / 'rag_knowledge' / 'conversion_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Summary saved: {summary_path}")


def verify_dual_storage():
    """두 군데 저장 전략 검증"""

    print("\n" + "=" * 80)
    print("🔍 Dual Storage Strategy Verification")
    print("=" * 80)

    checks = []

    # Check 1: plugins/ YAML 존재 확인
    print("\n✓ Check 1: Source YAML files (plugins/)")
    manufacturing_yamls = list((project_root / 'plugins' / 'manufacturing_expert' / 'config').glob('*.yaml'))
    packaging_yamls = list((project_root / 'plugins' / 'packaging_expert' / 'config').glob('*.yaml'))

    print(f"   Manufacturing: {len(manufacturing_yamls)} YAML files")
    print(f"   Packaging: {len(packaging_yamls)} YAML files")
    checks.append(len(manufacturing_yamls) > 0 and len(packaging_yamls) > 0)

    # Check 2: data/ JSON 존재 확인
    print("\n✓ Check 2: Target JSON files (data/)")
    manufacturing_jsons = list((project_root / 'data' / 'rag_knowledge' / 'manufacturing').glob('*.json'))
    packaging_jsons = list((project_root / 'data' / 'rag_knowledge' / 'packaging').glob('*.json'))

    print(f"   Manufacturing: {len(manufacturing_jsons)} JSON files")
    print(f"   Packaging: {len(packaging_jsons)} JSON files")
    checks.append(len(manufacturing_jsons) > 0 and len(packaging_jsons) > 0)

    # Check 3: Python에서 YAML 로드 가능
    print("\n✓ Check 3: Python can load YAML (code execution)")
    try:
        from plugins.manufacturing_expert import ManufacturingExpertPlugin
        plugin = ManufacturingExpertPlugin()
        print(f"   ✅ Plugin loaded successfully")
        print(f"   ✅ Config loaded: {len(plugin.config)} keys")
        checks.append(True)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        checks.append(False)

    # Check 4: JSON이 RAG 인덱싱 가능한 형태
    print("\n✓ Check 4: JSON format suitable for RAG")
    test_json = project_root / 'data' / 'rag_knowledge' / 'manufacturing' / 'terminology_with_metadata.json'
    if test_json.exists():
        with open(test_json, 'r') as f:
            data = json.load(f)
            has_metadata = 'metadata' in data
            has_data = 'data' in data
            is_searchable = data.get('metadata', {}).get('searchable', False)
            print(f"   ✅ Metadata present: {has_metadata}")
            print(f"   ✅ Data present: {has_data}")
            print(f"   ✅ Searchable: {is_searchable}")
            checks.append(has_metadata and has_data and is_searchable)
    else:
        print(f"   ❌ Test file not found")
        checks.append(False)

    # 최종 결과
    print("\n" + "=" * 80)
    all_passed = all(checks)
    if all_passed:
        print("✅ All checks passed! Dual storage strategy is working.")
    else:
        print(f"⚠️  {sum(checks)}/{len(checks)} checks passed")

    print("\n📋 Strategy Explanation:")
    print("   1. plugins/*.yaml → Code execution (Python loads YAML)")
    print("   2. data/*.json → RAG indexing (Vector DB loads JSON)")
    print("   3. Both exist simultaneously for different purposes")
    print("   4. JSON has metadata for better RAG retrieval")

    return all_passed


def main():
    """메인 실행 함수"""

    print("=" * 80)
    print("🔄 YAML to JSON Conversion for RAG")
    print("=" * 80)
    print("\n목적: plugins/의 YAML을 JSON으로 변환하여 data/에 RAG용 저장")
    print("전략: 두 군데 저장 (plugins/=코드용, data/=RAG용)")

    # Manufacturing Expert 변환
    manufacturing_results = process_manufacturing_expert()

    # Packaging Expert 변환
    packaging_results = process_packaging_expert()

    # 요약 리포트 생성
    generate_summary_report(manufacturing_results, packaging_results)

    # 두 군데 저장 전략 검증
    success = verify_dual_storage()

    print("\n" + "=" * 80)
    if success:
        print("✅ 변환 완료! plugins/와 data/ 모두에 데이터 존재")
    else:
        print("⚠️  변환 완료했으나 일부 검증 실패")
    print("=" * 80)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
