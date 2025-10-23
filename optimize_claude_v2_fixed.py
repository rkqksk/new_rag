#!/usr/bin/env python3
"""
Claude 설정 최적화 스크립트 v2.1 (호환성 수정)
- Python 3.6+ 호환
- 안전한 백업 및 정리
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

class ClaudeOptimizer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.home_claude = Path.home() / '.claude'
        self.clean_dir = self.project_root / '.claude-clean'
        self.backup_dir = self.project_root / f'.claude-backup-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # 소스 디렉토리들
        self.sources = {
            'home': self.home_claude,
            'root': self.project_root / '.claude',
            'config': self.project_root / '.claude-config',
            'backup': self.project_root / '.claude-backup'
        }
        
        # 수집할 패턴
        self.patterns = {
            'agents': ['*agent*.md', '*-agent.md', 'agent-*.md'],
            'commands': ['*command*.md', '*-cmd.md', 'cmd-*.md'],
            'skills': ['*skill*.md', '*-skill.md', 'skill-*.md'],
            'config': ['*.json', '*.yaml', '*.yml', '*.toml'],
            'workflows': ['*workflow*.md', '*-flow.md', 'flow-*.md']
        }
        
        # 제외할 파일/디렉토리
        self.excludes = {
            'debug', 'test', 'temp', 'cache', '__pycache__',
            '.git', '.DS_Store', 'node_modules', '.venv'
        }

    def safe_copytree(self, src: Path, dst: Path):
        """안전한 디렉토리 복사 (Python 3.6+ 호환)"""
        try:
            if src.exists():
                dst.mkdir(parents=True, exist_ok=True)
                for item in src.rglob('*'):
                    if item.is_file():
                        # 제외 패턴 체크
                        if any(excl in str(item) for excl in self.excludes):
                            continue
                        
                        # 상대 경로 계산
                        rel_path = item.relative_to(src)
                        dest_file = dst / rel_path
                        
                        # 디렉토리 생성
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 파일 복사
                        try:
                            shutil.copy2(item, dest_file)
                        except Exception as e:
                            print(f"⚠️  파일 복사 실패: {item} - {e}")
        except Exception as e:
            print(f"⚠️  디렉토리 복사 실패: {src} - {e}")

    def create_backup(self):
        """기존 설정 백업"""
        print(f"📦 백업 생성: {self.backup_dir}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        for name, path in self.sources.items():
            if path.exists():
                backup_path = self.backup_dir / name
                print(f"  ↳ {name}: {path}")
                self.safe_copytree(path, backup_path)

    def should_exclude(self, path: Path) -> bool:
        """파일/디렉토리 제외 여부 확인"""
        path_str = str(path).lower()
        return any(excl in path_str for excl in self.excludes)

    def collect_files(self, category: str, patterns: List[str]) -> Set[Path]:
        """패턴에 맞는 파일 수집"""
        files = set()
        
        for source_name, source_path in self.sources.items():
            if not source_path.exists():
                continue
                
            for pattern in patterns:
                for file in source_path.rglob(pattern):
                    if file.is_file() and not self.should_exclude(file):
                        files.add(file)
        
        return files

    def deduplicate_files(self, files: Set[Path]) -> Dict[str, Path]:
        """중복 제거 - 최신 파일 선택"""
        file_map = {}
        
        for file in files:
            name = file.name
            if name not in file_map:
                file_map[name] = file
            else:
                # 최신 수정 시간 파일 선택
                if file.stat().st_mtime > file_map[name].stat().st_mtime:
                    file_map[name] = file
        
        return file_map

    def organize_clean_structure(self):
        """정리된 구조 생성"""
        print("\n🗂️  깨끗한 구조 생성...")
        self.clean_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {}
        
        for category, patterns in self.patterns.items():
            print(f"\n📁 {category} 정리 중...")
            
            # 파일 수집
            files = self.collect_files(category, patterns)
            print(f"  ↳ 발견: {len(files)}개")
            
            # 중복 제거
            unique_files = self.deduplicate_files(files)
            print(f"  ↳ 고유: {len(unique_files)}개")
            
            # 복사
            target_dir = self.clean_dir / category
            target_dir.mkdir(parents=True, exist_ok=True)
            
            copied = 0
            for name, src_file in unique_files.items():
                try:
                    dst_file = target_dir / name
                    shutil.copy2(src_file, dst_file)
                    copied += 1
                except Exception as e:
                    print(f"  ⚠️  복사 실패: {name} - {e}")
            
            print(f"  ✅ 복사 완료: {copied}개")
            stats[category] = copied
            
            # README 생성
            self.create_readme(target_dir, category, list(unique_files.keys()))
        
        return stats

    def create_readme(self, directory: Path, category: str, files: List[str]):
        """카테고리별 README 생성"""
        readme_content = f"""# {category.upper()}

## 파일 목록 ({len(files)}개)

"""
        for file in sorted(files):
            readme_content += f"- `{file}`\n"
        
        readme_content += f"""
## 사용 방법

이 디렉토리의 파일들은 Claude {category}입니다.

### 활성화
```bash
# 전체 활성화
cp -r {category}/* ~/.claude/{category}/

# 개별 활성화
cp {category}/specific-file.md ~/.claude/{category}/
```

## 업데이트: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        readme_path = directory / 'README.md'
        readme_path.write_text(readme_content, encoding='utf-8')

    def create_master_config(self, stats: Dict[str, int]):
        """마스터 설정 파일 생성"""
        config = {
            "version": "2.1",
            "created": datetime.now().isoformat(),
            "project": str(self.project_root),
            "statistics": stats,
            "structure": {
                "agents": "AI 에이전트 정의",
                "commands": "실행 가능한 명령어",
                "skills": "특화 기술 세트",
                "config": "설정 파일",
                "workflows": "워크플로우 정의"
            },
            "sources": {name: str(path) for name, path in self.sources.items()},
            "excludes": list(self.excludes)
        }
        
        config_path = self.clean_dir / 'claude.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 설정 파일 생성: {config_path}")

    def create_activation_script(self):
        """활성화 스크립트 생성"""
        script_content = """#!/bin/bash
# Claude 정리된 설정 활성화 스크립트

set -e

CLEAN_DIR=".claude-clean"
TARGET_DIR="$HOME/.claude"

echo "=============================================="
echo "🚀 Claude 설정 활성화"
echo "=============================================="

# 백업 생성
BACKUP_DIR="$HOME/.claude-backup-$(date +%Y%m%d_%H%M%S)"
if [ -d "$TARGET_DIR" ]; then
    echo "📦 기존 설정 백업: $BACKUP_DIR"
    cp -r "$TARGET_DIR" "$BACKUP_DIR"
fi

# 디렉토리 생성
mkdir -p "$TARGET_DIR"

# 각 카테고리 복사
for category in agents commands skills config workflows; do
    if [ -d "$CLEAN_DIR/$category" ]; then
        echo "📁 복사 중: $category"
        mkdir -p "$TARGET_DIR/$category"
        cp -r "$CLEAN_DIR/$category/"* "$TARGET_DIR/$category/" 2>/dev/null || true
    fi
done

echo ""
echo "✅ 활성화 완료!"
echo ""
echo "📊 통계:"
echo "  - agents:    $(find "$TARGET_DIR/agents" -name '*.md' 2>/dev/null | wc -l) 개"
echo "  - commands:  $(find "$TARGET_DIR/commands" -name '*.md' 2>/dev/null | wc -l) 개"
echo "  - skills:    $(find "$TARGET_DIR/skills" -name '*.md' 2>/dev/null | wc -l) 개"
echo "  - config:    $(find "$TARGET_DIR/config" -name '*.*' 2>/dev/null | wc -l) 개"
echo "  - workflows: $(find "$TARGET_DIR/workflows" -name '*.md' 2>/dev/null | wc -l) 개"
echo ""
echo "🔄 변경사항 적용을 위해 Claude를 재시작하세요."
"""
        
        script_path = self.clean_dir / 'activate.sh'
        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)
        
        print(f"🔧 활성화 스크립트 생성: {script_path}")

    def print_summary(self, stats: Dict[str, int]):
        """최종 요약 출력"""
        print("\n" + "="*60)
        print("✨ 최적화 완료!")
        print("="*60)
        
        print(f"\n📊 통계:")
        total = 0
        for category, count in stats.items():
            print(f"  - {category:12s}: {count:3d}개")
            total += count
        print(f"  {'총계':12s}: {total:3d}개")
        
        print(f"\n📂 결과 위치: {self.clean_dir}")
        print(f"💾 백업 위치: {self.backup_dir}")
        
        print(f"\n🚀 활성화 방법:")
        print(f"  bash {self.clean_dir}/activate.sh")

def main():
    print("="*60)
    print("🧹 Claude 설정 최적화 v2.1 (호환성 개선)")
    print("="*60)
    
    # 현재 디렉토리에서 실행
    project_root = os.getcwd()
    optimizer = ClaudeOptimizer(project_root)
    
    try:
        # 1. 백업 생성
        optimizer.create_backup()
        
        # 2. 파일 수집 및 정리
        stats = optimizer.organize_clean_structure()
        
        # 3. 설정 파일 생성
        optimizer.create_master_config(stats)
        
        # 4. 활성화 스크립트 생성
        optimizer.create_activation_script()
        
        # 5. 요약 출력
        optimizer.print_summary(stats)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
