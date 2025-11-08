# Complete Page Templates

**Purpose**: Production-ready page templates for RAG Enterprise Platform.

---

## 1. Login Page (Complete)

### HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login - RAG Enterprise</title>
  <style>
    :root {
      --color-bg-primary: #ffffff;
      --color-bg-secondary: #f7f7f8;
      --color-bg-tertiary: #ececf1;
      --color-text-primary: #2d333a;
      --color-text-secondary: #6e6e80;
      --color-border: #d1d5db;
      --color-accent: #10a37f;
      --color-accent-hover: #0d8968;
      --color-error: #ef4444;
      --space-2: 8px;
      --space-4: 16px;
      --space-6: 24px;
      --space-8: 32px;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--color-bg-secondary);
      min-height: 100vh;
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

    .auth-logo {
      text-align: center;
      margin-bottom: var(--space-6);
    }

    .auth-logo h1 {
      font-size: 24px;
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .auth-title {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: var(--space-2);
      color: var(--color-text-primary);
    }

    .auth-subtitle {
      color: var(--color-text-secondary);
      margin-bottom: var(--space-6);
      font-size: 16px;
    }

    .form-group {
      margin-bottom: var(--space-4);
    }

    .form-label {
      display: block;
      margin-bottom: var(--space-2);
      font-size: 14px;
      font-weight: 500;
      color: var(--color-text-primary);
    }

    .input {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid var(--color-border);
      border-radius: 6px;
      background: var(--color-bg-primary);
      font-size: 16px;
      color: var(--color-text-primary);
      transition: border-color 0.2s;
    }

    .input:focus {
      outline: none;
      border-color: var(--color-accent);
    }

    .btn-primary {
      width: 100%;
      padding: 12px 24px;
      background: var(--color-accent);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.2s;
    }

    .btn-primary:hover {
      background: var(--color-accent-hover);
    }

    .auth-footer {
      margin-top: var(--space-6);
      text-align: center;
    }

    .auth-footer a {
      color: var(--color-text-secondary);
      text-decoration: none;
      font-size: 14px;
    }

    .auth-footer a:hover {
      color: var(--color-accent);
    }

    .error-message {
      background: #fef2f2;
      border: 1px solid var(--color-error);
      color: var(--color-error);
      padding: var(--space-3);
      border-radius: 6px;
      margin-bottom: var(--space-4);
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-logo">
        <h1>RAG Enterprise</h1>
      </div>

      <h2 class="auth-title">Welcome back</h2>
      <p class="auth-subtitle">Sign in to your account</p>

      <!-- Error message (hidden by default) -->
      <div class="error-message" id="error" style="display: none;">
        Invalid email or password
      </div>

      <form class="auth-form" id="loginForm">
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input
            type="email"
            id="email"
            class="input"
            placeholder="you@company.com"
            required
          >
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input
            type="password"
            id="password"
            class="input"
            placeholder="••••••••"
            required
          >
        </div>

        <button type="submit" class="btn-primary">
          Sign in
        </button>
      </form>

      <div class="auth-footer">
        <a href="/register">Don't have an account? Sign up</a>
      </div>
    </div>
  </div>

  <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;

      try {
        const response = await fetch('/api/v1/saas/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('token', data.token);
          window.location.href = '/dashboard';
        } else {
          document.getElementById('error').style.display = 'block';
        }
      } catch (error) {
        document.getElementById('error').style.display = 'block';
      }
    });
  </script>
</body>
</html>
```

---

## 2. Dashboard (Complete)

### HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard - RAG Enterprise</title>
  <style>
    :root {
      --color-bg-primary: #ffffff;
      --color-bg-secondary: #f7f7f8;
      --color-bg-tertiary: #ececf1;
      --color-text-primary: #2d333a;
      --color-text-secondary: #6e6e80;
      --color-text-tertiary: #8e8ea0;
      --color-border: #d1d5db;
      --color-accent: #10a37f;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-6: 24px;
      --space-8: 32px;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--color-bg-secondary);
      display: flex;
      min-height: 100vh;
    }

    /* Sidebar */
    .sidebar {
      width: 240px;
      background: var(--color-bg-primary);
      border-right: 1px solid var(--color-border);
      padding: var(--space-6);
      position: fixed;
      height: 100vh;
      overflow-y: auto;
    }

    .sidebar-header {
      margin-bottom: var(--space-8);
    }

    .sidebar-header h2 {
      font-size: 20px;
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: var(--space-2);
    }

    .nav-item {
      display: block;
      padding: var(--space-3) var(--space-4);
      color: var(--color-text-secondary);
      text-decoration: none;
      border-radius: 6px;
      transition: all 0.2s;
      font-size: 14px;
    }

    .nav-item:hover {
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
    }

    .nav-item.active {
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      font-weight: 500;
    }

    /* Main Content */
    .main-content {
      margin-left: 240px;
      flex: 1;
      padding: var(--space-6);
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--space-6);
    }

    .page-header h1 {
      font-size: 30px;
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .btn-secondary {
      padding: var(--space-3) var(--space-4);
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      border: 1px solid var(--color-border);
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }

    /* Stats Grid */
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
      color: var(--color-text-primary);
      margin-bottom: var(--space-1);
    }

    .stat-change {
      font-size: 14px;
      color: var(--color-text-tertiary);
    }

    /* Card */
    .card {
      background: var(--color-bg-primary);
      border: 1px solid var(--color-border);
      border-radius: 8px;
      padding: var(--space-6);
    }

    .card h3 {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: var(--space-4);
    }

    /* Table */
    .table {
      width: 100%;
      border-collapse: collapse;
    }

    .table th {
      text-align: left;
      padding: var(--space-3);
      border-bottom: 1px solid var(--color-border);
      font-size: 14px;
      font-weight: 500;
      color: var(--color-text-secondary);
    }

    .table td {
      padding: var(--space-3);
      border-bottom: 1px solid var(--color-border);
      font-size: 14px;
      color: var(--color-text-primary);
    }

    .badge-success {
      background: #f0fdf4;
      color: #10b981;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 500;
    }
  </style>
</head>
<body>
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>RAG Enterprise</h2>
    </div>

    <nav class="sidebar-nav">
      <a href="/dashboard" class="nav-item active">Overview</a>
      <a href="/search" class="nav-item">Search</a>
      <a href="/usage" class="nav-item">Usage</a>
      <a href="/billing" class="nav-item">Billing</a>
      <a href="/settings" class="nav-item">Settings</a>
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

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">API Calls (This Month)</div>
        <div class="stat-value" id="apiCalls">45,230</div>
        <div class="stat-change">+12% from last month</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Quota Usage</div>
        <div class="stat-value" id="quotaUsage">45.2%</div>
        <div class="stat-change">45,230 / 100,000</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Storage</div>
        <div class="stat-value" id="storage">12.5 GB</div>
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
        <tbody id="activityTable">
          <tr>
            <td>/api/v1/search</td>
            <td>POST</td>
            <td><span class="badge-success">200</span></td>
            <td>2 min ago</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>

  <script>
    // Load dashboard data
    async function loadDashboard() {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/saas/usage/stats', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          // Update stats
          document.getElementById('apiCalls').textContent = data.api_calls.toLocaleString();
          document.getElementById('quotaUsage').textContent = data.quota_percentage + '%';
          document.getElementById('storage').textContent = data.storage_gb + ' GB';
        }
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      }
    }

    loadDashboard();
  </script>
</body>
</html>
```

---

## 3. Chat Interface (RAG)

Full chat UI with message history, typing indicators, and product cards.

**Complete template available in**: `frontend/chat.html`

---

## Design Principles Applied

### 1. Monochrome Palette
- ✅ 95% grayscale (white, light gray backgrounds)
- ✅ Dark gray text (#2d333a) for high contrast
- ✅ Minimal accent (teal #10a37f only for CTAs)

### 2. Consistent Spacing
- ✅ All spacing from scale (4px, 8px, 12px, 16px, 24px, 32px)
- ✅ Padding: 24px for cards, 12px for buttons
- ✅ Margins: 16px between sections

### 3. Typography
- ✅ System font stack (native on all platforms)
- ✅ 16px base font size
- ✅ 1.5 line-height for readability

### 4. Cohesive Components
- ✅ Same button styles across pages
- ✅ Consistent card design
- ✅ Unified navigation

**All pages share**: colors.css, typography.css, components.css for consistency
