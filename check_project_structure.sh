#!/bin/bash

# RAG Enterprise 프로젝트 구조 확인 스크립트
# 실행: bash check_project_structure.sh

echo "=========================================="
echo "RAG Enterprise 프로젝트 구조 확인"
echo "=========================================="
echo ""

cd /Users/oypnus/Project/rag-enterprise

echo "📂 .claude 폴더 구조"
echo "===================="
if [ -d ".claude" ]; then
    tree .claude/ -L 3 2>/dev/null || find .claude/ -maxdepth 3 -type f
    echo ""
    
    if [ -d ".claude/skills" ]; then
        echo "🎯 Skills 목록:"
        ls -la .claude/skills/
        echo ""
        
        echo "📄 Skills 내용 미리보기:"
        for skill in .claude/skills/*/; do
            if [ -d "$skill" ]; then
                echo "---"
                echo "Skill: $(basename $skill)"
                if [ -f "${skill}SKILL.md" ]; then
                    head -20 "${skill}SKILL.md"
                fi
                echo ""
            fi
        done
    fi
else
    echo "⚠️  .claude 폴더가 없습니다."
fi

echo ""
echo "🔧 MCP 서버 목록"
echo "================"
if [ -f ".mcp.json" ]; then
    cat .mcp.json | grep -E '"[a-z_]+":' | head -20
else
    echo "⚠️  .mcp.json 파일이 없습니다."
fi

echo ""
echo "🔌 플러그인 목록"
echo "================"
if [ -d "plugins" ]; then
    ls -la plugins/
elif [ -d "rag_plugins" ]; then
    ls -la rag_plugins/
else
    echo "⚠️  plugins 디렉토리가 없습니다."
fi

echo ""
echo "📊 현재 MCP 프로필"
echo "=================="
if [ -f ".mcp.profile.current" ]; then
    cat .mcp.profile.current
else
    echo "⚠️  프로필 파일이 없습니다."
fi

echo ""
echo "=========================================="
echo "확인 완료!"
echo "=========================================="
