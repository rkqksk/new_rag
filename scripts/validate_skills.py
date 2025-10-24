#!/usr/bin/env python3
"""
Claude 스킬 검증 및 활성화 스크립트
모든 스킬이 Agent Skills 스펙에 맞게 작동하는지 확인합니다.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional

class SkillValidator:
    def __init__(self, claude_dir: Path):
        self.claude_dir = claude_dir
        self.skills_dir = claude_dir / 'skills'
        
    def find_all_skills(self) -> List[Path]:
        """모든 스킬 폴더 찾기"""
        skills = []
        if self.skills_dir.exists():
            for item in self.skills_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    skills.append(item)
        return skills
    
    def validate_skill(self, skill_dir: Path) -> Dict:
        """단일 스킬 검증"""
        result = {
            'name': skill_dir.name,
            'valid': False,
            'has_skill_md': False,
            'has_frontmatter': False,
            'frontmatter_valid': False,
            'has_content': False,
            'errors': [],
            'warnings': []
        }
        
        # SKILL.md 존재 확인
        skill_md = skill_dir / 'SKILL.md'
        if not skill_md.exists():
            result['errors'].append("SKILL.md 파일이 없습니다")
            return result
        
        result['has_skill_md'] = True
        
        # 파일 읽기
        try:
            content = skill_md.read_text(encoding='utf-8')
        except Exception as e:
            result['errors'].append(f"파일 읽기 실패: {e}")
            return result
        
        # Frontmatter 파싱
        if not content.startswith('---'):
            result['errors'].append("YAML frontmatter가 없습니다 (---로 시작해야 함)")
            return result
        
        result['has_frontmatter'] = True
        
        try:
            # Frontmatter 추출
            parts = content.split('---', 2)
            if len(parts) < 3:
                result['errors'].append("Frontmatter가 올바르게 닫히지 않았습니다")
                return result
            
            frontmatter_text = parts[1]
            body = parts[2].strip()
            
            # YAML 파싱
            frontmatter = yaml.safe_load(frontmatter_text)
            
            # 필수 필드 확인
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in frontmatter:
                    result['errors'].append(f"필수 필드 누락: {field}")
            
            # name이 디렉토리 이름과 일치하는지 확인
            if 'name' in frontmatter:
                # 하이픈을 언더스코어로 변환해서 비교
                expected_name = skill_dir.name.replace('_', '-')
                actual_name = frontmatter['name']
                if expected_name != actual_name:
                    result['warnings'].append(
                        f"스킬 이름 불일치: 폴더={skill_dir.name}, frontmatter={actual_name}"
                    )
            
            # description 길이 확인
            if 'description' in frontmatter:
                desc_len = len(frontmatter['description'])
                if desc_len < 50:
                    result['warnings'].append(f"description이 너무 짧습니다 ({desc_len}자)")
                elif desc_len > 500:
                    result['warnings'].append(f"description이 너무 깁니다 ({desc_len}자)")
            
            # 선택적 필드 확인
            if 'license' in frontmatter:
                result['has_license'] = True
            
            if 'allowed-tools' in frontmatter:
                tools = frontmatter['allowed-tools']
                if not isinstance(tools, list):
                    result['warnings'].append("allowed-tools는 리스트여야 합니다")
                result['allowed_tools'] = len(tools) if isinstance(tools, list) else 0
            
            if 'metadata' in frontmatter:
                result['has_metadata'] = True
            
            result['frontmatter_valid'] = len(result['errors']) == 0
            
            # 본문 확인
            if len(body) > 100:
                result['has_content'] = True
            else:
                result['warnings'].append("본문이 너무 짧습니다")
            
            # 전체 검증 결과
            result['valid'] = (
                result['has_skill_md'] and
                result['has_frontmatter'] and
                result['frontmatter_valid'] and
                result['has_content'] and
                len(result['errors']) == 0
            )
            
        except yaml.YAMLError as e:
            result['errors'].append(f"YAML 파싱 오류: {e}")
        except Exception as e:
            result['errors'].append(f"검증 중 오류: {e}")
        
        return result
    
    def validate_all(self) -> Dict:
        """모든 스킬 검증"""
        skills = self.find_all_skills()
        results = {
            'total': len(skills),
            'valid': 0,
            'invalid': 0,
            'skills': {}
        }
        
        for skill_dir in skills:
            result = self.validate_skill(skill_dir)
            results['skills'][skill_dir.name] = result
            
            if result['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        return results
    
    def print_report(self, results: Dict):
        """검증 결과 리포트 출력"""
        print("\n" + "="*70)
        print("🔍 Claude Skills 검증 리포트")
        print("="*70)
        
        print(f"\n📊 전체 통계:")
        print(f"  - 전체 스킬: {results['total']}개")
        print(f"  - ✅ 정상: {results['valid']}개")
        print(f"  - ❌ 오류: {results['invalid']}개")
        
        # 정상 스킬
        if results['valid'] > 0:
            print(f"\n✅ 정상 스킬 ({results['valid']}개):")
            for name, result in results['skills'].items():
                if result['valid']:
                    warnings = f" ({len(result['warnings'])} 경고)" if result['warnings'] else ""
                    tools = f", {result.get('allowed_tools', 0)} tools" if result.get('allowed_tools') else ""
                    print(f"  ✓ {name}{warnings}{tools}")
        
        # 오류 스킬
        if results['invalid'] > 0:
            print(f"\n❌ 오류 스킬 ({results['invalid']}개):")
            for name, result in results['skills'].items():
                if not result['valid']:
                    print(f"  ✗ {name}")
                    for error in result['errors']:
                        print(f"      - {error}")
        
        # 경고사항
        warnings_total = sum(
            len(r['warnings']) for r in results['skills'].values()
        )
        if warnings_total > 0:
            print(f"\n⚠️  경고사항 ({warnings_total}개):")
            for name, result in results['skills'].items():
                if result['warnings']:
                    print(f"  {name}:")
                    for warning in result['warnings']:
                        print(f"    - {warning}")
        
        # 다음 단계
        print(f"\n🚀 다음 단계:")
        if results['invalid'] > 0:
            print(f"  1. 오류가 있는 스킬 수정 필요")
        else:
            print(f"  1. ✅ 모든 스킬이 정상입니다!")
        
        print(f"  2. Claude 재시작")
        print(f"  3. 스킬 테스트:")
        for name in list(results['skills'].keys())[:3]:
            cmd_name = name.replace('_', '-')
            print(f"     - \"{cmd_name} 관련 작업 요청\"")

def main():
    print("="*70)
    print("🔍 Claude Skills 검증")
    print("="*70)
    
    # Claude 디렉토리 찾기
    project_root = Path.cwd()
    claude_dir = project_root / '.claude'
    
    if not claude_dir.exists():
        print(f"\n❌ .claude 디렉토리를 찾을 수 없습니다: {claude_dir}")
        return 1
    
    print(f"\n📂 Claude 디렉토리: {claude_dir}")
    
    # 검증 실행
    validator = SkillValidator(claude_dir)
    results = validator.validate_all()
    
    # 리포트 출력
    validator.print_report(results)
    
    # 종료 코드
    return 0 if results['invalid'] == 0 else 1

if __name__ == '__main__':
    exit(main())
