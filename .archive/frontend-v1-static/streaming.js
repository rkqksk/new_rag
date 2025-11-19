/**
 * WebSocket and SSE Streaming Module for Real-time LLM Responses
 * ==============================================================
 *
 * Features:
 * - WebSocket for bidirectional real-time communication
 * - Server-Sent Events (SSE) as fallback
 * - Token-by-token streaming display
 * - Progress updates during search
 * - Automatic reconnection
 *
 * Usage:
 *     const stream = new StreamingClient(sessionId, {
 *         onToken: (token) => console.log(token),
 *         onComplete: (data) => console.log('Done'),
 *         onError: (error) => console.error(error)
 *     });
 *
 *     stream.query("50ml PET 용기", {
 *         collections: ["chungjinkorea"],
 *         materials: ["PET"]
 *     });
 *
 * Version: v6.0.0
 */

class StreamingClient {
    constructor(sessionId, callbacks = {}) {
        this.sessionId = sessionId;
        this.callbacks = {
            onStatus: callbacks.onStatus || (() => {}),
            onToken: callbacks.onToken || (() => {}),
            onProductsBatch: callbacks.onProductsBatch || (() => {}),
            onComplete: callbacks.onComplete || (() => {}),
            onError: callbacks.onError || ((err) => console.error(err)),
        };

        this.ws = null;
        this.eventSource = null;
        this.useWebSocket = true; // Try WebSocket first
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
    }

    /**
     * Send query via WebSocket or SSE
     */
    async query(query, options = {}) {
        const collections = options.collections || null;
        const materials = options.materials || null;

        if (this.useWebSocket) {
            return this.queryWebSocket(query, collections, materials);
        } else {
            return this.querySSE(query, collections, materials);
        }
    }

    /**
     * Query via WebSocket
     */
    async queryWebSocket(query, collections, materials) {
        return new Promise((resolve, reject) => {
            const wsUrl = `ws://localhost:8001/api/v1/stream/ws/${this.sessionId}`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.reconnectAttempts = 0;

                    // Send query
                    this.ws.send(JSON.stringify({
                        type: 'query',
                        query: query,
                        collections: collections,
                        materials: materials
                    }));
                };

                this.ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);

                    if (message.type === 'complete') {
                        resolve(message.data);
                        this.ws.close();
                    } else if (message.type === 'error') {
                        reject(new Error(message.data));
                        this.ws.close();
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);

                    // Fallback to SSE
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        console.log(`Retrying WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                        setTimeout(() => {
                            this.queryWebSocket(query, collections, materials)
                                .then(resolve)
                                .catch(reject);
                        }, 1000 * this.reconnectAttempts);
                    } else {
                        console.log('Falling back to SSE...');
                        this.useWebSocket = false;
                        this.querySSE(query, collections, materials)
                            .then(resolve)
                            .catch(reject);
                    }
                };

                this.ws.onclose = () => {
                    console.log('WebSocket closed');
                };

            } catch (error) {
                console.error('WebSocket initialization failed:', error);
                // Fallback to SSE
                this.useWebSocket = false;
                this.querySSE(query, collections, materials)
                    .then(resolve)
                    .catch(reject);
            }
        });
    }

    /**
     * Query via Server-Sent Events (SSE)
     */
    async querySSE(query, collections, materials) {
        return new Promise((resolve, reject) => {
            const params = new URLSearchParams({
                session_id: this.sessionId,
                query: query
            });

            if (collections && collections.length > 0) {
                params.append('collections', collections.join(','));
            }
            if (materials && materials.length > 0) {
                params.append('materials', materials.join(','));
            }

            const sseUrl = `http://localhost:8001/api/v1/stream/sse?${params.toString()}`;

            try {
                this.eventSource = new EventSource(sseUrl);

                this.eventSource.addEventListener('status', (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                });

                this.eventSource.addEventListener('token', (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                });

                this.eventSource.addEventListener('products_batch', (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                });

                this.eventSource.addEventListener('complete', (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                    resolve(message.data);
                    this.eventSource.close();
                });

                this.eventSource.addEventListener('error', (event) => {
                    const message = JSON.parse(event.data);
                    reject(new Error(message.data));
                    this.eventSource.close();
                });

                this.eventSource.onerror = (error) => {
                    console.error('SSE error:', error);
                    reject(error);
                    this.eventSource.close();
                };

            } catch (error) {
                console.error('SSE initialization failed:', error);
                reject(error);
            }
        });
    }

    /**
     * Handle incoming message
     */
    handleMessage(message) {
        console.log('Message received:', message.type, message);

        switch (message.type) {
            case 'status':
                this.callbacks.onStatus(message.data, message);
                break;

            case 'token':
                this.callbacks.onToken(message.data, message);
                break;

            case 'products_batch':
                this.callbacks.onProductsBatch(message.data, message);
                break;

            case 'complete':
                this.callbacks.onComplete(message.data, message);
                break;

            case 'error':
                this.callbacks.onError(message.data, message);
                break;

            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    /**
     * Send keep-alive ping (WebSocket only)
     */
    ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }

    /**
     * Close connection
     */
    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

/**
 * Fallback to HTTP POST (backward compatibility)
 */
async function queryHTTP(sessionId, query, collections, materials) {
    const response = await fetch('http://localhost:8001/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            query: query,
            collections: collections,
            materials: materials
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
    }

    return await response.json();
}

// Export for use in chat.html
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StreamingClient, queryHTTP };
}
