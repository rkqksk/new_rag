#!/usr/bin/env python3
"""
Claude 설정 통합 및 정리 스크립트
- 중복 제거
- 작동하지 않는 파일 식별
- 통합된 구조 생성
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Set

class ClaudeConsolidator:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path('/Users/oypnus/Project/rag-enterprise')
        self.home_claude = Path('/Users/oypnus/.claude')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 통합할 디렉토리들
        self.claude_dirs = [
            self.project_root / '.claude',
            self.project_root / '.claude-plugin', 
            self.project_root / '.claude-unified',
            self.project_root / '.claude-v3',
            self.home_claude
        ]
        
        # 결과 디렉토리
        self.consolidated = self.project_root / '.claude-consolidated'
        self.backup_dir = self.project_root / f'.claude-backup-{self.timestamp}'
        
        # 파일 추적
        self.file_hashes = {}  # hash -> original_path
        self.duplicates = []
        self.broken_files = []
        self.stats = {
            'total_files': 0,
            'duplicates': 0,
            'broken': 0,
            'agents': 0,
            'commands': 0,
            'skills': 0
        }

    def create_backup(self):
        """현재 .claude 폴더들 백업"""
        print(f"📦 백업 생성: {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)
        
        for dir_path in self.claude_dirs:
            if dir_path.exists():
                backup_name = dir_path.name
                if dir_path == self.home_claude:
                    backup_name = 'home-claude'
                
                backup_path = self.backup_dir / backup_name
                if dir_path.is_dir():
                    shutil.copytree(dir_path, backup_path, ignore_errors=True)
                    print(f"  ✅ {dir_path} -> {backup_path}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """파일 내용의 해시값 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.broken_files.append(str(file_path))
            return None

    def scan_directory(self, dir_path: Path):
        """디렉토리 스캔 및 파일 수집"""
        if not dir_path.exists():
            return
            
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                # 불필요한 파일 제외
                if any(skip in str(file_path) for skip in [
                    '.git/', '__pycache__/', '.pyc', '.DS_Store',
                    'debug/', 'logs/', 'file-history/', '.backup/'
                ]):
                    continue
                
                self.stats['total_files'] += 1
                
                # 파일 타입 분류
                if '/agents/' in str(file_path):
                    self.stats['agents'] += 1
                elif '/commands/' in str(file_path):
                    self.stats['commands'] += 1
                elif '/skills/' in str(file_path):
                    self.stats['skills'] += 1
                
                # 해시 계산
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    if file_hash in self.file_hashes:
                        self.duplicates.append({
                            'original': self.file_hashes[file_hash],
                            'duplicate': str(file_path)
                        })
                        self.stats['duplicates'] += 1
                    else:
                        self.file_hashes[file_hash] = str(file_path)

    def create_consolidated_structure(self):
        """통합된 구조 생성"""
        print(f"\n🔨 통합 구조 생성: {self.consolidated}")
        
        # 기존 통합 폴더 제거
        if self.consolidated.exists():
            shutil.rmtree(self.consolidated)
        
        # 새 구조 생성
        dirs = [
            'agents',
            'commands',
            'skills',
            'plugins',
            'config',
            'docs'
        ]
        
        for dir_name in dirs:
            (self.consolidated / dir_name).mkdir(parents=True, exist_ok=True)

    def consolidate_files(self):
        """중복 제거하며 파일 통합"""
        print("\n📁 파일 통합 중...")
        
        processed_hashes = set()
        
        for file_hash, file_path in self.file_hashes.items():
            if file_hash in processed_hashes:
                continue
                
            source = Path(file_path)
            
            # 대상 경로 결정
            if '/agents/' in file_path:
                dest_dir = self.consolidated / 'agents'
            elif '/commands/' in file_path:
                dest_dir = self.consolidated / 'commands'
            elif '/skills/' in file_path:
                dest_dir = self.consolidated / 'skills'
            elif '/plugins/' in file_path or '/.claude-plugin/' in file_path:
                dest_dir = self.consolidated / 'plugins'
            else:
                # config 파일들
                if source.suffix in ['.json', '.yaml', '.yml', '.toml']:
                    dest_dir = self.consolidated / 'config'
                elif source.suffix == '.md':
                    dest_dir = self.consolidated / 'docs'
                else:
                    dest_dir = self.consolidated / 'config'
            
            # 파일 복사
            dest = dest_dir / source.name
            
            # 이름 충돌 처리
            if dest.exists():
                base = dest.stem
                ext = dest.suffix
                counter = 1
                while dest.exists():
                    dest = dest_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            try:
                shutil.copy2(source, dest)
                processed_hashes.add(file_hash)
            except Exception as e:
                print(f"  ⚠️ 복사 실패: {source} -> {dest}: {e}")

    def create_index(self):
        """통합된 파일들의 인덱스 생성"""
        index = {
            'timestamp': self.timestamp,
            'stats': self.stats,
            'structure': {},
            'duplicates': self.duplicates[:10],  # 처음 10개만
            'broken_files': self.broken_files[:10]  # 처음 10개만
        }
        
        # 구조 스캔
        for category in ['agents', 'commands', 'skills', 'plugins', 'config', 'docs']:
            category_path = self.consolidated / category
            if category_path.exists():
                files = [f.name for f in category_path.iterdir() if f.is_file()]
                index['structure'][category] = {
                    'count': len(files),
                    'files': files[:20]  # 처음 20개만
                }
        
        # 인덱스 저장
        index_path = self.consolidated / 'INDEX.json'
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2, default=str)
        
        print(f"\n📊 인덱스 생성: {index_path}")

    def create_readme(self):
        """README 파일 생성"""
        readme_content = f"""# Claude 통합 설정

생성일: {self.timestamp}

## 📊 통계

- **전체 파일**: {self.stats['total_files']}
- **중복 제거**: {self.stats['duplicates']}
- **손상된 파일**: {len(self.broken_files)}
- **에이전트**: {self.stats['agents']}
- **명령어**: {self.stats['commands']}
- **스킬**: {self.stats['skills']}

## 📁 구조

```
.claude-consolidated/
├── agents/        # AI 에이전트 정의
├── commands/      # 슬래시 명령어
├── skills/        # 재사용 가능한 스킬
├── plugins/       # 플러그인 정의
├── config/        # 설정 파일
├── docs/          # 문서
└── INDEX.json     # 전체 인덱스
```

## 🔄 통합된 소스

1. 프로젝트 `.claude`
2. 프로젝트 `.claude-plugin`
3. 프로젝트 `.claude-unified`
4. 프로젝트 `.claude-v3`
5. 홈 디렉토리 `.claude`

## 📝 다음 단계

1. `.claude-consolidated` 폴더 검토
2. 필요한 파일만 선택
3. 기존 `.claude` 폴더 교체
4. 불필요한 백업 삭제

## ⚠️ 주의사항

- 백업: `{self.backup_dir}`
- 중복 파일 목록: INDEX.json 참조
- 손상된 파일 목록: INDEX.json 참조
"""
        
        readme_path = self.consolidated / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"📄 README 생성: {readme_path}")

    def generate_report(self):
        """상세 리포트 생성"""
        report = {
            'summary': self.stats,
            'duplicates': self.duplicates,
            'broken_files': self.broken_files,
            'file_mapping': {}
        }
        
        # 파일 매핑 생성
        for hash_val, path in self.file_hashes.items():
            filename = Path(path).name
            if filename not in report['file_mapping']:
                report['file_mapping'][filename] = []
            report['file_mapping'][filename].append(path)
        
        # 리포트 저장
        report_path = self.project_root / f'claude_consolidation_report_{self.timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 상세 리포트: {report_path}")
        
        # 요약 출력
        print("\n" + "="*50)
        print("📌 통합 요약")
        print("="*50)
        print(f"전체 파일: {self.stats['total_files']}")
        print(f"중복 파일: {self.stats['duplicates']}")
        print(f"손상된 파일: {len(self.broken_files)}")
        print(f"에이전트: {self.stats['agents']}")
        print(f"명령어: {self.stats['commands']}")
        print(f"스킬: {self.stats['skills']}")
        
        if self.duplicates:
            print(f"\n🔍 주요 중복 파일 (처음 5개):")
            for dup in self.duplicates[:5]:
                print(f"  - {Path(dup['original']).name}")
                print(f"    원본: {dup['original']}")
                print(f"    중복: {dup['duplicate']}")

    def run(self):
        """전체 프로세스 실행"""
        print("🚀 Claude 설정 통합 시작")
        print("="*50)
        
        # 1. 백업
        self.create_backup()
        
        # 2. 스캔
        print("\n🔍 파일 스캔 중...")
        for dir_path in self.claude_dirs:
            if dir_path.exists():
                print(f"  스캔: {dir_path}")
                self.scan_directory(dir_path)
        
        # 3. 통합 구조 생성
        self.create_consolidated_structure()
        
        # 4. 파일 통합
        self.consolidate_files()
        
        # 5. 인덱스 생성
        self.create_index()
        
        # 6. README 생성
        self.create_readme()
        
        # 7. 리포트 생성
        self.generate_report()
        
        print("\n✅ 통합 완료!")
        print(f"결과: {self.consolidated}")
        print(f"백업: {self.backup_dir}")

if __name__ == "__main__":
    consolidator = ClaudeConsolidator()
    consolidator.run()
