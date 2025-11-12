/**
 * Dark Mode Manager
 * Complete dark theme support with persistence
 * Version: v8.3.0
 */

const STORAGE_KEY = 'dark_mode';
const THEME_ATTR = 'data-theme';

class DarkModeManager {
    constructor() {
        this.isDark = this.loadPreference();
        this.init();
    }

    /**
     * Initialize dark mode
     */
    init() {
        // Apply saved theme
        this.apply(this.isDark);

        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (!this.hasManualPreference()) {
                    this.set(e.matches);
                }
            });
        }
    }

    /**
     * Load saved preference or system preference
     */
    loadPreference() {
        const saved = localStorage.getItem(STORAGE_KEY);

        if (saved !== null) {
            return saved === 'true';
        }

        // Use system preference
        if (window.matchMedia) {
            return window.matchMedia('(prefers-color-scheme: dark)').matches;
        }

        return false;
    }

    /**
     * Check if user has manually set preference
     */
    hasManualPreference() {
        return localStorage.getItem(STORAGE_KEY) !== null;
    }

    /**
     * Set dark mode
     */
    set(isDark) {
        this.isDark = isDark;
        localStorage.setItem(STORAGE_KEY, String(isDark));
        this.apply(isDark);

        // Dispatch event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: {theme: isDark ? 'dark' : 'light'}
        }));
    }

    /**
     * Toggle dark mode
     */
    toggle() {
        this.set(!this.isDark);
    }

    /**
     * Apply theme to document
     */
    apply(isDark) {
        if (isDark) {
            document.documentElement.setAttribute(THEME_ATTR, 'dark');
            document.body.classList.add('dark-mode');
        } else {
            document.documentElement.setAttribute(THEME_ATTR, 'light');
            document.body.classList.remove('dark-mode');
        }
    }

    /**
     * Get current theme
     */
    getTheme() {
        return this.isDark ? 'dark' : 'light';
    }

    /**
     * Is dark mode enabled
     */
    isDarkMode() {
        return this.isDark;
    }

    /**
     * Clear preference (use system default)
     */
    clearPreference() {
        localStorage.removeItem(STORAGE_KEY);
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.set(systemDark);
    }
}

// Global instance
const darkMode = new DarkModeManager();

// Export
window.darkMode = darkMode;

// CSS Variables for Dark Mode
const darkModeStyles = `
<style id="dark-mode-styles">
    [data-theme="dark"] {
        /* Background colors */
        --color-bg-main: #1a1a1a;
        --color-bg-secondary: #2a2a2a;
        --color-bg-input: #333333;
        --color-bg-user: #2d2d2d;
        --color-bg-assistant: #252525;

        /* Text colors */
        --color-text-primary: #e0e0e0;
        --color-text-secondary: #b0b0b0;
        --color-text-placeholder: #808080;

        /* Border colors */
        --color-border: #404040;
        --color-border-focus: #606060;
        --color-hover: #333333;
    }

    /* Dark mode specific overrides */
    body.dark-mode {
        background: var(--color-bg-main);
        color: var(--color-text-primary);
    }

    body.dark-mode .card,
    body.dark-mode .action-card,
    body.dark-mode .search-bar {
        background: var(--color-bg-secondary);
        border-color: var(--color-border);
    }

    body.dark-mode .product-card {
        background: var(--color-bg-secondary);
        border-color: var(--color-border);
    }

    body.dark-mode .product-card:hover {
        background: var(--color-hover);
    }

    body.dark-mode input,
    body.dark-mode textarea,
    body.dark-mode select {
        background: var(--color-bg-input);
        color: var(--color-text-primary);
        border-color: var(--color-border);
    }

    body.dark-mode .message.user {
        background: var(--color-bg-user);
    }

    body.dark-mode .message.assistant {
        background: var(--color-bg-assistant);
    }

    body.dark-mode .bottom-nav,
    body.dark-mode #app-navbar {
        background: var(--color-bg-secondary);
        border-color: var(--color-border);
    }

    body.dark-mode .navbar-link:hover,
    body.dark-mode .nav-item:hover {
        background: var(--color-hover);
    }

    /* Images in dark mode - reduce brightness */
    body.dark-mode img {
        opacity: 0.9;
    }

    body.dark-mode img:hover {
        opacity: 1;
    }

    /* Buttons in dark mode */
    body.dark-mode button:not(.btn-primary) {
        background: var(--color-bg-input);
        color: var(--color-text-primary);
        border-color: var(--color-border);
    }

    body.dark-mode button:not(.btn-primary):hover {
        background: var(--color-hover);
    }

    /* Loading skeleton in dark mode */
    body.dark-mode .product-image.loading {
        background: linear-gradient(
            90deg,
            var(--color-bg-secondary) 25%,
            var(--color-hover) 50%,
            var(--color-bg-secondary) 75%
        );
    }

    /* Modals in dark mode */
    body.dark-mode .gallery-modal {
        background: rgba(0, 0, 0, 0.95);
    }

    body.dark-mode .alert-success {
        background: #1a3a1a;
        color: #4ade80;
        border-color: #2a4a2a;
    }

    body.dark-mode .alert-error {
        background: #3a1a1a;
        color: #ff6b6b;
        border-color: #4a2a2a;
    }
</style>
`;

// Inject styles
if (!document.getElementById('dark-mode-styles')) {
    document.head.insertAdjacentHTML('beforeend', darkModeStyles);
}
