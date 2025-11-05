# Development Guide Loader

**Purpose**: Load development guides with validation.

## Execution Protocol

### Step 1: Validate Request
```
User input: /guide [guide-name]
Example: /guide development
Example: /guide testing
Example: /guide session-protocol
```

### Step 2: Check Available Guides

Available guides:
- `development` → guides/development.md - Development commands, scenarios, tools
- `testing` → guides/testing.md - Testing strategies and tools
- `session-protocol` → guides/session-protocol.md - Session management rules
- `contributing` → guides/contributing.md - Contribution guidelines
- `deployment` → guides/deployment.md - Deployment procedures

### Step 3: Load with Validation

```
1. Check if guide exists using Read tool
2. If exists:
   - Load the guide documentation
   - Answer user's question using loaded context
3. If NOT exists:
   - Show available guides list
   - Ask user to choose from available options
```

### Step 4: Fallback Response Template

If guide not found:

```
❌ Guide '[guide-name]' not found.

Available guides:
1. development - Commands, scenarios, development tools
2. testing - Testing strategies and pytest guide
3. session-protocol - Session start/end protocols
4. contributing - Contribution guidelines and standards
5. deployment - Deployment and production setup

Usage: /guide [guide-name]
Example: /guide development
```

## Success Response

```
✅ Loaded: [Guide Name]
[Answer user's question based on loaded documentation]

💡 Related:
- /workflow [name] - See workflows related to this guide
- /component [type] - Component details
```
