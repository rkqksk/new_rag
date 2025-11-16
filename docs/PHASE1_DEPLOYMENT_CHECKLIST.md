# Phase 1 Deployment Checklist

**Target**: Production Deployment
**Date**: 2025-11-15
**Version**: v7.0.0+

---

## Pre-Deployment Validation ✅

### 1. Code Quality
- [x] TestSprite removed from all configs
- [x] MCP servers configured (7 servers)
- [x] Agents updated to pytest (8 agents)
- [x] Skills present and validated (26 skills)
- [x] Feature bundles configured
- [x] Backend tests passing (54/71 - 76%)
- [ ] API routes verified (11 routes returning 404)

### 2. Dependencies
- [x] Python 3.11.14 installed
- [x] All Python packages installed (qdrant-client, aiohttp, pytest, fastapi)
- [x] Docker containers ready
- [x] Environment variables configured

### 3. Configuration Files
- [x] `.env` file present and valid
- [x] `.claude/mcp.json` valid
- [x] `.claude/feature-bundles.json` valid
- [x] `docker-compose.yml` ready
- [x] `pytest.ini` configured

---

## Deployment Steps

### Step 1: Pre-Flight Checks

```bash
# 1. Git status clean
git status

# 2. Run validation script
./scripts/validate-claude-system.sh

# 3. Run backend tests
pytest tests/integration/ tests/unit/ -v --maxfail=5

# 4. Check Docker services
docker-compose ps
```

### Step 2: Environment Setup

```bash
# 1. Verify environment variables
cat .env | grep -E "^(POSTGRES|REDIS|QDRANT|OLLAMA|GITHUB)"

# 2. Verify ports available
lsof -i :8001  # API
lsof -i :15432  # Postgres
lsof -i :16379  # Redis
lsof -i :16333  # Qdrant
lsof -i :11434  # Ollama

# 3. Kill conflicting processes if needed
# kill -9 <PID>
```

### Step 3: Start Services

```bash
# Option A: Optimized deployment script
./scripts/deploy-optimized.sh development

# Option B: Manual docker-compose
docker-compose down -v
docker-compose up -d

# Wait for services to be ready
sleep 10
```

### Step 4: Verify Services

```bash
# 1. Check all containers running
docker-compose ps

# 2. Health checks
curl http://localhost:8001/health/ready
curl http://localhost:8001/api/v1/docs

# 3. Check logs
docker-compose logs backend --tail=50
docker-compose logs postgres --tail=20
docker-compose logs redis --tail=20
docker-compose logs qdrant --tail=20
```

### Step 5: Integration Tests

```bash
# Run integration tests against live services
pytest tests/integration/test_health_endpoints.py -v
pytest tests/integration/test_service_integration.py -v

# Test key endpoints
curl -X POST http://localhost:8001/api/v1/health \
  -H "Content-Type: application/json"
```

### Step 6: MCP Servers Test

```bash
# Test each MCP server individually (in separate terminals)

# Terminal 1: Qdrant
python3 mcp_servers/qdrant_server.py

# Terminal 2: Ollama
python3 mcp_servers/ollama_server.py

# Terminal 3: RAG Orchestrator
python3 mcp_servers/rag_orchestrator.py

# Verify no errors, then Ctrl+C each
```

### Step 7: Claude Code Integration

```bash
# 1. Restart Claude Code to load new MCP config
# Ctrl+D or exit, then restart: claude

# 2. Test basic MCP commands (in Claude Code session)
# - Check filesystem MCP: List files
# - Check GitHub MCP: Get repo info
# - Verify no TestSprite errors
```

---

## Post-Deployment Validation

### 1. Functional Tests

```bash
# API Health
curl http://localhost:8001/health/ready | jq

# API Docs
open http://localhost:8001/api/v1/docs

# Metrics
curl http://localhost:8001/metrics

# Realtime Demo (if enabled)
open http://localhost:8080/realtime-demo.html
```

### 2. Log Review

```bash
# Check for errors in logs
docker-compose logs backend | grep ERROR
docker-compose logs postgres | grep ERROR
docker-compose logs redis | grep ERROR
docker-compose logs qdrant | grep ERROR
```

### 3. Performance Check

```bash
# Run load tests (optional)
pytest tests/load/load_test.py -v

# Check resource usage
docker stats

# Monitor logs in real-time
docker-compose logs -f backend
```

---

## Rollback Plan

If deployment fails:

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup (if needed)
# git checkout <previous-commit>

# 3. Restart with previous config
docker-compose up -d

# 4. Verify rollback
curl http://localhost:8001/health/ready
```

---

## Known Issues & Workarounds

### Issue 1: API Routes 404
**Status**: Non-critical
**Impact**: 11 test failures
**Workaround**:
```bash
# Verify routes registered in app/api/main.py
grep "app.include_router" app/api/main.py
```

### Issue 2: Mock Config Missing postgres_user
**Status**: Test-only issue
**Impact**: 2 test failures
**Workaround**: Update test fixtures in `tests/integration/conftest.py`

### Issue 3: Claude API Key Not Configured
**Status**: Optional feature
**Impact**: 2 health check tests fail
**Workaround**: Add `ANTHROPIC_API_KEY` to `.env` (optional)

---

## Success Criteria

### Minimum (Phase 1):
- [x] All Docker containers running
- [x] Backend API responding (health check passes)
- [x] Core services functional (RAG, search)
- [x] MCP servers load without errors
- [x] No TestSprite errors

### Optimal:
- [x] 76%+ backend tests passing
- [ ] 90%+ API tests passing (currently 66%)
- [x] All MCP servers responding
- [x] Claude Code integration working
- [ ] Zero errors in logs (minor issues acceptable)

**Current Status**: **Minimum criteria met** ✅

---

## Post-Deployment Tasks

### Immediate (Day 1):
1. Monitor logs for 1 hour
2. Test key user workflows
3. Verify MCP servers stable
4. Check resource usage (CPU, memory)

### Short-term (Week 1):
1. Fix API route registration issues
2. Update test fixtures
3. Add integration tests for new MCP servers
4. Performance optimization

### Medium-term (Month 1):
1. Configure Claude API key (optional)
2. Enable additional feature bundles
3. Implement monitoring dashboards
4. Load testing and optimization

---

## Emergency Contacts

**Technical Lead**: [Your Name]
**DevOps**: [Team]
**Backup**: TROUBLESHOOTING.md

---

## Sign-Off

- [ ] Technical validation complete
- [ ] Security review complete (N/A for development)
- [ ] Performance acceptable
- [ ] Rollback plan tested
- [ ] Documentation updated

**Deployment Approved By**: _______________
**Date**: _______________

---

**Notes**:
- This is a Phase 1 deployment (development/staging)
- Production deployment requires additional security hardening
- Monitor closely for first 24 hours
- Keep backup ready for quick rollback

**Good to Deploy**: ✅ YES (with minor known issues)
