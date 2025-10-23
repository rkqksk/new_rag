#!/usr/bin/env python3
"""
Claude 설정 통합 및 정리 스크립트
산재된 모든 Claude 관련 파일을 분석하고 하나의 .claude 폴더로 통합
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

class ClaudeConsolidator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.report = {
            'found_items': [],
            'duplicates': [],
            'errors': [],
            'consolidated': []
        }
        
    def scan_all_claude_folders(self):
        """모든 Claude 관련 폴더 스캔"""
        print("🔍 Claude 관련 폴더 스캔 중...")
        
        patterns = [
            '.claude*',
            '.mcp*',
            'plugins/',
            'agents/',
            'mcp_servers/'
        ]
        
        found = {}
        for pattern in patterns:
            for path in self.project_root.glob(pattern):
                if path.is_dir() or path.is_file():
                    found[str(path)] = {
                        'type': 'dir' if path.is_dir() else 'file',
                        'size': self._get_size(path),
                        'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    }
        
        self.report['found_items'] = found
        
        # 상세 출력
        print(f"\n발견된 항목:")
        for path, info in found.items():
            print(f"  📁 {path} ({info['type']}, {info['size']} bytes)")
        
        return found
    
    def _get_size(self, path):
        """파일/디렉토리 크기 계산"""
        if path.is_file():
            return path.stat().st_size
        total = 0
        for p in path.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
        return total
    
    def collect_all_skills(self):
        """모든 스킬 수집 및 중복 제거"""
        print("\n📚 스킬 수집 중...")
        
        skills = {}
        skill_paths = [
            '.claude/skills',
            '.claude-plugin/plugins/anthropic-agent-skills',
            '.claude-unified/skills',
            '.claude-v3/skills',
            'plugins/'
        ]
        
        for base_path in skill_paths:
            base = Path(base_path)
            if not base.exists():
                continue
                
            # SKILL.md 파일 찾기
            for skill_file in base.rglob('SKILL.md'):
                skill_dir = skill_file.parent
                skill_name = skill_dir.name
                
                # 스킬 내용 읽기
                try:
                    content = skill_file.read_text()
                    # YAML frontmatter에서 메타데이터 추출
                    metadata = self._extract_metadata(content)
                    
                    # 중복 체크 (내용 해시)
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if skill_name not in skills:
                        skills[skill_name] = {
                            'paths': [str(skill_dir)],
                            'metadata': metadata,
                            'hash': content_hash,
                            'primary_path': str(skill_dir)
                        }
                    else:
                        # 중복 발견
                        skills[skill_name]['paths'].append(str(skill_dir))
                        if skills[skill_name]['hash'] != content_hash:
                            self.report['duplicates'].append({
                                'name': skill_name,
                                'paths': skills[skill_name]['paths'],
                                'different_content': True
                            })
                
                except Exception as e:
                    self.report['errors'].append(f"스킬 읽기 실패 {skill_file}: {e}")
        
        # 결과 출력
        print(f"\n발견된 스킬: {len(skills)}개")
        for name, info in skills.items():
            print(f"  ✅ {name}")
            if len(info['paths']) > 1:
                print(f"     ⚠️  중복 발견: {len(info['paths'])}개 위치")
        
        return skills
    
    def _extract_metadata(self, content):
        """SKILL.md에서 메타데이터 추출"""
        metadata = {}
        if content.startswith('---'):
            lines = content.split('\n')
            for i, line in enumerate(lines[1:], 1):
                if line == '---':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        return metadata
    
    def collect_all_commands(self):
        """모든 명령어 수집"""
        print("\n⚡ 명령어 수집 중...")
        
        commands = {}
        command_paths = [
            '.claude/commands',
            '.claude-plugin/claude-code/.claude/commands',
            '.claude-plugin/plugins/*/commands',
            'plugins/*/commands'
        ]
        
        for base_path in command_paths:
            base = Path(base_path)
            if not base.exists():
                continue
                
            for cmd_file in base.glob('**/*.md'):
                cmd_name = cmd_file.stem
                
                if cmd_name not in commands:
                    commands[cmd_name] = {
                        'paths': [str(cmd_file)],
                        'content': cmd_file.read_text()[:200]  # 첫 200자
                    }
                else:
                    commands[cmd_name]['paths'].append(str(cmd_file))
        
        print(f"발견된 명령어: {len(commands)}개")
        for name in commands:
            print(f"  ⚡ {name}")
        
        return commands
    
    def consolidate_mcp_configs(self):
        """MCP 설정 통합"""
        print("\n🔧 MCP 설정 통합 중...")
        
        mcp_files = list(self.project_root.glob('.mcp*.json'))
        
        consolidated_config = {
            "mcpServers": {},
            "_profiles": {}
        }
        
        for mcp_file in mcp_files:
            try:
                with open(mcp_file) as f:
                    config = json.load(f)
                    
                # 서버 설정 병합
                if 'mcpServers' in config:
                    consolidated_config['mcpServers'].update(config['mcpServers'])
                
                # 프로파일 저장
                profile_name = mcp_file.stem.replace('.mcp.', '')
                if profile_name == '.mcp':
                    profile_name = 'current'
                consolidated_config['_profiles'][profile_name] = config
                    
            except Exception as e:
                self.report['errors'].append(f"MCP 파일 읽기 실패 {mcp_file}: {e}")
        
        print(f"통합된 MCP 서버: {len(consolidated_config['mcpServers'])}개")
        for server in consolidated_config['mcpServers']:
            print(f"  🖥️  {server}")
        
        return consolidated_config
    
    def create_unified_structure(self, skills, commands, mcp_config):
        """통합된 .claude 구조 생성"""
        print("\n🏗️  통합 구조 생성 중...")
        
        # 새로운 .claude 디렉토리
        claude_dir = self.project_root / '.claude.new'
        claude_dir.mkdir(exist_ok=True)
        
        # 1. 스킬 복사 (중복 제거)
        skills_dir = claude_dir / 'skills'
        skills_dir.mkdir(exist_ok=True)
        
        for skill_name, skill_info in skills.items():
            src = Path(skill_info['primary_path'])
            dst = skills_dir / skill_name
            
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                self.report['consolidated'].append(f"스킬: {skill_name}")
        
        # 2. 명령어 복사
        commands_dir = claude_dir / 'commands'
        commands_dir.mkdir(exist_ok=True)
        
        for cmd_name, cmd_info in commands.items():
            if cmd_info['paths']:
                src = Path(cmd_info['paths'][0])
                dst = commands_dir / f"{cmd_name}.md"
                shutil.copy2(src, dst)
                self.report['consolidated'].append(f"명령어: {cmd_name}")
        
        # 3. settings.local.json 생성
        settings = {
            "permissions": {
                "allow": [
                    "Read(//Users/oypnus/**)",
                    "WebFetch(domain:*.com)",
                    "Bash(python*)",
                    "Bash(docker-compose*)",
                    "Bash(curl*)",
                    "mcp__chrome_devtools__navigate_page",
                    "mcp__chrome_devtools__new_page"
                ]
            },
            "enableAllProjectMcpServers": True,
            "outputStyle": "code-mentor"
        }
        
        with open(claude_dir / 'settings.local.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        # 4. MCP 설정 저장
        with open(self.project_root / '.mcp.json.new', 'w') as f:
            # 현재 프로파일만 저장
            current = mcp_config.get('_profiles', {}).get('current', {})
            if not current:
                current = {'mcpServers': mcp_config.get('mcpServers', {})}
            json.dump(current, f, indent=2)
        
        print(f"\n✅ 통합 완료:")
        print(f"   - 스킬: {len(skills)}개")
        print(f"   - 명령어: {len(commands)}개")
        print(f"   - MCP 서버: {len(mcp_config.get('mcpServers', {}))}개")
        
        return claude_dir
    
    def cleanup_duplicates(self):
        """중복 및 불필요한 폴더 정리"""
        print("\n🧹 정리할 항목:")
        
        to_remove = [
            '.claude-unified',
            '.claude-v3',
            '.claude.backup.20251021_111051'
        ]
        
        for item in to_remove:
            path = self.project_root / item
            if path.exists():
                print(f"   🗑️  {item}")
        
        confirm = input("\n이 항목들을 삭제하시겠습니까? (y/n): ")
        if confirm.lower() == 'y':
            for item in to_remove:
                path = self.project_root / item
                if path.exists():
                    shutil.rmtree(path)
                    print(f"   ✓ {item} 삭제됨")
    
    def generate_report(self):
        """최종 리포트 생성"""
        report_file = self.project_root / 'claude-consolidation-report.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"\n📊 리포트 저장됨: {report_file}")
        
        # 요약 출력
        print("\n📋 요약:")
        print(f"   - 발견된 항목: {len(self.report['found_items'])}개")
        print(f"   - 중복: {len(self.report['duplicates'])}개")
        print(f"   - 오류: {len(self.report['errors'])}개")
        print(f"   - 통합됨: {len(self.report['consolidated'])}개")
    
    def apply_changes(self):
        """변경사항 적용"""
        print("\n🔄 변경사항 적용 중...")
        
        # 기존 .claude 백업
        if (self.project_root / '.claude').exists():
            backup = self.project_root / f'.claude.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.move(self.project_root / '.claude', backup)
            print(f"   ✓ 기존 .claude → {backup}")
        
        # 새 .claude 적용
        if (self.project_root / '.claude.new').exists():
            shutil.move(self.project_root / '.claude.new', self.project_root / '.claude')
            print(f"   ✓ 새 .claude 적용됨")
        
        # 새 MCP 설정 적용
        if (self.project_root / '.mcp.json.new').exists():
            if (self.project_root / '.mcp.json').exists():
                shutil.move(self.project_root / '.mcp.json', 
                           self.project_root / f'.mcp.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.move(self.project_root / '.mcp.json.new', self.project_root / '.mcp.json')
            print(f"   ✓ MCP 설정 적용됨")

def main():
    print("🚀 Claude 설정 통합 도구 v1.0")
    print("=" * 50)
    
    consolidator = ClaudeConsolidator()
    
    # 1. 스캔
    consolidator.scan_all_claude_folders()
    
    # 2. 수집
    skills = consolidator.collect_all_skills()
    commands = consolidator.collect_all_commands()
    mcp_config = consolidator.consolidate_mcp_configs()
    
    # 3. 통합
    new_claude_dir = consolidator.create_unified_structure(skills, commands, mcp_config)
    
    # 4. 리포트
    consolidator.generate_report()
    
    # 5. 적용 확인
    print("\n" + "=" * 50)
    print("✅ 분석 및 통합 완료!")
    print("\n새로운 구조가 .claude.new에 생성되었습니다.")
    
    confirm = input("\n변경사항을 적용하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        consolidator.apply_changes()
        
        # 6. 정리
        cleanup = input("\n중복 폴더를 삭제하시겠습니까? (y/n): ")
        if cleanup.lower() == 'y':
            consolidator.cleanup_duplicates()
        
        print("\n✨ 모든 작업 완료!")
        print("\n다음 단계:")
        print("1. Claude Code 재시작")
        print("2. 스킬이 자동으로 로드됩니다")
    else:
        print("\n변경사항이 적용되지 않았습니다.")
        print(".claude.new 폴더를 직접 확인하실 수 있습니다.")

if __name__ == "__main__":
    main()
