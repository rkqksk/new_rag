---
name: debugging-expert
description: Debugging Expert Skill
---

# Debugging Expert Skill

**Version**: 1.0.0
**Status**: Production Ready ✅
**Purpose**: AI-powered browser debugging using Chrome DevTools MCP integration

> **Live browser debugging expertise** - AI agents can control and inspect real Chrome instances for debugging, testing, performance optimization, and automated QA.

---

## Quick Reference

### Commands

```bash
# Browser Control
debug launch                                    # Launch Chrome with DevTools connection
debug navigate <url>                            # Navigate to URL
debug screenshot <path>                         # Capture screenshot
debug reload                                    # Reload current page

# DOM Inspection
debug inspect <selector>                        # Inspect element by selector
debug query <selector>                          # Query DOM elements
debug highlight <selector>                      # Highlight element visually
debug get-html <selector>                       # Get element HTML
debug get-styles <selector>                     # Get computed CSS styles

# Console & JavaScript
debug console-log                               # Read console output
debug execute-js <code>                         # Execute JavaScript in page context
debug evaluate <expression>                     # Evaluate expression and return result

# Network Debugging
debug network-log                               # View network requests
debug analyze-cors                              # Analyze CORS issues
debug check-blocked-resources                   # Find blocked resources (CSP, 404, etc.)
debug simulate-offline                          # Test offline behavior

# Performance Analysis
debug record-performance <duration>             # Record performance trace
debug analyze-core-vitals                       # Check Core Web Vitals (LCP, FID, CLS)
debug lighthouse-audit                          # Run Lighthouse performance audit
debug memory-profile                            # Analyze memory usage

# Automated Testing
debug test-user-flow <steps>                    # Simulate user interactions
debug verify-fix <scenario>                     # Verify bug fix in live browser
debug regression-test <test-cases>              # Run regression tests
```

---

## Core Capabilities

### 1. Chrome DevTools MCP Integration

**What is Chrome DevTools MCP?**

The Chrome DevTools Model Context Protocol server lets AI agents:
- **Control a live Chrome browser** - Navigate, click, scroll, submit forms
- **Inspect DOM & CSS** - Read HTML structure, computed styles, layout
- **Execute JavaScript** - Run code in page context, manipulate DOM
- **Read Console** - Access console.log(), errors, warnings
- **Monitor Network** - Track requests, analyze CORS, detect blocked resources
- **Profile Performance** - Record traces, analyze Core Web Vitals
- **Automate User Flows** - Simulate real user behavior

**Why This Matters for AI Agents**:

Traditional AI coding assistants are "blind" - they generate code but can't see what it does in the browser. Chrome DevTools MCP solves this by giving AI agents **vision** - they can:

1. **Debug visually** - See actual rendering, not just code
2. **Test automatically** - Verify fixes work in real browser
3. **Catch regressions** - Detect layout breaks, performance issues
4. **Optimize performance** - Measure and improve Core Web Vitals
5. **Fix browser-specific bugs** - Test in real Chrome environment

**Requirements**:
- Node.js ≥ 22
- Chrome browser (latest version)
- MCP-compatible AI client (Claude Code, Cursor, GitHub Copilot)

---

### 2. DOM Inspection & Manipulation

**Inspect Element**:
```javascript
// AI can inspect any element
debug inspect ".error-message"

// Returns:
{
  "tagName": "div",
  "className": "error-message",
  "textContent": "Invalid email address",
  "computedStyle": {
    "color": "rgb(220, 53, 69)",
    "fontSize": "14px",
    "display": "block"
  },
  "boundingBox": { "x": 100, "y": 200, "width": 300, "height": 40 }
}
```

**Query DOM**:
```javascript
// Find all buttons
debug query "button"

// Find form inputs
debug query "input[type='email']"

// Find elements by text content
debug query "*:contains('Submit')"
```

**Execute JavaScript**:
```javascript
// Change DOM
debug execute-js "document.querySelector('.modal').style.display = 'none'"

// Trigger events
debug execute-js "document.querySelector('#submit-btn').click()"

// Get values
debug evaluate "document.querySelectorAll('.product').length"
// Returns: 24
```

**Use Cases**:
- Verify element rendering
- Check CSS application
- Test JavaScript interactions
- Validate form behavior
- Debug layout issues

---

### 3. Console Debugging

**Read Console Output**:
```javascript
// AI can read all console messages
debug console-log

// Returns:
[
  { level: "log", text: "App initialized", timestamp: 1699564123 },
  { level: "warn", text: "Deprecated API usage", timestamp: 1699564125 },
  { level: "error", text: "Failed to fetch /api/data", timestamp: 1699564130 }
]
```

**Identify Errors**:
```javascript
// Filter by error level
debug console-log --level error

// Returns:
[
  {
    level: "error",
    text: "Uncaught TypeError: Cannot read property 'name' of undefined",
    source: "app.js:42",
    stackTrace: "at fetchUser (app.js:42)\nat init (app.js:10)"
  }
]
```

**Debug Workflow**:
1. Navigate to page with bug
2. Read console for errors
3. Inspect error source in code
4. Propose fix
5. Apply fix and reload
6. Verify error is gone

**Real Example**:
```
User Report: "Clicking 'Add to Cart' shows error"

AI Debugging Steps:
1. debug navigate "https://example.com/product/123"
2. debug execute-js "document.querySelector('.add-to-cart').click()"
3. debug console-log --level error
   → Error: "Cannot read property 'price' of undefined"
4. debug inspect ".product-price"
   → Element not found! Missing price element
5. Diagnosis: Frontend expects price, but API didn't return it
6. Fix: Add null check before accessing product.price
```

---

### 4. Network Debugging

**Monitor Requests**:
```javascript
// AI can see all network activity
debug network-log

// Returns:
[
  {
    url: "https://api.example.com/products",
    method: "GET",
    status: 200,
    responseTime: 145ms,
    size: "24.5 KB"
  },
  {
    url: "https://cdn.example.com/image.jpg",
    method: "GET",
    status: 404,
    responseTime: 52ms
  }
]
```

**Analyze CORS Issues**:
```javascript
debug analyze-cors

// Returns:
{
  corsErrors: [
    {
      url: "https://api.other-domain.com/data",
      error: "No 'Access-Control-Allow-Origin' header present",
      fix: "Add CORS headers on server: Access-Control-Allow-Origin: *"
    }
  ]
}
```

**Find Blocked Resources**:
```javascript
debug check-blocked-resources

// Returns:
{
  blockedResources: [
    { url: "/old-script.js", reason: "404 Not Found" },
    { url: "https://analytics.com/track.js", reason: "Blocked by CSP" },
    { url: "/api/old-endpoint", reason: "CORS error" }
  ],
  recommendations: [
    "Remove reference to /old-script.js from HTML",
    "Update CSP policy to allow analytics.com",
    "Update API endpoint to /api/v2/endpoint"
  ]
}
```

**Test Offline Behavior**:
```javascript
// Simulate offline mode
debug simulate-offline

// Verify offline fallback
debug navigate "https://example.com"
debug screenshot "offline-state.png"

// Return online
debug simulate-online
```

---

### 5. Performance Optimization

**Record Performance Trace**:
```javascript
// AI can profile page load
debug record-performance 5s

// Returns detailed trace:
{
  "duration": 5000ms,
  "metrics": {
    "FCP": 1200ms,  // First Contentful Paint
    "LCP": 2400ms,  // Largest Contentful Paint
    "TTI": 3200ms,  // Time to Interactive
    "TBT": 150ms,   // Total Blocking Time
    "CLS": 0.05     // Cumulative Layout Shift
  },
  "bottlenecks": [
    {
      "type": "Long Task",
      "duration": 250ms,
      "source": "bundle.js:1234",
      "suggestion": "Split long task into smaller chunks"
    }
  ]
}
```

**Analyze Core Web Vitals**:
```javascript
debug analyze-core-vitals

// Returns:
{
  "LCP": {
    "value": 2.4s,
    "rating": "Good",  // < 2.5s
    "element": "img.hero-image",
    "recommendation": "Preload hero image with <link rel='preload'>"
  },
  "FID": {
    "value": 85ms,
    "rating": "Needs Improvement",  // 100-300ms
    "suggestion": "Reduce JavaScript execution time"
  },
  "CLS": {
    "value": 0.05,
    "rating": "Good",  // < 0.1
    "sources": []
  }
}
```

**Lighthouse Audit**:
```javascript
debug lighthouse-audit

// Returns comprehensive audit:
{
  "performance": 92/100,
  "accessibility": 88/100,
  "bestPractices": 95/100,
  "seo": 90/100,
  "opportunities": [
    {
      "title": "Eliminate render-blocking resources",
      "savings": "450ms",
      "fix": "Defer non-critical CSS and JavaScript"
    },
    {
      "title": "Properly size images",
      "savings": "120 KB",
      "fix": "Use responsive images with srcset"
    }
  ]
}
```

**Memory Profiling**:
```javascript
debug memory-profile

// Returns:
{
  "heapSize": "45 MB",
  "leaks": [
    {
      "type": "Detached DOM nodes",
      "count": 127,
      "source": "carousel.js:45",
      "fix": "Remove event listeners before deleting elements"
    }
  ]
}
```

---

### 6. Automated Testing & QA

**Simulate User Flow**:
```javascript
// AI can simulate real user interactions
debug test-user-flow [
  "navigate https://example.com",
  "click #login-button",
  "type #email 'user@example.com'",
  "type #password 'password123'",
  "click #submit",
  "wait-for .dashboard",
  "screenshot login-success.png"
]

// Returns:
{
  "success": true,
  "steps": 7,
  "duration": 2.3s,
  "screenshots": ["login-success.png"]
}
```

**Verify Bug Fix**:
```javascript
// Test that a fix actually works
debug verify-fix {
  scenario: "Form submission with empty email",
  steps: [
    "navigate https://example.com/contact",
    "type #name 'John Doe'",
    "type #email ''",  // Empty email
    "click #submit"
  ],
  expected: "Error message should appear",
  verify: "querySelector('.error-message').textContent includes 'Email required'"
}

// Returns:
{
  "passed": true,
  "actualResult": "Error message: 'Email is required'",
  "screenshot": "error-validation.png"
}
```

**Regression Testing**:
```javascript
// Run multiple test cases
debug regression-test [
  {
    name: "Login flow",
    steps: ["navigate /login", "type #email 'test@example.com'", ...],
    expected: "Dashboard loads"
  },
  {
    name: "Add to cart",
    steps: ["navigate /products", "click .add-to-cart", ...],
    expected: "Cart counter increments"
  },
  {
    name: "Checkout process",
    steps: ["navigate /cart", "click #checkout", ...],
    expected: "Payment page loads"
  }
]

// Returns:
{
  "totalTests": 3,
  "passed": 2,
  "failed": 1,
  "failures": [
    {
      "test": "Add to cart",
      "error": "Cart counter did not increment",
      "screenshot": "failed-cart-test.png"
    }
  ]
}
```

---

## Advanced Use Cases

### 1. Visual Regression Testing

```javascript
// Baseline screenshot
debug navigate "https://example.com"
debug screenshot "baseline.png"

// After code changes
debug navigate "https://example.com"
debug screenshot "current.png"

// AI compares screenshots visually
// Reports: "Layout shifted 10px down, button color changed from blue to green"
```

### 2. Cross-Browser Bug Reproduction

```javascript
// User reports: "Button doesn't work in Chrome"
debug launch chrome
debug navigate "https://example.com"
debug execute-js "document.querySelector('#broken-button').click()"
debug console-log --level error

// AI finds:
// Error: "event.srcElement is not a function"
// Diagnosis: Using IE-specific API (srcElement) instead of standard (target)
// Fix: Replace event.srcElement with event.target
```

### 3. Performance Bottleneck Identification

```javascript
// User complains: "Page is slow"
debug navigate "https://example.com"
debug record-performance 10s

// AI analyzes trace and finds:
// - JavaScript bundle is 2.5 MB (blocking main thread for 800ms)
// - 47 images loaded before viewport (wasted bandwidth)
// - No code splitting (entire app loaded upfront)

// AI suggests:
// 1. Enable code splitting → Save 600ms TTI
// 2. Lazy-load below-fold images → Save 1.2s LCP
// 3. Use CDN for static assets → Save 200ms
```

### 4. Accessibility Debugging

```javascript
debug navigate "https://example.com"

// Check keyboard navigation
debug execute-js "document.activeElement.tagName"
debug execute-js "document.querySelectorAll('[tabindex]').length"

// Check ARIA labels
debug query "[aria-label='']"  // Empty ARIA labels
debug query "img:not([alt])"   // Images without alt text

// Check color contrast
debug evaluate "getComputedStyle(document.querySelector('.text')).color"
debug evaluate "getComputedStyle(document.querySelector('.text')).backgroundColor"
// AI calculates contrast ratio and warns if < 4.5:1
```

---

## Integration with Other Skills

**frontend-platform** + debugging-expert:
- Build UI with shadcn-ui components
- Test in live browser with DevTools
- Debug layout issues visually
- Optimize performance

**web-scraping-expert** + debugging-expert:
- Scrape dynamic JavaScript sites
- Debug why scraping fails
- Handle dynamic content loading
- Bypass anti-bot measures

**production-expert** + debugging-expert:
- Monitor production site health
- Debug customer-reported issues
- Performance monitoring
- Real user monitoring (RUM)

---

## Best Practices

### 1. Always Test in Real Browser
- Code that works in theory may fail in practice
- Browser quirks (CORS, CSP, cookies) only appear in real environment
- Visual bugs (layout, responsive design) need actual rendering

### 2. Use Screenshots for Evidence
- Capture before/after screenshots
- Document visual regressions
- Share with team for review
- Attach to bug reports

### 3. Performance First
- Measure before optimizing
- Focus on Core Web Vitals
- Test on slow networks (throttle to 3G)
- Profile mobile devices

### 4. Automate Regression Tests
- Create test suites for critical flows
- Run before each deployment
- Catch bugs early
- Build confidence in releases

---

## MCP Integration

**Chrome DevTools MCP** → Live browser debugging, performance profiling, automated testing

**Key Features Enabled**:
- Real-time DOM inspection
- Console output reading
- Network request monitoring
- Performance trace recording
- User interaction automation
- Screenshot capture
- JavaScript execution

---

## Troubleshooting

**Node.js Version Too Old**:
```bash
# Check version
node --version

# Required: ≥ 22
# Install Node.js 22 via nvm:
nvm install 22
nvm use 22
```

**Chrome Not Found**:
```bash
# Install Chrome
# Ubuntu: apt install google-chrome-stable
# macOS: brew install --cask google-chrome
# Windows: Download from google.com/chrome
```

**Connection Failed**:
```bash
# Ensure Chrome is not already running
# Close all Chrome instances, then retry
```

**Port Already in Use**:
```bash
# Default DevTools port: 9222
# Change port in MCP config if needed
```

---

## Related Skills

- **frontend-platform** - UI development with live testing
- **web-scraping-expert** - Dynamic site scraping with browser control
- **production-expert** - Performance monitoring and optimization

---

**Version**: 1.0.0 | **Status**: Production Ready | **License**: MIT

**Official Docs**: https://developer.chrome.com/blog/chrome-devtools-mcp
**GitHub**: https://github.com/ChromeDevTools/chrome-devtools-mcp
