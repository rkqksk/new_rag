# Web Scraping Expert Skill

**Purpose**: Advanced web scraping with BeautifulSoup, Playwright, and anti-detection

**Version**: 2.0.0
**Last Updated**: 2025-11-08 (v5.7.1)
**Project**: rag-enterprise

---

## 🎯 Quick Commands

### `scrape`
```bash
/web-scraping-expert scrape --url=<url> [--method=<static|dynamic>] [--robots=<ignore|respect>]
```

### `extract`
```bash
/web-scraping-expert extract --url=<url> --selector=<css_selector> [--multiple]
```

### `monitor`
```bash
/web-scraping-expert monitor --url=<url> --interval=<seconds> --changes=<selector>
```

---

## 🚀 Features

- ✅ Static scraping (BeautifulSoup)
- ✅ Dynamic scraping (Playwright)
- ✅ Manual 2FA login support
- ✅ robots.txt handling (respect/ignore/bypass)
- ✅ Anti-bot evasion
- ✅ Rate limiting
- ✅ Session management

---

## 📋 MCP Servers

This skill uses:
- `puppeteer` - Browser automation
- `fetch` - Web content fetching
- `chrome-devtools` - Live browser debugging
- `tavily` - AI-powered search
- `filesystem` - File operations

---

## 🔧 Configuration

See `.claude/mcp.json` and `advanced-data-acquisition` skill for detailed usage.

---

**Status**: ✅ Production-Ready
