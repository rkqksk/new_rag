# Crawling Agent

**Purpose**: Dedicated agent for web crawling and data acquisition

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent with integrated MCP servers for efficient web crawling and data extraction.

### Key Features

- ✅ **Multi-strategy crawling** (Static, Dynamic, API)
- ✅ **Integrated MCP servers** (Puppeteer, Fetch, Chrome DevTools)
- ✅ **Authentication support** (Manual 2FA, TOTP, API Keys)
- ✅ **Anti-bot evasion** (User-Agent rotation, proxies)
- ✅ **robots.txt handling** (Respect/Ignore/Bypass)
- ✅ **Session management** (Cookie persistence)

---

## 🚀 Usage

### Direct Agent Invocation

```bash
# Use advanced-data-acquisition skill with this agent
/advanced-data-acquisition crawl --url=https://example.com
```

### Tools Available

This agent has access to:
- `StaticCrawler` - BeautifulSoup-based
- `DynamicCrawler` - Playwright-based
- `MultiStrategyCrawler` - Auto-detection
- `ManualAuthHandler` - Browser login
- `RobotsHandler` - robots.txt
- `AntiDetectionManager` - Evasion
- `SessionManager` - Cookies

---

## 🔧 MCP Servers

### Enabled by Default

| Server | Purpose | Priority |
|--------|---------|----------|
| **puppeteer** | Browser automation | High |
| **fetch** | HTTP requests | High |
| **filesystem** | File operations | High |
| **chrome-devtools** | Browser debugging | Medium |

### Optional (Requires API Key)

| Server | Purpose | Setup |
|--------|---------|-------|
| **tavily** | AI search | Set `TAVILY_API_KEY` |

---

## ⚙️ Configuration

Located in `agent.json`:

```json
{
  "config": {
    "max_concurrent_requests": 5,
    "default_timeout": 30,
    "rate_limit": {
      "max_requests": 10,
      "time_window": 60
    },
    "anti_detection": {
      "enabled": true,
      "min_delay": 2.0,
      "max_delay": 5.0
    },
    "robots_policy": "respect"
  }
}
```

---

## 📊 Performance

- ✅ **27 tests passing**
- ✅ **Tested with real websites**
- ✅ **Production-ready**

---

## 📚 Related

- Skill: `advanced-data-acquisition`
- Skill: `web-scraping-expert`
- Docs: `docs/CRAWLING_PRACTICAL_GUIDE.md`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
