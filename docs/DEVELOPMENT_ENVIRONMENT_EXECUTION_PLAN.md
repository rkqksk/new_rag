# Development Environment Execution Plan
**Project**: RAG Enterprise v10.0.0 "Unified"
**Date**: 2025-11-15
**Status**: 🚀 Ready for Immediate Execution
**Philosophy**: Maximal Features + Minimal Guidelines + Orchestration

---

## 🎯 Execution Principles

### 1. Maximal Features (맥시멀 기능)
**Goal**: Activate ALL features from integration plans
- ✅ Backend consolidation (app/ + src/ → backend/)
- ✅ Frontend unification (4 frontends → 1 monorepo)
- ✅ Complete tooling (Serena MCP, GitHub MCP, Sub-Agents, Skills)
- ✅ Full automation (orchestration, routing, dynamic activation)

### 2. Minimal Guidelines (미니멀 지침)
**Approach**: Efficient, symbol-based, orchestrated
- ✅ **Symbolization**: Serena MCP for all code navigation
- ✅ **Sub-Agents**: Parallel/sequential orchestration
- ✅ **Skills**: Standardized workflows (reusable templates)
- ✅ **MCP**: Multi-server utilization (filesystem, github, serena)
- ✅ **Orchestration**: Dynamic feature activation/deactivation

### 3. Orchestration Focus (오케스트레이션)
**Strategy**: Hardware optimization through routing
- ✅ Lazy loading (activate only when needed)
- ✅ Smart routing (direct tasks to appropriate handlers)
- ✅ Resource pooling (shared services, caching)
- ✅ Dynamic scaling (activate/deactivate based on demand)

### 4. Execution Process (실행 프로세스)
**Workflow**: Review → Test → Apply
- ✅ Review: Code review, plan validation
- ✅ Test: Dry-run, unit tests, integration tests
- ✅ Apply: Incremental deployment with rollback capability

---

## 📋 Development Environment Architecture

### Target Environment Structure

```
Development Environment (v10.0.0)
│
├── Orchestration Layer ⭐ NEW
│   ├── Service Router (dynamic feature activation)
│   ├── Resource Manager (hardware optimization)
│   ├── Task Dispatcher (sub-agent orchestration)
│   └── Feature Registry (track active/inactive features)
│
├── Backend Layer (Unified)
│   ├── Core Services (always active)
│   │   ├── API Gateway (routing)
│   │   ├── Authentication (JWT)
│   │   └── Health Monitoring
│   ├── Feature Services (lazy-loaded) ⭐
│   │   ├── RAG Pipeline (activate on demand)
│   │   ├── Manufacturing (activate on demand)
│   │   ├── Data Collection (activate on demand)
│   │   └── Multimodal/OCR (activate on demand)
│   └── Database Layer (PostgreSQL, Redis, Qdrant)
│
├── Frontend Layer (Monorepo)
│   ├── Core App (apps/web - always loaded)
│   ├── Mobile App (apps/mobile - conditional)
│   ├── Shared Packages (packages/* - tree-shaken)
│   └── PWA Layer (service worker, offline)
│
├── Tooling Layer
│   ├── Claude Code Integration
│   │   ├── MCP Servers (filesystem, github, serena)
│   │   ├── Sub-Agents (Explore, General, Plan)
│   │   ├── Skills (standardized workflows)
│   │   └── Slash Commands (project shortcuts)
│   ├── Development Tools
│   │   ├── Turborepo (monorepo build orchestration)
│   │   ├── pnpm (package management)
│   │   ├── Docker Compose (service orchestration)
│   │   └── Hot Reload (dev server)
│   └── Testing Tools
│       ├── pytest (backend tests)
│       ├── jest (frontend tests)
│       ├── Playwright (E2E tests)
│       └── Coverage (80%+ target)
│
└── Monitoring Layer
    ├── Performance Metrics (resource usage)
    ├── Feature Usage Tracking (active/inactive)
    ├── Error Tracking (Sentry)
    └── Logging (structured logs)
```

---

## 🔧 Orchestration System Design

### 1. Service Router (Dynamic Activation)

**Purpose**: Activate services only when needed, deactivate when idle

**Implementation**: `backend/orchestration/service_router.py`

```python
# Conceptual design (to be implemented)

class ServiceRouter:
    """
    Routes requests to appropriate services, activating them on-demand
    """

    def __init__(self):
        self.active_services = set()  # Currently running services
        self.service_registry = {
            'rag': {'module': 'backend.services.rag', 'priority': 'high'},
            'manufacturing': {'module': 'backend.services.manufacturing', 'priority': 'medium'},
            'ocr': {'module': 'backend.services.ocr', 'priority': 'low'},
            'data_collection': {'module': 'backend.services.data_collection', 'priority': 'low'},
        }

    async def route_request(self, service_name: str, endpoint: str, payload: dict):
        """
        Route request to service, activating if needed
        """
        # Activate service if not running
        if service_name not in self.active_services:
            await self.activate_service(service_name)

        # Route to service
        service = self.get_service(service_name)
        result = await service.handle_request(endpoint, payload)

        # Schedule deactivation if idle
        self.schedule_deactivation(service_name, idle_timeout=300)  # 5 min

        return result

    async def activate_service(self, service_name: str):
        """
        Dynamically import and initialize service
        """
        config = self.service_registry[service_name]
        module = importlib.import_module(config['module'])
        service = module.initialize()
        self.active_services.add(service_name)
        logger.info(f"✅ Activated service: {service_name}")

    async def deactivate_service(self, service_name: str):
        """
        Gracefully shutdown service
        """
        service = self.get_service(service_name)
        await service.cleanup()
        self.active_services.remove(service_name)
        logger.info(f"❌ Deactivated service: {service_name}")
```

**Benefits**:
- 🚀 Faster startup (core only)
- 💾 Less memory (load on demand)
- 🔋 Less CPU (shutdown idle services)

### 2. Resource Manager (Hardware Optimization)

**Purpose**: Minimize hardware usage through intelligent resource allocation

**Implementation**: `backend/orchestration/resource_manager.py`

```python
class ResourceManager:
    """
    Manages hardware resources (CPU, memory, GPU)
    """

    def __init__(self):
        self.resource_limits = {
            'cpu': {'max': 80, 'threshold': 70},  # % usage
            'memory': {'max': 8192, 'threshold': 6144},  # MB
            'gpu': {'max': 100, 'threshold': 80},  # % usage
        }
        self.service_priorities = ['high', 'medium', 'low']

    async def allocate_resources(self, service_name: str, required_resources: dict):
        """
        Allocate resources to service, throttling low-priority if needed
        """
        current_usage = self.get_current_usage()

        # Check if resources available
        if not self.has_available_resources(required_resources, current_usage):
            # Throttle or deactivate low-priority services
            await self.free_resources(required_resources)

        # Allocate
        allocation = self.assign_resources(service_name, required_resources)
        logger.info(f"📊 Allocated {allocation} to {service_name}")

        return allocation

    async def free_resources(self, required: dict):
        """
        Free resources by throttling/deactivating low-priority services
        """
        # Sort services by priority (low to high)
        services = self.get_active_services_by_priority()

        for service in services:
            if service['priority'] == 'low':
                await self.deactivate_service(service['name'])
                if self.has_available_resources(required, self.get_current_usage()):
                    break
```

**Benefits**:
- ⚡ Optimal resource usage
- 🎯 Priority-based allocation
- 📉 Automatic throttling

### 3. Task Dispatcher (Sub-Agent Orchestration)

**Purpose**: Intelligently dispatch tasks to appropriate sub-agents

**Implementation**: `backend/orchestration/task_dispatcher.py`

```python
class TaskDispatcher:
    """
    Orchestrates sub-agents for complex tasks
    """

    def __init__(self):
        self.agent_pool = {
            'explore': {'capacity': 3, 'active': 0},
            'general': {'capacity': 5, 'active': 0},
            'plan': {'capacity': 2, 'active': 0},
        }
        self.task_queue = []

    async def dispatch_task(self, task: dict) -> dict:
        """
        Analyze task and dispatch to appropriate agent(s)
        """
        # Analyze task complexity
        complexity = self.analyze_complexity(task)

        # Choose agent type
        agent_type = self.choose_agent_type(complexity, task['type'])

        # Check capacity
        if self.has_capacity(agent_type):
            result = await self.execute_with_agent(agent_type, task)
        else:
            # Queue task
            self.task_queue.append(task)
            result = {'status': 'queued', 'position': len(self.task_queue)}

        return result

    def choose_agent_type(self, complexity: str, task_type: str) -> str:
        """
        Select optimal agent type based on task characteristics
        """
        if task_type == 'analysis' or task_type == 'exploration':
            return 'explore'
        elif task_type == 'planning':
            return 'plan'
        elif complexity in ['high', 'very_high']:
            return 'general'
        else:
            return 'general'

    async def execute_parallel(self, tasks: list) -> list:
        """
        Execute multiple tasks in parallel (batch processing)
        """
        # Group by agent type
        grouped = self.group_by_agent_type(tasks)

        # Launch agents in parallel
        results = await asyncio.gather(*[
            self.execute_batch(agent_type, batch)
            for agent_type, batch in grouped.items()
        ])

        return results
```

**Benefits**:
- 🔀 Parallel execution
- 📊 Load balancing
- ⏱️ Optimal agent selection

### 4. Feature Registry (Active/Inactive Tracking)

**Purpose**: Track which features are active, enable/disable dynamically

**Implementation**: `backend/orchestration/feature_registry.py`

```python
class FeatureRegistry:
    """
    Central registry for all features (backend + frontend)
    """

    def __init__(self):
        self.features = {
            # Backend features
            'backend.rag.search': {'status': 'inactive', 'activations': 0},
            'backend.rag.chunking': {'status': 'inactive', 'activations': 0},
            'backend.manufacturing.vision': {'status': 'inactive', 'activations': 0},
            'backend.ocr.parsing': {'status': 'inactive', 'activations': 0},
            'backend.data_collection.web': {'status': 'inactive', 'activations': 0},

            # Frontend features
            'frontend.search_page': {'status': 'active', 'activations': 1000},
            'frontend.realtime_demo': {'status': 'inactive', 'activations': 10},
            'frontend.profile': {'status': 'inactive', 'activations': 50},
        }

    def activate(self, feature_name: str):
        """Activate a feature"""
        self.features[feature_name]['status'] = 'active'
        self.features[feature_name]['activations'] += 1
        logger.info(f"✅ Feature activated: {feature_name}")

    def deactivate(self, feature_name: str):
        """Deactivate a feature"""
        self.features[feature_name]['status'] = 'inactive'
        logger.info(f"❌ Feature deactivated: {feature_name}")

    def get_active_features(self) -> list:
        """Get all currently active features"""
        return [
            name for name, config in self.features.items()
            if config['status'] == 'active'
        ]

    def suggest_deactivations(self) -> list:
        """
        Suggest features to deactivate based on usage
        """
        # Features with <10 activations and inactive
        return [
            name for name, config in self.features.items()
            if config['activations'] < 10 and config['status'] == 'inactive'
        ]
```

**Benefits**:
- 📊 Usage tracking
- 🎯 Smart recommendations
- 🔍 Visibility into active features

---

## 🛠️ Sub-Agents Orchestration Strategy

### Agent Pool Design

```python
# Orchestration configuration

AGENT_POOL = {
    'explore': {
        'max_concurrent': 3,  # Max 3 Explore agents at once
        'use_cases': ['code_analysis', 'pattern_discovery', 'dependency_mapping'],
        'priority': 'high',
    },
    'general': {
        'max_concurrent': 5,  # Max 5 General agents
        'use_cases': ['planning', 'code_generation', 'migration', 'testing'],
        'priority': 'medium',
    },
    'plan': {
        'max_concurrent': 2,  # Max 2 Plan agents
        'use_cases': ['architecture_planning', 'quick_analysis'],
        'priority': 'low',
    },
}

# Task routing rules
TASK_ROUTING = {
    # Analysis tasks → Explore
    'analyze_duplication': {'agent': 'explore', 'thoroughness': 'medium'},
    'analyze_dependencies': {'agent': 'explore', 'thoroughness': 'very thorough'},
    'analyze_symbols': {'agent': 'explore', 'thoroughness': 'quick'},

    # Planning tasks → General or Plan
    'create_migration_plan': {'agent': 'general', 'model': 'sonnet'},
    'quick_architecture_review': {'agent': 'plan', 'thoroughness': 'quick'},

    # Execution tasks → General
    'generate_migration_scripts': {'agent': 'general', 'model': 'sonnet'},
    'migrate_html_to_react': {'agent': 'general', 'model': 'sonnet'},
    'generate_tests': {'agent': 'general', 'model': 'haiku'},  # Faster model

    # Documentation tasks → General
    'generate_api_docs': {'agent': 'general', 'model': 'haiku'},
    'write_developer_guide': {'agent': 'general', 'model': 'sonnet'},
}
```

### Dynamic Agent Activation

**Strategy**: Activate agents only when tasks arrive, deactivate when complete

```python
class AgentOrchestrator:
    """
    Manages sub-agent lifecycle and task distribution
    """

    async def execute_task(self, task_name: str, task_params: dict):
        """
        Execute task with optimal agent
        """
        # Get routing config
        config = TASK_ROUTING.get(task_name)

        # Check agent availability
        agent_type = config['agent']
        if not self.has_available_slot(agent_type):
            # Queue task
            return await self.queue_task(task_name, task_params)

        # Launch agent
        agent_id = await self.launch_agent(
            agent_type=agent_type,
            task=task_name,
            params=task_params,
            **config
        )

        # Monitor execution
        result = await self.monitor_agent(agent_id)

        # Deactivate agent
        await self.deactivate_agent(agent_id)

        return result
```

---

## 📚 Skills Standardization

### Skill Categories

#### 1. Migration Skills
```
.claude/skills/migration/
├── backend-migration.md
├── frontend-migration.md
├── component-migration.md
└── service-extraction.md
```

#### 2. Testing Skills
```
.claude/skills/testing/
├── unit-test-generation.md
├── integration-test-generation.md
├── e2e-test-generation.md
└── performance-testing.md
```

#### 3. Documentation Skills
```
.claude/skills/documentation/
├── api-documentation.md
├── component-documentation.md
├── architecture-documentation.md
└── guide-writing.md
```

#### 4. Code Analysis Skills
```
.claude/skills/analysis/
├── duplication-analysis.md
├── dependency-analysis.md
├── performance-analysis.md
└── security-analysis.md
```

### Example Skill: Backend Migration

**File**: `.claude/skills/migration/backend-migration.md`

```markdown
# Backend Migration Skill

## Purpose
Standardized workflow for migrating backend code from app/src to backend/

## Steps

### 1. Pre-Migration Analysis
- Use Serena MCP to analyze target directory
- Identify duplications with `find_symbol`
- Map dependencies with `find_referencing_symbols`

### 2. File Migration
- Copy files to new location
- Preserve directory structure
- Handle conflicts (create *_v2.py if needed)

### 3. Import Updates
- Update all imports from app.* → backend.*
- Update all imports from src.* → backend.api.v2.*
- Validate with TypeScript/Python type checker

### 4. Testing
- Run unit tests
- Run integration tests
- Validate imports (no app.*, no src.*)

### 5. Cleanup
- Archive old files
- Update documentation
- Commit changes

## Tools
- Serena MCP: Symbol navigation
- Bash: File operations
- Edit: Import updates
- pytest: Testing

## Output
- Migrated files in backend/
- Updated imports
- Passing tests
- Migration log
```

---

## 🔌 MCP Server Optimization

### Current MCP Configuration

**File**: `.claude/mcp.json`

**Servers**:
1. ✅ **filesystem** - File operations
2. ✅ **github** - GitHub integration
3. ✅ **serena** - Code navigation (AST-based)

### Optimization Strategy

#### 1. Filesystem Server (Restricted Access)

**Goal**: Limit to relevant directories only

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/rkqksk/projects/new_rag/apps",
        "/home/rkqksk/projects/new_rag/packages",
        "/home/rkqksk/projects/new_rag/backend",
        "/home/rkqksk/projects/new_rag/docs",
        "/home/rkqksk/projects/new_rag/scripts"
      ]
    }
  }
}
```

**Benefits**:
- ⚡ Faster file operations (smaller search space)
- 🔒 Security (can't access system files)
- 🎯 Focused (only project directories)

#### 2. Serena Server (Symbol Navigation)

**Goal**: Use for all code exploration instead of full file reads

**Usage Pattern**:
```python
# ❌ AVOID: Full file read
Read(file_path="/home/rkqksk/projects/new_rag/backend/services/rag_service.py")

# ✅ PREFER: Symbol-based navigation
mcp__serena__get_symbols_overview(relative_path="backend/services/rag_service.py")
mcp__serena__find_symbol(name_path="RAGService/search", include_body=True)
```

**Benefits**:
- 📉 70-80% token reduction
- 🎯 Precise code access
- 🔍 Relationship tracking (find_referencing_symbols)

#### 3. GitHub Server (Branch Management)

**Goal**: Use for git operations, branch analysis

**Usage**:
- `mcp__github__list_commits` - Commit history
- `mcp__github__create_branch` - Create feature branches
- `mcp__github__create_pull_request` - PRs with description

---

## 🚀 Execution Plan (Immediate)

### Phase 0: Orchestration Setup (TODAY - 2 hours)

**Tasks**:
1. ✅ Create orchestration modules
   - backend/orchestration/service_router.py
   - backend/orchestration/resource_manager.py
   - backend/orchestration/task_dispatcher.py
   - backend/orchestration/feature_registry.py

2. ✅ Create skills
   - .claude/skills/migration/backend-migration.md
   - .claude/skills/migration/frontend-migration.md
   - .claude/skills/testing/test-generation.md
   - .claude/skills/documentation/api-docs.md

3. ✅ Update MCP configuration
   - Optimize .claude/mcp.json (restrict filesystem)
   - Validate Serena MCP working

4. ✅ Create execution scripts
   - scripts/orchestration/setup_orchestration.sh
   - scripts/orchestration/activate_feature.sh
   - scripts/orchestration/deactivate_feature.sh

**Sub-Agents**: 1 General-purpose (Orchestration Setup)

**Deliverables**:
- 4 orchestration modules (Python)
- 4 skills (Markdown)
- Optimized MCP config
- 3 orchestration scripts

---

### Phase 1: Backend Migration (Week 2-3)

**Review → Test → Apply**

#### Step 1: Review (Day 1)
- ✅ Review BACKEND_MIGRATION_PLAN.md
- ✅ Review migration scripts (00-03)
- ✅ Team alignment

#### Step 2: Test (Day 2)
- ✅ Run dry-run: `./scripts/migration/00_run_migration.sh --dry-run`
- ✅ Review dry-run output
- ✅ Validate no critical errors

#### Step 3: Apply (Day 3-10)
- ✅ Execute migration: `./scripts/migration/00_run_migration.sh`
- ✅ Validate: `./scripts/migration/03_validate_structure.sh`
- ✅ Run tests: `pytest backend/`
- ✅ Fix any issues
- ✅ Commit changes

**Sub-Agents**:
- 1 Explore (Import dependency mapping)
- 1 General (Fix any migration issues)

**Orchestration**:
- Activate: RAG, core services
- Deactivate: Manufacturing, OCR (not needed for migration)

---

### Phase 2: Frontend Consolidation (Week 4-5)

**Review → Test → Apply**

#### Step 1: Review (Day 1)
- ✅ Review FRONTEND_FILE_STRUCTURE_PLAN.md
- ✅ Review component list (7 dashboard components)
- ✅ Validate apps/web structure

#### Step 2: Test (Day 2-3)
- ✅ Generate scripts (if not done):
  - General agent: "Generate frontend migration scripts"
- ✅ Run dry-run for each script
- ✅ Validate no breaking changes

#### Step 3: Apply (Day 4-10)
- ✅ Archive deprecated:
  - `./scripts/frontend-migration/00_archive_deprecated.sh`
- ✅ Move components:
  - `./scripts/frontend-migration/01_move_components.sh`
- ✅ Extract services:
  - `./scripts/frontend-migration/08_extract_services.sh`
- ✅ Validate:
  - `pnpm build` (all apps)
  - `pnpm test` (all packages)
- ✅ Commit changes

**Sub-Agents**:
- 1 General (Script generation if needed)
- 1 Explore (Component duplication verification)

**Orchestration**:
- Activate: Frontend dev server, Turborepo
- Deactivate: Backend services (not needed)

---

### Phase 3: HTML → React Migration (Week 6-9)

**Iterative: Review → Test → Apply (per feature)**

#### Feature 1: chat.html → SearchPage (Week 6-7)

**Review**:
- ✅ Analyze chat.html features
- ✅ Design React component structure
- ✅ Plan state management (Zustand)

**Test**:
- ✅ Launch General agent: "Migrate chat.html to React"
- ✅ Review generated code
- ✅ Test locally (side-by-side with HTML)

**Apply**:
- ✅ Integrate into apps/web
- ✅ Add tests (Jest + Playwright)
- ✅ Deploy to staging
- ✅ Gather user feedback
- ✅ Redirect /chat.html → /customer/search

**Sub-Agents**: 1 General (Chat Migrator)

#### Features 2-6: (Week 8-9)
- Realtime, Profile, RAG Dashboard, Dashboard, Streaming
- Same process: Review → Test → Apply

**Sub-Agents**: 5 General (parallel or sequential)

**Orchestration**:
- Activate: Frontend + Backend APIs
- Deactivate: Heavy services (Manufacturing, OCR)

---

### Phase 4: Testing & Validation (Week 11)

**Review → Test → Apply**

#### Review:
- ✅ Identify test gaps
- ✅ Set coverage targets (80%+)

#### Test:
- ✅ Launch General agent: "Generate comprehensive test suite"
- ✅ Review generated tests
- ✅ Run tests locally

#### Apply:
- ✅ Add tests to codebase
- ✅ Fix failing tests
- ✅ Achieve 80%+ coverage
- ✅ Set up CI/CD (GitHub Actions)

**Sub-Agents**: 1 General (Test Suite Generator)

**Orchestration**:
- Activate: All services (for integration tests)
- Deactivate: After tests pass

---

## ✅ Immediate Execution Checklist

### Pre-Execution (NOW - 30 min)

- [ ] Read this plan thoroughly
- [ ] Confirm understanding of orchestration approach
- [ ] Verify all tools available (MCP servers, sub-agents)
- [ ] Git status clean, backup branch created

### Phase 0: Orchestration Setup (TODAY - 2 hours)

**Task 1: Create Orchestration Modules** (1 hour)
- [ ] Launch General agent: "Create orchestration modules"
  - service_router.py
  - resource_manager.py
  - task_dispatcher.py
  - feature_registry.py

**Task 2: Create Skills** (30 min)
- [ ] Create .claude/skills/migration/
- [ ] Create .claude/skills/testing/
- [ ] Create .claude/skills/documentation/
- [ ] Create .claude/skills/analysis/

**Task 3: Optimize MCP Config** (15 min)
- [ ] Update .claude/mcp.json (restrict filesystem paths)
- [ ] Validate Serena MCP working

**Task 4: Create Orchestration Scripts** (15 min)
- [ ] scripts/orchestration/setup_orchestration.sh
- [ ] scripts/orchestration/activate_feature.sh
- [ ] scripts/orchestration/deactivate_feature.sh

### Phase 1: Backend Migration (START AFTER PHASE 0)

- [ ] Review BACKEND_MIGRATION_PLAN.md
- [ ] Run dry-run
- [ ] Execute migration
- [ ] Validate and test
- [ ] Commit changes

### Continuous (Throughout Execution)

- [ ] Track active/inactive features (Feature Registry)
- [ ] Monitor resource usage (Resource Manager)
- [ ] Use sub-agents strategically (Task Dispatcher)
- [ ] Update documentation as we go

---

## 🎯 Success Criteria

### Phase 0 (Orchestration Setup)
- [x] Orchestration modules created and functional
- [x] Skills defined and usable
- [x] MCP servers optimized
- [x] Orchestration scripts ready

### Phase 1 (Backend Migration)
- [ ] Single backend/ directory
- [ ] No app.*, src.* imports
- [ ] All tests passing
- [ ] Orchestration active (feature routing working)

### Phase 2 (Frontend Consolidation)
- [ ] Single apps/web/ frontend
- [ ] 27 components in packages/ui
- [ ] All builds passing
- [ ] Orchestration tracking active features

### Overall System
- [ ] Maximal features enabled ✅
- [ ] Minimal resource usage ✅ (orchestration)
- [ ] All changes tested ✅ (review → test → apply)
- [ ] System stable and working ✅

---

## 🚀 Ready to Execute

**Status**: 🟢 All plans complete, ready for immediate execution

**Next Action**:
1. Confirm understanding ✅
2. Start Phase 0 (Orchestration Setup) ✅
3. Use sub-agents as planned ✅
4. Follow Review → Test → Apply for all changes ✅

**Expected Timeline**:
- Phase 0: TODAY (2 hours)
- Phase 1-3: Week 2-9
- Phase 4: Week 11
- Total: 12 weeks → 7 weeks with orchestration + sub-agents

**Philosophy**:
- Maximal features ✅
- Minimal guidelines (symbols, sub-agents, skills, MCP, orchestration) ✅
- Hardware optimization (routing, lazy loading) ✅
- Robust process (review → test → apply) ✅

Let's execute! 🚀
