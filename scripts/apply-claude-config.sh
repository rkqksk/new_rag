#!/bin/bash
# Claude 프로젝트 설정 적용 스크립트

echo "🚀 Claude RAG Enterprise 설정 적용 중..."

# 현재 디렉토리 확인
PROJECT_ROOT=$(pwd)
echo "📁 프로젝트 루트: $PROJECT_ROOT"

# Python 경로 확인
PYTHON_PATH="/Users/oypnus/Project/rag-enterprise/.direnv/python-3.11/bin/python3"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "⚠️  Python 경로를 찾을 수 없습니다. 기본 python3 사용"
    PYTHON_PATH="python3"
fi

# 기존 설정 백업
if [ -d ".claude" ] && [ ! -d ".claude.backup.$(date +%Y%m%d)" ]; then
    echo "📦 기존 설정 백업 중..."
    cp -r .claude .claude.backup.$(date +%Y%m%d_%H%M%S)
fi

# .claude-v3 관리 도구 실행
if [ -f ".claude-v3/manager.py" ]; then
    echo "🔧 관리 도구로 설정 생성 중..."
    $PYTHON_PATH .claude-v3/manager.py setup
else
    echo "⚠️  관리 도구를 찾을 수 없습니다. 수동 설정 진행..."
    
    # 수동으로 디렉토리 생성
    mkdir -p .claude/skills
    mkdir -p .claude/commands  
    mkdir -p .claude/agents
    mkdir -p .claude-plugin
    
    # 기본 MCP 설정 생성
    cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
EOF
    
    # 기본 settings.local.json 생성
    cat > .claude/settings.local.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Read(./**)",
      "Bash(python *)"
    ]
  },
  "enableAllProjectMcpServers": true
}
EOF
fi

# 스킬 존재 확인
echo ""
echo "📦 설치된 스킬 확인:"
if [ -d ".claude/skills" ]; then
    for skill in .claude/skills/*/; do
        if [ -f "${skill}SKILL.md" ]; then
            skill_name=$(basename "$skill")
            echo "   ✅ $skill_name"
        fi
    done
else
    echo "   ⚠️  스킬이 설치되지 않았습니다"
fi

# 검증
echo ""
echo "🔍 설정 검증:"

check_file() {
    if [ -f "$1" ]; then
        echo "   ✅ $1"
        return 0
    else
        echo "   ❌ $1"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "   ✅ $1/"
        return 0
    else
        echo "   ❌ $1/"
        return 1
    fi
}

all_valid=true
check_file ".mcp.json" || all_valid=false
check_file ".claude/settings.local.json" || all_valid=false
check_dir ".claude/skills" || all_valid=false
check_dir ".claude-plugin" || all_valid=false

echo ""
if [ "$all_valid" = true ]; then
    echo "✅ 모든 설정이 성공적으로 적용되었습니다!"
    echo ""
    echo "다음 단계:"
    echo "1. Claude Code를 재시작하세요"
    echo "2. 스킬이 자동으로 로드됩니다"
    echo "3. 'RAG 문서 처리' 또는 '벡터 검색' 관련 작업시 스킬이 활성화됩니다"
else
    echo "⚠️  일부 설정이 누락되었습니다. 수동으로 확인이 필요합니다."
fi

echo ""
echo "💡 팁: 다른 프로젝트로 이식하려면:"
echo "   cp -r .claude /path/to/new-project/"
echo "   cp .mcp.json /path/to/new-project/"
