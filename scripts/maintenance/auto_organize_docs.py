#!/usr/bin/env python3
"""
문서 자동 정리 시스템
- 파일명 패턴 기반 자동 분류
- 날짜 기반 자동 아카이빙
- 중요 문서 보호
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
import argparse


class DocumentOrganizer:
    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.moves: List[Tuple[Path, Path]] = []
        
        # 루트에 유지할 중요 문서들
        self.keep_in_root = {
            'CLAUDE.md',
            'PROGRESS.md', 
            'README.md',
            'QUICK_START.md',
            'Makefile',
            'Dockerfile',
            'pytest.ini',
            '.env',
            '.env.example',
            '.env.local',
            '.envrc',
            '.gitignore',
            '.dockerignore',
            '.claudeignore',
            '.coveragerc'
        }
        
        # 파일 분류 규칙 (패턴: 목적지)
        self.file_rules = [
            # 가이드 문서
            (r'^CLAUDE_.*\.md$', 'docs/guides'),
            (r'^.*_GUIDE\.md$', 'docs/guides'),
            (r'^.*_README\.md$', 'docs/guides'),
            
            # 분석 문서
            (r'^DISCOUNT_.*\.md$', 'docs/analysis'),
            (r'^.*_ANALYSIS\.md$', 'docs/analysis'),
            (r'^.*_REPORT\.md$', 'docs/analysis'),
            (r'^.*_INDEX\.md$', 'docs/analysis'),
            (r'^.*_SUMMARY\.md$', 'docs/analysis'),
            
            # 개발 문서
            (r'^.*_IMPLEMENTATION.*\.py$', 'docs/development'),
            (r'^SKILLS_.*\.md$', 'docs/development'),
            
            # 테스트 파일
            (r'^test_.*\.py$', 'tests'),
            (r'^.*_test\.py$', 'tests'),
            
            # MCP 설정
            (r'^\.mcp\..*\.json$', 'config/mcp'),
            
            # Docker 설정
            (r'^docker-compose\..*\.yml$', 'config/docker'),
            
            # Requirements
            (r'^requirements-.*\.txt$', 'config/requirements'),
            
            # 스크립트
            (r'^.*\.sh$', 'scripts'),
            (r'^run_.*\.py$', 'scripts'),
            (r'^validate_.*\.py$', 'scripts'),
            (r'^apply-.*\.sh$', 'scripts'),
        ]
        
        # 아카이빙 기준 (일)
        self.archive_after_days = 30
        
    def scan_root_files(self) -> List[Path]:
        """루트 디렉토리의 파일들만 스캔"""
        files = []
        for item in self.project_root.iterdir():
            if item.is_file() and not item.name.startswith('.git'):
                files.append(item)
        return files
    
    def should_keep_in_root(self, filename: str) -> bool:
        """루트에 유지해야 하는 파일인지 확인"""
        return filename in self.keep_in_root
    
    def get_destination(self, file_path: Path) -> str | None:
        """파일의 목적지 경로 결정"""
        filename = file_path.name
        
        # 루트 유지 파일
        if self.should_keep_in_root(filename):
            return None
        
        # 패턴 매칭
        for pattern, destination in self.file_rules:
            if re.match(pattern, filename, re.IGNORECASE):
                return destination
        
        return None
    
    def should_archive(self, file_path: Path) -> bool:
        """아카이빙 대상인지 확인 (30일 이상 수정 안 됨)"""
        if not file_path.suffix in ['.md', '.txt', '.py']:
            return False
        
        if self.should_keep_in_root(file_path.name):
            return False
        
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            return age_days > self.archive_after_days
        except:
            return False
    
    def get_archive_path(self, file_path: Path) -> str:
        """아카이빙 경로 결정"""
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        year_month = mtime.strftime('%Y-%m')
        return f'docs/archived/{year_month}'
    
    def organize(self):
        """문서 정리 실행"""
        print(f"{'[DRY RUN] ' if self.dry_run else ''}문서 정리 시작...\n")
        
        files = self.scan_root_files()
        print(f"루트에서 {len(files)}개 파일 발견\n")
        
        # 1단계: 패턴 기반 분류
        print("=" * 60)
        print("1단계: 파일 분류")
        print("=" * 60)
        
        for file_path in files:
            destination = self.get_destination(file_path)
            
            if destination:
                dest_path = self.project_root / destination / file_path.name
                self.moves.append((file_path, dest_path))
                print(f"📁 {file_path.name}")
                print(f"   → {destination}/")
                print()
        
        # 2단계: 날짜 기반 아카이빙
        print("\n" + "=" * 60)
        print("2단계: 오래된 문서 아카이빙")
        print("=" * 60)
        
        for file_path in files:
            # 이미 이동 예정이면 스킵
            if any(file_path == src for src, _ in self.moves):
                continue
            
            if self.should_archive(file_path):
                archive_path = self.get_archive_path(file_path)
                dest_path = self.project_root / archive_path / file_path.name
                self.moves.append((file_path, dest_path))
                
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (datetime.now() - mtime).days
                
                print(f"📦 {file_path.name}")
                print(f"   수정: {mtime.strftime('%Y-%m-%d')} ({age_days}일 전)")
                print(f"   → {archive_path}/")
                print()
        
        # 실행
        if self.moves:
            print("\n" + "=" * 60)
            print(f"총 {len(self.moves)}개 파일 이동")
            print("=" * 60)
            
            if not self.dry_run:
                self._execute_moves()
                print("\n✅ 정리 완료!")
            else:
                print("\n💡 실제 실행하려면: --execute 옵션 사용")
        else:
            print("\n✅ 이미 정리되어 있습니다!")
    
    def _execute_moves(self):
        """실제 파일 이동 실행"""
        for src, dest in self.moves:
            # 목적지 디렉토리 생성
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 이동
            try:
                shutil.move(str(src), str(dest))
                print(f"✓ {src.name} → {dest.parent.name}/")
            except Exception as e:
                print(f"✗ {src.name} 이동 실패: {e}")
    
    def create_directory_structure(self):
        """필요한 디렉토리 구조 생성"""
        directories = [
            'docs/guides',
            'docs/analysis', 
            'docs/development',
            'docs/archived',
            'tests',
            'config/mcp',
            'config/docker',
            'config/requirements',
            'scripts',
        ]
        
        for directory in directories:
            path = self.project_root / directory
            if not path.exists():
                if not self.dry_run:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"✓ 생성: {directory}/")
                else:
                    print(f"[DRY RUN] 생성 예정: {directory}/")


def main():
    parser = argparse.ArgumentParser(description='문서 자동 정리 시스템')
    parser.add_argument('--execute', action='store_true', 
                       help='실제로 파일을 이동합니다 (기본값: dry-run)')
    parser.add_argument('--project-root', type=str, 
                       default=os.getcwd(),
                       help='프로젝트 루트 디렉토리')
    parser.add_argument('--create-dirs', action='store_true',
                       help='필요한 디렉토리 구조 생성')
    
    args = parser.parse_args()
    
    organizer = DocumentOrganizer(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    if args.create_dirs:
        print("디렉토리 구조 생성 중...")
        organizer.create_directory_structure()
        print()
    
    organizer.organize()


if __name__ == '__main__':
    main()
