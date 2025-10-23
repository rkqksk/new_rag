# Makefile - RAG Enterprise 개발 단축 명령어

.PHONY: help max api profile status

help: ## 사용 가능한 명령어 목록 표시
	@echo "RAG Enterprise - Make Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

max: ## MCP 프로필을 max로 전환 (7개 서버, 전체 기능)
	@echo "🚀 Switching to MAX profile..."
	@./scripts/switch_mcp_profile.sh max
	@echo ""
	@echo "✅ Done! Restart Claude Code to apply changes."

api: ## MCP 프로필을 api로 전환 (4개 서버, 경량)
	@echo "🔌 Switching to API profile..."
	@./scripts/switch_mcp_profile.sh api
	@echo ""
	@echo "✅ Done! Restart Claude Code to apply changes."

profile: ## 현재 활성 MCP 프로필 확인
	@echo "📋 Current MCP Profile:"
	@echo "======================"
	@if [ -f .mcp.profile.current ]; then \
		echo "Active: $$(cat .mcp.profile.current)"; \
	else \
		echo "No profile marker found"; \
	fi
	@echo ""
	@echo "Configuration (.mcp.json):"
	@grep -A1 "_comment" .mcp.json | head -2

status: ## 프로젝트 상태 확인 (Docker, services)
	@echo "🔍 Project Status"
	@echo "================="
	@echo ""
	@echo "Docker Containers:"
	@docker-compose ps 2>/dev/null || echo "  Docker Compose not running"
	@echo ""
	@echo "MCP Profile:"
	@make profile --no-print-directory
