# Data Agent

**Purpose**: Database operations and data management with PostgreSQL and SQLite

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for database operations, SQL queries, and data management.

### Key Features

- ✅ **PostgreSQL** (production database)
- ✅ **SQLite** (local cache)
- ✅ **SQL queries** and analysis
- ✅ **Schema management**
- ✅ **Data migration**

---

## 🚀 Usage

### Via Task Tool

```python
# Launch data agent for database operations
task = Task(
    subagent_type="data-agent",
    prompt="Analyze user activity data from PostgreSQL"
)
```

### Tools Available

- `postgres` - Production database
- `sqlite` - Local cache
- `filesystem` - Data import/export

---

## 🔧 MCP Servers

| Server | Purpose | Cost |
|--------|---------|------|
| **postgres** | Production database | $0/month (software) + server costs |
| **sqlite** | Local cache | $0/month |
| **filesystem** | File operations | $0/month |

**Total Cost**: $0/month (software only)

---

## ⚙️ Configuration

### PostgreSQL Setup

```bash
# Set connection string
export POSTGRES_URL="postgresql://user:password@localhost:5432/rag_enterprise"
```

### SQLite Setup

```bash
# Create cache database
mkdir -p data
touch data/cache.db
```

---

## 📚 Related

- Agent: `crawling-agent`
- Skill: `saas-platform`
- Docs: `docs/SAAS_ARCHITECTURE.md`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
