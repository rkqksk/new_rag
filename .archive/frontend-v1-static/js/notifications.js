/**
 * WebSocket Notifications UI Component
 * Real-time notification management with toast and list views
 * Version: v8.6.0 (Phase 9)
 */

class NotificationManager {
    constructor(options = {}) {
        this.ws = null;
        this.reconnectInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000; // Start with 2 seconds

        this.options = {
            apiBase: options.apiBase || 'http://localhost:8001/api/v1',
            wsUrl: options.wsUrl || 'ws://localhost:8001/api/v1/ws/notifications',
            autoConnect: options.autoConnect !== false,
            showToasts: options.showToasts !== false,
            toastDuration: options.toastDuration || 5000,
            maxNotifications: options.maxNotifications || 50,
            onNotification: options.onNotification || null,
            onConnect: options.onConnect || null,
            onDisconnect: options.onDisconnect || null
        };

        this.notifications = [];
        this.isConnected = false;

        // Create UI elements
        this.createUI();

        // Auto-connect if enabled
        if (this.options.autoConnect) {
            this.connect();
        }
    }

    /**
     * Create notification UI elements
     */
    createUI() {
        // Create toast container
        if (!document.getElementById('notification-toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.id = 'notification-toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(toastContainer);
        }

        // Create notification bell icon (optional)
        this.createBellIcon();
    }

    /**
     * Create notification bell icon
     */
    createBellIcon() {
        // Check if bell already exists
        if (document.getElementById('notification-bell')) return;

        const bell = document.createElement('div');
        bell.id = 'notification-bell';
        bell.innerHTML = `
            <button id="notification-bell-btn" style="
                position: relative;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 18px;
                transition: all 0.2s;
            ">
                🔔
                <span id="notification-badge" style="
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: #ef4444;
                    color: white;
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: bold;
                    display: none;
                ">0</span>
            </button>
        `;

        // Add to page (you can customize where it's added)
        // For now, we'll skip auto-adding it and let the page decide
    }

    /**
     * Connect to WebSocket
     */
    async connect() {
        try {
            // Get auth token
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.warn('No access token found, connecting as anonymous');
            }

            // Build WebSocket URL with token
            const wsUrl = token
                ? `${this.options.wsUrl}?token=${token}`
                : this.options.wsUrl;

            // Create WebSocket connection
            this.ws = new WebSocket(wsUrl);

            // Set up event handlers
            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onclose = () => this.onClose();

        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket open
     */
    onOpen() {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 2000;

        // Call user callback
        if (this.options.onConnect) {
            this.options.onConnect();
        }

        // Send ping periodically
        this.startPingInterval();
    }

    /**
     * Handle incoming message
     */
    onMessage(event) {
        try {
            const notification = JSON.parse(event.data);

            // Handle special message types
            if (notification.type === 'pong') {
                // Pong response
                return;
            }

            if (notification.type === 'room_joined' || notification.type === 'room_left') {
                console.log('Room event:', notification);
                return;
            }

            if (notification.type === 'error') {
                console.error('WebSocket error:', notification.message);
                return;
            }

            // Add to notifications list
            this.addNotification(notification);

            // Show toast
            if (this.options.showToasts) {
                this.showToast(notification);
            }

            // Call user callback
            if (this.options.onNotification) {
                this.options.onNotification(notification);
            }

        } catch (error) {
            console.error('Failed to parse notification:', error);
        }
    }

    /**
     * Handle WebSocket error
     */
    onError(error) {
        console.error('WebSocket error:', error);
    }

    /**
     * Handle WebSocket close
     */
    onClose() {
        console.log('❌ WebSocket disconnected');
        this.isConnected = false;
        this.stopPingInterval();

        // Call user callback
        if (this.options.onDisconnect) {
            this.options.onDisconnect();
        }

        // Schedule reconnect
        this.scheduleReconnect();
    }

    /**
     * Schedule reconnection
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);

        this.reconnectInterval = setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
    }

    /**
     * Start ping interval
     */
    startPingInterval() {
        this.pingInterval = setInterval(() => {
            if (this.isConnected && this.ws) {
                this.send('ping', {timestamp: Date.now()});
            }
        }, 30000); // Ping every 30 seconds
    }

    /**
     * Stop ping interval
     */
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Send command to WebSocket
     */
    send(command, data = {}) {
        if (!this.isConnected || !this.ws) {
            console.warn('WebSocket not connected');
            return false;
        }

        try {
            this.ws.send(JSON.stringify({command, ...data}));
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
            return false;
        }
    }

    /**
     * Join a room
     */
    joinRoom(room) {
        return this.send('join_room', {room});
    }

    /**
     * Leave a room
     */
    leaveRoom(room) {
        return this.send('leave_room', {room});
    }

    /**
     * Add notification to list
     */
    addNotification(notification) {
        notification.id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        notification.read = false;
        notification.timestamp = notification.timestamp || new Date().toISOString();

        this.notifications.unshift(notification);

        // Limit number of notifications
        if (this.notifications.length > this.options.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.options.maxNotifications);
        }

        // Update badge
        this.updateBadge();
    }

    /**
     * Show toast notification
     */
    showToast(notification) {
        const container = document.getElementById('notification-toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.style.cssText = `
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 16px;
            margin-bottom: 12px;
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
        `;

        // Priority color
        const priorityColors = {
            low: '#6b7280',
            normal: '#2563eb',
            high: '#f59e0b',
            urgent: '#ef4444'
        };

        const borderColor = priorityColors[notification.priority] || priorityColors.normal;

        toast.innerHTML = `
            <div style="border-left: 4px solid ${borderColor}; padding-left: 12px;">
                <div style="font-weight: 600; margin-bottom: 4px;">
                    ${notification.title || 'Notification'}
                </div>
                <div style="font-size: 14px; color: #6b7280;">
                    ${notification.message || ''}
                </div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 8px;">
                    ${new Date(notification.timestamp).toLocaleTimeString()}
                </div>
            </div>
        `;

        // Click to dismiss
        toast.addEventListener('click', () => {
            toast.remove();
        });

        container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }
        }, this.options.toastDuration);

        // Add animations
        if (!document.getElementById('notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Update notification badge
     */
    updateBadge() {
        const badge = document.getElementById('notification-badge');
        if (!badge) return;

        const unreadCount = this.getUnreadCount();

        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }

    /**
     * Get unread notifications count
     */
    getUnreadCount() {
        return this.notifications.filter(n => !n.read).length;
    }

    /**
     * Mark notification as read
     */
    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
            this.updateBadge();
        }
    }

    /**
     * Mark all as read
     */
    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.updateBadge();
    }

    /**
     * Get all notifications
     */
    getNotifications() {
        return this.notifications;
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        this.notifications = [];
        this.updateBadge();
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        if (this.reconnectInterval) {
            clearTimeout(this.reconnectInterval);
            this.reconnectInterval = null;
        }

        this.stopPingInterval();
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.isConnected;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}
