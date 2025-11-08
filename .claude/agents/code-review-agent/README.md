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

- `github` - GitHub API integration
- `filesystem` - File operations

---

## 🔧 MCP Servers

| Server | Purpose | Cost |
|--------|---------|------|
| **github** | GitHub API | $0/month (unlimited for public repos) |
| **filesystem** | File operations | $0/month |

**Total Cost**: $0/month

---

## ⚙️ Configuration

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
**Last Updated**: 2025-11-08
