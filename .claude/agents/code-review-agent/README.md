# Code Review Agent

**Purpose**: GitHub integration and automated code review

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for GitHub operations, PR reviews, and code analysis.

### Key Features

- ✅ **Pull request review**
- ✅ **Issue management**
- ✅ **Code analysis**
- ✅ **Repository management**
- ✅ **Automated checks**
- ⭐ **AI-powered testing & debugging** (TestSprite)

---

## 🚀 Usage

### Via Task Tool

```python
# Launch code review agent
task = Task(
    subagent_type="code-review-agent",
    prompt="Review PR #123 and provide feedback"
)
```

### Tools Available

- `testsprite` - ⭐ AI-powered automatic testing & debugging
- `github` - GitHub API integration
- `filesystem` - File operations

---

## 🔧 MCP Servers

| Server | Purpose | Cost | Priority |
|--------|---------|------|----------|
| **testsprite** ⭐ | AI-powered testing & debugging | Free tier available | Critical |
| **github** | GitHub API | $0/month (unlimited for public repos) | High |
| **filesystem** | File operations | $0/month | High |

**Total Cost**: $0/month (with free tiers)

### ⭐ TestSprite Benefits

- **42% → 93% code quality improvement**
- Automatic test case generation
- Smart failure diagnosis
- PRD-based testing
- Cloud-based parallel execution

---

## ⚙️ Configuration

### TestSprite API Key Setup (Recommended) ⭐

```bash
# Get free API key at: https://testsprite.com
export TESTSPRITE_API_KEY="your_api_key_here"

# Or add to .env file
echo "TESTSPRITE_API_KEY=your_api_key_here" >> .env
```

### GitHub Token Setup (Optional)

```bash
# For private repositories only
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."

# Get token at: https://github.com/settings/tokens
# Required scopes: repo, read:org
```

**Note**: Public repositories work without token.

---

## 📚 Related

- Agent: `crawling-agent`
- Skill: `pcb-expert`, `mold-expert`
- Docs: `CONTRIBUTING.md`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-09
**Enhancement**: Added TestSprite MCP for AI-powered code quality validation
