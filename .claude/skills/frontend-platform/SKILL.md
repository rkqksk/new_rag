# Frontend Platform Skill

**Purpose**: Unified frontend architecture with minimal monochrome design system for enterprise SaaS platform.

**Version**: 1.0.0 (v5.0.0 Platform)
**Status**: Design-ready ✅

---

## 🎯 Skill Overview

This skill provides complete frontend architecture covering:
- **Design System**: Minimal monochrome palette (gray scale)
- **Authentication UI**: Login, registration, password reset
- **Dashboard**: Tenant overview, usage metrics, billing
- **RAG Interface**: Chat UI, search results, recommendations
- **Admin Panel**: Tenant management, system monitoring

**Design Philosophy**:
- 🎨 **Monochrome**: Single-color gradients (grays) with minimal accents
- 📐 **Minimal**: Clean layouts, ample whitespace, focused content
- 🔗 **Cohesive**: Shared components, consistent patterns
- ⚡ **Fast**: Vanilla JS/lightweight frameworks, minimal dependencies

**Use this skill when:**
- Building login/registration pages
- Creating tenant dashboards
- Designing RAG chat interfaces
- Implementing admin panels
- Establishing design system

**Architecture Reference**: §ui.* symbols → `docs/FRONTEND_UI_POLICY.md`

---

## 📋 Available Commands

### 1. `design-system`
**Description**: Generate design system tokens and documentation

**Usage**:
```bash
design-system [--output <dir>]
```

**Generates**:
- `colors.css` - Monochrome color palette
- `typography.css` - Font system
- `spacing.css` - Spacing scale
- `components.css` - Base component styles

**Example**:
```bash
design-system --output frontend/styles/
```

**Output** (`colors.css`):
```css
:root {
  /* Monochrome Palette (Gray Scale) */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f7f7f8;
  --color-bg-tertiary: #ececf1;

  --color-text-primary: #2d333a;
  --color-text-secondary: #6e6e80;
  --color-text-tertiary: #8e8ea0;

  --color-border: #d1d5db;
  --color-border-hover: #9ca3af;

  /* Accent (minimal) */
  --color-accent: #10a37f;
  --color-accent-hover: #0d8968;

  /* States */
  --color-error: #ef4444;
  --color-success: #10b981;
  --color-warning: #f59e0b;
}
```

---

### 2. `create-page`
**Description**: Generate page templates (login, dashboard, chat)

**Usage**:
```bash
create-page <page-type> [options]
```

**Page Types**:
- `login` - Login/registration page
- `dashboard` - Tenant dashboard
- `chat` - RAG chat interface
- `admin` - Admin panel
- `billing` - Billing/subscription page

**Options**:
- `--standalone` - Self-contained HTML file
- `--components` - Split into components
- `--framework <name>` - React/Vue/Vanilla (default: vanilla)

**Example**:
```bash
# Standalone login page
create-page login --standalone

# Dashboard with components
create-page dashboard --components

# Chat interface (React)
create-page chat --framework react
```

---

### 3. `component`
**Description**: Generate reusable UI components

**Usage**:
```bash
component <component-name> [options]
```

**Available Components**:
- `button` - Primary/secondary buttons
- `input` - Text inputs, textareas
- `card` - Content cards
- `modal` - Modal dialogs
- `navbar` - Navigation bar
- `sidebar` - Side navigation
- `table` - Data tables
- `chart` - Usage charts

**Example**:
```bash
# Generate button component
component button

# Generate card with variants
component card --variants="default,elevated,outline"
```

---

### 4. `layout`
**Description**: Generate layout templates

**Usage**:
```bash
layout <layout-type>
```

**Layout Types**:
- `auth` - Centered auth form (login/register)
- `dashboard` - Sidebar + main content
- `fullscreen` - Full-screen chat interface
- `split` - Two-column layout

**Example**:
```bash
# Auth layout
layout auth

# Dashboard layout with sidebar
layout dashboard
```

---

## 🎨 Design System

### Color Palette (Monochrome)

```
Backgrounds:
├─ Primary:   #ffffff (white)
├─ Secondary: #f7f7f8 (very light gray)
└─ Tertiary:  #ececf1 (light gray)

Text:
├─ Primary:   #2d333a (dark gray, high contrast)
├─ Secondary: #6e6e80 (medium gray)
└─ Tertiary:  #8e8ea0 (light gray, subtle)

Borders:
├─ Default: #d1d5db (gray)
└─ Hover:   #9ca3af (darker gray)

Accent (minimal usage):
└─ Primary: #10a37f (teal, for CTAs only)

States:
├─ Error:   #ef4444 (red)
├─ Success: #10b981 (green)
└─ Warning: #f59e0b (amber)
```

**Philosophy**: 95% grayscale, 5% accent for critical actions

### Typography

```
Font Stack:
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
             Roboto, Helvetica, Arial, sans-serif;

Hierarchy:
├─ h1: 32px/40px, 600 weight, -0.02em letter-spacing
├─ h2: 24px/32px, 600 weight, -0.01em letter-spacing
├─ h3: 20px/28px, 600 weight
├─ body: 16px/24px, 400 weight
├─ small: 14px/20px, 400 weight
└─ tiny: 12px/16px, 400 weight

Line Height: 1.5 (body), 1.2 (headings)
```

### Spacing Scale

```
--space-0: 0px
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-6: 24px
--space-8: 32px
--space-12: 48px
--space-16: 64px
```

### Component Styles

**Button**:
```css
.btn-primary {
  background: var(--color-accent);
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  padding: 12px 24px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
}
```

**Card**:
```css
.card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--space-6);
}

.card-elevated {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**Input**:
```css
.input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-size: 16px;
}

.input:focus {
  outline: none;
  border-color: var(--color-accent);
}
```

---

## 📄 Page Templates

### 1. Login Page

**Layout**: Centered card on plain background

```html
<!DOCTYPE html>
<html>
<head>
  <title>Login - RAG Enterprise</title>
  <link rel="stylesheet" href="styles/design-system.css">
</head>
<body class="auth-page">
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">Welcome back</h1>
      <p class="auth-subtitle">Sign in to your account</p>

      <form class="auth-form">
        <div class="form-group">
          <label>Email</label>
          <input type="email" class="input" placeholder="you@company.com">
        </div>

        <div class="form-group">
          <label>Password</label>
          <input type="password" class="input" placeholder="••••••••">
        </div>

        <button type="submit" class="btn-primary btn-full">
          Sign in
        </button>
      </form>

      <div class="auth-footer">
        <a href="/register">Don't have an account? Sign up</a>
      </div>
    </div>
  </div>
</body>
</html>
```

**Styles** (`auth.css`):
```css
.auth-page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: var(--space-4);
}

.auth-card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: var(--space-8);
}

.auth-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: var(--space-2);
}

.auth-subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-6);
}
```

---

### 2. Dashboard

**Layout**: Sidebar + main content + header

```html
<!DOCTYPE html>
<html>
<head>
  <title>Dashboard - RAG Enterprise</title>
  <link rel="stylesheet" href="styles/design-system.css">
</head>
<body class="dashboard-page">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>RAG Enterprise</h2>
    </div>

    <nav class="sidebar-nav">
      <a href="/dashboard" class="nav-item active">
        Overview
      </a>
      <a href="/search" class="nav-item">
        Search
      </a>
      <a href="/usage" class="nav-item">
        Usage
      </a>
      <a href="/billing" class="nav-item">
        Billing
      </a>
      <a href="/settings" class="nav-item">
        Settings
      </a>
    </nav>
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    <!-- Header -->
    <header class="page-header">
      <h1>Overview</h1>
      <div class="header-actions">
        <button class="btn-secondary">Account</button>
      </div>
    </header>

    <!-- Content -->
    <div class="content-area">
      <!-- Stats Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">API Calls (This Month)</div>
          <div class="stat-value">45,230</div>
          <div class="stat-change">+12% from last month</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Quota Usage</div>
          <div class="stat-value">45.2%</div>
          <div class="stat-change">45,230 / 100,000</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Storage</div>
          <div class="stat-value">12.5 GB</div>
          <div class="stat-change">25% of 50 GB</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Current Plan</div>
          <div class="stat-value">Pro</div>
          <div class="stat-change">$49/month</div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card">
        <h3>Recent Activity</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Endpoint</th>
              <th>Method</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>/api/v1/search</td>
              <td>POST</td>
              <td><span class="badge-success">200</span></td>
              <td>2 min ago</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</body>
</html>
```

**Styles** (`dashboard.css`):
```css
.dashboard-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg-secondary);
}

.sidebar {
  width: 240px;
  background: var(--color-bg-primary);
  border-right: 1px solid var(--color-border);
  padding: var(--space-6);
}

.sidebar-nav .nav-item {
  display: block;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.2s;
}

.sidebar-nav .nav-item.active {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  font-weight: 500;
}

.main-content {
  flex: 1;
  padding: var(--space-6);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--space-6);
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: var(--space-1);
}

.stat-change {
  font-size: 14px;
  color: var(--color-text-tertiary);
}
```

---

### 3. Chat Interface (RAG)

**Layout**: Full-screen chat with message list + input

```html
<!DOCTYPE html>
<html>
<head>
  <title>Search - RAG Enterprise</title>
  <link rel="stylesheet" href="styles/design-system.css">
</head>
<body class="chat-page">
  <div class="chat-container">
    <!-- Chat Header -->
    <header class="chat-header">
      <h2>Product Search</h2>
      <button class="btn-secondary">New Chat</button>
    </header>

    <!-- Messages -->
    <div class="chat-messages">
      <div class="message user-message">
        <div class="message-content">
          50ml PET bottle with pump dispenser
        </div>
      </div>

      <div class="message assistant-message">
        <div class="message-content">
          I found 3 products matching your query:

          <div class="product-card">
            <h4>50ml PET Bottle - Code: A001</h4>
            <p>Capacity: 50ml | Material: PET</p>
            <p>MOQ: 10,000 units | Price: $0.25</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-container">
      <textarea
        class="chat-input"
        placeholder="Search for products..."
        rows="1"
      ></textarea>
      <button class="btn-primary">Send</button>
    </div>
  </div>
</body>
</html>
```

**Styles** (`chat.css`):
```css
.chat-page {
  min-height: 100vh;
  background: var(--color-bg-secondary);
}

.chat-container {
  max-width: 768px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.message {
  margin-bottom: var(--space-4);
}

.message-content {
  padding: var(--space-4);
  border-radius: 12px;
  max-width: 80%;
}

.user-message .message-content {
  background: var(--color-bg-tertiary);
  margin-left: auto;
}

.assistant-message .message-content {
  background: var(--color-bg-secondary);
}

.chat-input-container {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: var(--space-2);
}

.chat-input {
  flex: 1;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  resize: none;
}
```

---

## 🔧 Component Library

### Button Variants

```html
<!-- Primary (accent color, for main actions) -->
<button class="btn-primary">Sign in</button>

<!-- Secondary (gray, for secondary actions) -->
<button class="btn-secondary">Cancel</button>

<!-- Outline (transparent with border) -->
<button class="btn-outline">Learn more</button>

<!-- Text only (no background) -->
<button class="btn-text">Forgot password?</button>

<!-- Full width -->
<button class="btn-primary btn-full">Continue</button>
```

### Form Inputs

```html
<!-- Text input -->
<div class="form-group">
  <label class="form-label">Email</label>
  <input type="email" class="input" placeholder="you@company.com">
</div>

<!-- Textarea -->
<div class="form-group">
  <label class="form-label">Message</label>
  <textarea class="input" rows="4"></textarea>
</div>

<!-- Select -->
<div class="form-group">
  <label class="form-label">Plan</label>
  <select class="input">
    <option>Free</option>
    <option>Pro</option>
    <option>Enterprise</option>
  </select>
</div>
```

### Cards

```html
<!-- Basic card -->
<div class="card">
  <h3>Card Title</h3>
  <p>Card content goes here.</p>
</div>

<!-- Elevated card (with shadow) -->
<div class="card card-elevated">
  <h3>Important Info</h3>
  <p>This card stands out with a shadow.</p>
</div>

<!-- Interactive card (hover effect) -->
<div class="card card-interactive">
  <h3>Clickable Card</h3>
  <p>Hover to see effect.</p>
</div>
```

---

## 💡 Best Practices

### Color Usage

```css
/* ✅ Good: Minimal accent usage */
.cta-button {
  background: var(--color-accent);  /* Only for primary CTAs */
}

.page-content {
  background: var(--color-bg-primary);  /* White/gray for content */
  color: var(--color-text-primary);      /* Dark gray for text */
}

/* ❌ Avoid: Too many colors */
.bad-example {
  background: blue;
  color: red;
  border: 2px solid green;  /* Too colorful! */
}
```

### Typography

```css
/* ✅ Good: Clear hierarchy */
h1 { font-size: 32px; font-weight: 600; }
h2 { font-size: 24px; font-weight: 600; }
p  { font-size: 16px; font-weight: 400; }

/* ❌ Avoid: Similar sizes */
h1 { font-size: 20px; }
h2 { font-size: 19px; }  /* Too close! */
```

### Spacing

```css
/* ✅ Good: Consistent spacing scale */
.section { padding: var(--space-8); }
.card { margin-bottom: var(--space-4); }

/* ❌ Avoid: Random pixel values */
.bad { padding: 17px; margin: 23px; }  /* Not on scale! */
```

### Layout

```css
/* ✅ Good: Max-width for readability */
.content {
  max-width: 768px;
  margin: 0 auto;
}

/* ❌ Avoid: Full-width text */
.bad-text {
  width: 100%;  /* Too wide on large screens */
}
```

---

## 📚 References

### Progressive Disclosure
- **Quick Start**: This file (SKILL.md) - ~500 lines
- **Design System**: `references/design_system.md` - Complete tokens
- **Components**: `references/components.md` - All component specs
- **Examples**: `examples/page_templates.md` - Full page examples

### Symbol Navigation
- `§ui.design` - Design system tokens
- `§ui.version` - Current version (v2.0.0)
- `§ui.components` - Component library

### Full Documentation
- **Frontend UI Policy**: `docs/FRONTEND_UI_POLICY.md`
- **Design System**: `.claude/skills/frontend-platform/references/`

---

## 🚀 Quick Start

### 1. Generate Design System

```bash
design-system --output frontend/styles/
```

### 2. Create Login Page

```bash
create-page login --standalone
```

### 3. Create Dashboard

```bash
create-page dashboard --components
```

### 4. Add Components

```bash
component button
component card
component input
```

---

## 📊 Design Checklist

Before shipping:
- [ ] All colors from monochrome palette
- [ ] Accent color used sparingly (<5% of UI)
- [ ] Typography follows scale (16px base)
- [ ] Spacing uses scale (4px, 8px, 12px, etc.)
- [ ] Max-width applied to content (768px)
- [ ] Consistent border-radius (6-12px)
- [ ] Hover states on interactive elements
- [ ] Focus states on form inputs
- [ ] Responsive breakpoints (mobile, tablet, desktop)
- [ ] Accessible contrast ratios (WCAG AA)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Maintainer**: RAG Enterprise Platform Team
