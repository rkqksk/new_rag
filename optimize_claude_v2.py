#!/usr/bin/env python3
"""
Claude 설정 최적화 스크립트 v2
- 필수 파일만 보존
- 불필요한 파일 제거
- 깔끔한 구조 생성
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

# 설정
PROJECT_ROOT = Path('/Users/oypnus/Project/rag-enterprise')
HOME_CLAUDE = Path('/Users/oypnus/.claude')
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# 보존할 파일 패턴
KEEP_PATTERNS = {
    'agents': ['.md', '.py'],
    'commands': ['.md'],
    'skills': ['.md', '.py', 'SKILL.md'],
    'config': ['.json', '.yaml', '.yml'],
    'docs': ['.md']
}

# 제외할 디렉토리
EXCLUDE_DIRS = [
    'debug', 'file-history', 'logs', '__pycache__', 
    '.backup', '.git', 'ide', '.DS_Store'
]

def create_clean_structure():
    """깔끔한 .claude 구조 생성"""
    print("🏗️ 깔끔한 구조 생성 중...")
    
    # 타겟 디렉토리
    target = PROJECT_ROOT / '.claude-clean'
    
    # 기존 디렉토리 제거
    if target.exists():
        shutil.rmtree(target)
    
    # 디렉토리 구조 생성
    structure = {
        'agents': '# AI Agents\n\nAI 에이전트 정의 파일들',
        'commands': '# Commands\n\n슬래시 명령어 정의',
        'skills': '# Skills\n\n재사용 가능한 스킬',
        'workflows': '# Workflows\n\n작업 흐름 정의',
        'config': '# Configuration\n\n설정 파일들'
    }
    
    for dir_name, readme_content in structure.items():
        dir_path = target / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # README 생성
        readme_path = dir_path / 'README.md'
        readme_path.write_text(readme_content)
    
    return target

def collect_essential_files(source_dirs):
    """필수 파일만 수집"""
    print("📂 필수 파일 수집 중...")
    
    essential_files = {
        'agents': [],
        'commands': [],
        'skills': [],
        'config': [],
        'workflows': []
    }
    
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
            
        print(f"  스캔: {source_dir}")
        
        # agents 수집
        agents_path = source_dir / 'agents'
        if agents_path.exists():
            for file in agents_path.glob('*.md'):
                if file.name not in [f.name for f in essential_files['agents']]:
                    essential_files['agents'].append(file)
        
        # commands 수집
        for cmd_path in [source_dir / 'commands', source_dir / 'commands' / 'sc']:
            if cmd_path.exists():
                for file in cmd_path.glob('*.md'):
                    if file.name not in [f.name for f in essential_files['commands']]:
                        essential_files['commands'].append(file)
        
        # skills 수집
        skills_path = source_dir / 'skills'
        if skills_path.exists():
            for skill_dir in skills_path.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                    skill_file = skill_dir / 'SKILL.md'
                    if skill_file.exists():
                        essential_files['skills'].append(skill_dir)
        
        # config 파일 수집
        for config_file in source_dir.glob('*.json'):
            if 'backup' not in config_file.name.lower():
                essential_files['config'].append(config_file)
    
    return essential_files

def copy_essential_files(essential_files, target):
    """필수 파일 복사"""
    print("📋 파일 복사 중...")
    
    stats = {'agents': 0, 'commands': 0, 'skills': 0, 'config': 0}
    
    # Agents
    for agent_file in essential_files['agents']:
        dest = target / 'agents' / agent_file.name
        shutil.copy2(agent_file, dest)
        stats['agents'] += 1
        print(f"  ✅ Agent: {agent_file.name}")
    
    # Commands
    for cmd_file in essential_files['commands']:
        dest = target / 'commands' / cmd_file.name
        shutil.copy2(cmd_file, dest)
        stats['commands'] += 1
        print(f"  ✅ Command: {cmd_file.name}")
    
    # Skills
    for skill_dir in essential_files['skills']:
        dest_dir = target / 'skills' / skill_dir.name
        shutil.copytree(skill_dir, dest_dir)
        stats['skills'] += 1
        print(f"  ✅ Skill: {skill_dir.name}")
    
    # Config
    for config_file in essential_files['config']:
        dest = target / 'config' / config_file.name
        shutil.copy2(config_file, dest)
        stats['config'] += 1
        print(f"  ✅ Config: {config_file.name}")
    
    return stats

def create_master_config(target, stats):
    """마스터 설정 파일 생성"""
    print("⚙️ 마스터 설정 생성 중...")
    
    config = {
        "version": "2.0",
        "timestamp": TIMESTAMP,
        "structure": {
            "agents": stats['agents'],
            "commands": stats['commands'],
            "skills": stats['skills'],
            "config": stats['config']
        },
        "settings": {
            "auto_load": True,
            "debug": False,
            "optimization": "production"
        }
    }
    
    config_path = target / 'claude.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"  ✅ 설정 파일: {config_path}")

def create_activation_script(target):
    """활성화 스크립트 생성"""
    script_content = f"""#!/bin/bash
# Claude 설정 활성화 스크립트

echo "🚀 Claude 설정 활성화..."

# 백업
if [ -d "$HOME/.claude" ]; then
    echo "📦 기존 설정 백업..."
    mv "$HOME/.claude" "$HOME/.claude.backup.{TIMESTAMP}"
fi

# 새 설정 적용
echo "✨ 새 설정 적용..."
cp -r "{target}" "$HOME/.claude"

# 프로젝트 설정 업데이트
if [ -d "{PROJECT_ROOT}/.claude" ]; then
    mv "{PROJECT_ROOT}/.claude" "{PROJECT_ROOT}/.claude.backup.{TIMESTAMP}"
fi
ln -s "$HOME/.claude" "{PROJECT_ROOT}/.claude"

echo "✅ 완료! 새 Claude 설정이 활성화되었습니다."
"""
    
    script_path = target / 'activate.sh'
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    print(f"  ✅ 활성화 스크립트: {script_path}")

def main():
    print("="*60)
    print("🧹 Claude 설정 최적화 v2")
    print("="*60)
    
    # 1. 백업
    backup_dir = PROJECT_ROOT / f'.claude-backup-{TIMESTAMP}'
    print(f"\n📦 백업 생성: {backup_dir}")
    
    for dir_path in [HOME_CLAUDE, PROJECT_ROOT / '.claude']:
        if dir_path.exists():
            backup_path = backup_dir / dir_path.name
            if dir_path == HOME_CLAUDE:
                backup_path = backup_dir / 'home-claude'
            shutil.copytree(dir_path, backup_path, ignore_errors=True)
            print(f"  ✅ {dir_path}")
    
    # 2. 깔끔한 구조 생성
    target = create_clean_structure()
    
    # 3. 필수 파일 수집
    source_dirs = [
        PROJECT_ROOT / '.claude',
        PROJECT_ROOT / '.claude-unified',
        PROJECT_ROOT / '.claude-v3',
        HOME_CLAUDE
    ]
    
    essential_files = collect_essential_files(source_dirs)
    
    # 4. 파일 복사
    stats = copy_essential_files(essential_files, target)
    
    # 5. 마스터 설정 생성
    create_master_config(target, stats)
    
    # 6. 활성화 스크립트 생성
    create_activation_script(target)
    
    # 7. 요약
    print("\n" + "="*60)
    print("✅ 최적화 완료!")
    print("="*60)
    print(f"📁 결과: {target}")
    print(f"📦 백업: {backup_dir}")
    print(f"\n📊 통계:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    print(f"\n💡 다음 단계:")
    print(f"  1. {target} 내용 검토")
    print(f"  2. bash {target}/activate.sh 실행하여 적용")
    print(f"  3. 테스트 후 백업 삭제")

if __name__ == "__main__":
    main()
