/**
 * Authentication Utilities for RAG Enterprise
 * Handles JWT token management, auto-refresh, and user session
 * Version: v8.2.0 (Phase 2)
 */

const AUTH_CONFIG = {
    API_BASE: window.location.origin + '/api/v1',
    TOKEN_KEY: 'access_token',
    REFRESH_KEY: 'refresh_token',
    USER_KEY: 'user',
    REFRESH_BEFORE_EXPIRY_MS: 5 * 60 * 1000, // Refresh 5 minutes before expiry
};

class AuthManager {
    constructor() {
        this.refreshTimer = null;
        this.isRefreshing = false;
    }

    /**
     * Get access token from localStorage
     */
    getAccessToken() {
        return localStorage.getItem(AUTH_CONFIG.TOKEN_KEY);
    }

    /**
     * Get refresh token from localStorage
     */
    getRefreshToken() {
        return localStorage.getItem(AUTH_CONFIG.REFRESH_KEY);
    }

    /**
     * Get user info from localStorage
     */
    getUser() {
        const userStr = localStorage.getItem(AUTH_CONFIG.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * Save tokens and user info
     */
    saveAuth(accessToken, refreshToken, user) {
        localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, accessToken);
        localStorage.setItem(AUTH_CONFIG.REFRESH_KEY, refreshToken);
        localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(user));

        // Schedule auto-refresh
        this.scheduleTokenRefresh();
    }

    /**
     * Clear all auth data
     */
    clearAuth() {
        localStorage.removeItem(AUTH_CONFIG.TOKEN_KEY);
        localStorage.removeItem(AUTH_CONFIG.REFRESH_KEY);
        localStorage.removeItem(AUTH_CONFIG.USER_KEY);

        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return !!this.getAccessToken();
    }

    /**
     * Parse JWT token to get expiry time
     */
    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error('Failed to parse JWT:', e);
            return null;
        }
    }

    /**
     * Check if token is expired or will expire soon
     */
    isTokenExpiringSoon(token, beforeMs = AUTH_CONFIG.REFRESH_BEFORE_EXPIRY_MS) {
        const payload = this.parseJWT(token);
        if (!payload || !payload.exp) return true;

        const expiryTime = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        return (expiryTime - now) < beforeMs;
    }

    /**
     * Refresh access token using refresh token
     */
    async refreshAccessToken() {
        if (this.isRefreshing) {
            console.log('Token refresh already in progress');
            return false;
        }

        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            console.error('No refresh token available');
            return false;
        }

        this.isRefreshing = true;

        try {
            const response = await fetch(`${AUTH_CONFIG.API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem(AUTH_CONFIG.TOKEN_KEY, data.access_token);

                console.log('Access token refreshed successfully');
                this.scheduleTokenRefresh();
                return true;
            } else {
                console.error('Token refresh failed:', response.status);
                // If refresh fails, clear auth and redirect to login
                this.clearAuth();
                window.location.href = '/login.html';
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        } finally {
            this.isRefreshing = false;
        }
    }

    /**
     * Schedule automatic token refresh
     */
    scheduleTokenRefresh() {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }

        const accessToken = this.getAccessToken();
        if (!accessToken) return;

        const payload = this.parseJWT(accessToken);
        if (!payload || !payload.exp) return;

        const expiryTime = payload.exp * 1000;
        const now = Date.now();
        const refreshTime = expiryTime - AUTH_CONFIG.REFRESH_BEFORE_EXPIRY_MS;
        const delay = refreshTime - now;

        if (delay > 0) {
            console.log(`Token refresh scheduled in ${Math.round(delay / 1000)}s`);
            this.refreshTimer = setTimeout(() => {
                this.refreshAccessToken();
            }, delay);
        } else {
            // Token already expired or expiring soon, refresh immediately
            console.log('Token expiring soon, refreshing now');
            this.refreshAccessToken();
        }
    }

    /**
     * Verify current authentication status with server
     */
    async verifyAuth() {
        console.log('[Auth] verifyAuth() called');
        const accessToken = this.getAccessToken();
        if (!accessToken) {
            console.error('[Auth] No access token found');
            return false;
        }
        console.log('[Auth] Access token exists');

        // Check if token is expiring soon
        if (this.isTokenExpiringSoon(accessToken)) {
            console.log('[Auth] Token expiring soon, refreshing...');
            const refreshed = await this.refreshAccessToken();
            if (!refreshed) {
                console.error('[Auth] Token refresh failed');
                return false;
            }
            console.log('[Auth] Token refreshed successfully');
        }

        try {
            const url = `${AUTH_CONFIG.API_BASE}/auth/me`;
            console.log('[Auth] Calling:', url);

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.getAccessToken()}`,
                },
            });

            console.log('[Auth] Response status:', response.status);
            console.log('[Auth] Response ok:', response.ok);

            if (response.ok) {
                const user = await response.json();
                console.log('[Auth] User verified:', user.email);
                localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(user));
                return true;
            } else {
                const errorText = await response.text();
                console.error('[Auth] Auth verification failed:', response.status, errorText);
                return false;
            }
        } catch (error) {
            console.error('[Auth] Auth verification error:', error);
            return false;
        }
    }

    /**
     * Logout user
     */
    async logout() {
        const accessToken = this.getAccessToken();

        // Call logout endpoint if token exists
        if (accessToken) {
            try {
                await fetch(`${AUTH_CONFIG.API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                });
            } catch (error) {
                console.error('Logout API call failed:', error);
            }
        }

        // Clear local auth data
        this.clearAuth();

        // Redirect to login
        window.location.href = '/login.html';
    }

    /**
     * Require authentication - redirect to login if not authenticated
     * Call this on protected pages
     */
    async requireAuth() {
        console.log('[Auth] requireAuth() called');

        if (!this.isLoggedIn()) {
            console.error('[Auth] Not logged in, redirecting to login');
            window.location.href = '/login.html';
            return false;
        }
        console.log('[Auth] User is logged in');

        const isValid = await this.verifyAuth();
        console.log('[Auth] Verification result:', isValid);

        if (!isValid) {
            console.error('[Auth] Verification failed, clearing auth and redirecting');
            this.clearAuth();
            window.location.href = '/login.html';
            return false;
        }

        // Start auto-refresh if not already scheduled
        if (!this.refreshTimer) {
            console.log('[Auth] Scheduling token refresh');
            this.scheduleTokenRefresh();
        }

        console.log('[Auth] Authentication successful');
        return true;
    }

    /**
     * Make authenticated API request
     */
    async fetchWithAuth(url, options = {}) {
        const accessToken = this.getAccessToken();
        if (!accessToken) {
            throw new Error('Not authenticated');
        }

        // Check if token needs refresh
        if (this.isTokenExpiringSoon(accessToken)) {
            await this.refreshAccessToken();
        }

        // Add authorization header
        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.getAccessToken()}`,
        };

        const response = await fetch(url, {
            ...options,
            headers,
        });

        // If 401, try to refresh token once
        if (response.status === 401 && !options._retry) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Retry request with new token
                return this.fetchWithAuth(url, { ...options, _retry: true });
            } else {
                // Refresh failed, redirect to login
                this.clearAuth();
                window.location.href = '/login.html';
                throw new Error('Authentication failed');
            }
        }

        return response;
    }

    /**
     * Get authorization header for manual fetch calls
     */
    getAuthHeader() {
        const token = this.getAccessToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }
}

// Global auth instance
const auth = new AuthManager();

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Schedule refresh if user is logged in
        if (auth.isLoggedIn()) {
            auth.scheduleTokenRefresh();
        }
    });
} else {
    // Document already loaded
    if (auth.isLoggedIn()) {
        auth.scheduleTokenRefresh();
    }
}

// Export for use in other scripts
window.auth = auth;
