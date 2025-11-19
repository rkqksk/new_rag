/**
 * Recommendations Widget
 * Display personalized product recommendations
 * Version: v8.6.0 (Phase 9)
 */

class RecommendationsWidget {
    constructor(options = {}) {
        this.options = {
            apiBase: options.apiBase || 'http://localhost:8001/api/v1',
            containerId: options.containerId || 'recommendations-container',
            strategy: options.strategy || 'hybrid',
            topK: options.topK || 10,
            autoLoad: options.autoLoad !== false,
            onItemClick: options.onItemClick || null
        };

        this.recommendations = [];
        this.loading = false;

        // Create container if it doesn't exist
        this.ensureContainer();

        // Auto-load if enabled
        if (this.options.autoLoad) {
            this.load();
        }
    }

    /**
     * Ensure container exists
     */
    ensureContainer() {
        let container = document.getElementById(this.options.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.containerId;
            document.body.appendChild(container);
        }
        this.container = container;
    }

    /**
     * Load recommendations
     */
    async load(userId = null) {
        if (this.loading) return;

        this.loading = true;
        this.showLoading();

        try {
            // Get user ID from auth if not provided
            if (!userId) {
                const user = typeof auth !== 'undefined' && auth.getUser();
                userId = user ? user.id : 'anonymous';
            }

            // Fetch recommendations
            const url = `${this.options.apiBase}/recommendations/user/${userId}?strategy=${this.options.strategy}&top_k=${this.options.topK}`;

            let response;
            if (typeof auth !== 'undefined' && auth.fetchWithAuth) {
                response = await auth.fetchWithAuth(url);
            } else {
                response = await fetch(url);
            }

            if (!response.ok) {
                throw new Error(`Failed to load recommendations: ${response.status}`);
            }

            const data = await response.json();
            this.recommendations = data.recommendations || [];

            this.render();

        } catch (error) {
            console.error('Failed to load recommendations:', error);
            this.showError('Failed to load recommendations');
        } finally {
            this.loading = false;
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #6b7280;">
                <div style="
                    border: 3px solid #e5e7eb;
                    border-top: 3px solid #2563eb;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 10px;
                "></div>
                Loading recommendations...
            </div>
        `;

        // Add spin animation if not already added
        if (!document.getElementById('recommendations-spin-animation')) {
            const style = document.createElement('style');
            style.id = 'recommendations-spin-animation';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        this.container.innerHTML = `
            <div style="
                background: #fee;
                color: #ef4444;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            ">
                ${message}
            </div>
        `;
    }

    /**
     * Render recommendations
     */
    render() {
        if (this.recommendations.length === 0) {
            this.container.innerHTML = `
                <div style="
                    background: #f3f4f6;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    color: #6b7280;
                ">
                    No recommendations available
                </div>
            `;
            return;
        }

        // Create recommendations grid
        const html = `
            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
            ">
                ${this.recommendations.map(rec => this.renderItem(rec)).join('')}
            </div>
        `;

        this.container.innerHTML = html;

        // Add click listeners
        this.recommendations.forEach((rec, index) => {
            const element = this.container.querySelector(`[data-rec-index="${index}"]`);
            if (element) {
                element.addEventListener('click', () => this.onItemClick(rec));
            }
        });
    }

    /**
     * Render single recommendation item
     */
    renderItem(rec, index) {
        const scorePercent = (rec.score * 100).toFixed(0);

        return `
            <div data-rec-index="${index}" style="
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 16px;
                cursor: pointer;
                transition: all 0.2s;
            " onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'"
               onmouseout="this.style.boxShadow='none'">
                <div style="font-weight: 600; margin-bottom: 8px; font-size: 16px;">
                    ${rec.metadata.product_name || rec.item_id}
                </div>

                <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">
                    ${rec.reason}
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="
                        background: #dbeafe;
                        color: #1e40af;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: 600;
                    ">
                        ${scorePercent}% Match
                    </div>

                    ${rec.metadata.price ? `
                        <div style="font-weight: 600; color: #2563eb;">
                            ₩${rec.metadata.price.toLocaleString()}
                        </div>
                    ` : ''}
                </div>

                ${rec.metadata.category ? `
                    <div style="
                        margin-top: 8px;
                        padding-top: 8px;
                        border-top: 1px solid #f3f4f6;
                        font-size: 12px;
                        color: #9ca3af;
                    ">
                        ${rec.metadata.category}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Handle item click
     */
    onItemClick(rec) {
        console.log('Recommendation clicked:', rec);

        // Track interaction
        this.trackInteraction(rec.item_id, 'click');

        // Call user callback
        if (this.options.onItemClick) {
            this.options.onItemClick(rec);
        }
    }

    /**
     * Track user interaction
     */
    async trackInteraction(itemId, interactionType = 'view') {
        try {
            const url = `${this.options.apiBase}/recommendations/track`;

            const body = {
                item_id: itemId,
                interaction_type: interactionType
            };

            let response;
            if (typeof auth !== 'undefined' && auth.fetchWithAuth) {
                response = await auth.fetchWithAuth(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                });
            } else {
                response = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                });
            }

            if (!response.ok) {
                console.warn('Failed to track interaction');
            }

        } catch (error) {
            console.error('Failed to track interaction:', error);
        }
    }

    /**
     * Change recommendation strategy
     */
    async changeStrategy(strategy) {
        this.options.strategy = strategy;
        await this.load();
    }

    /**
     * Refresh recommendations
     */
    async refresh() {
        await this.load();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RecommendationsWidget;
}
