/**
 * WebSocketManager - Client-side manager for WebSocket connections
 * 
 * This class provides a robust implementation for managing WebSocket connections
 * with automatic reconnection, authentication, and message handling.
 */
class WebSocketManager {
    /**
     * Initialize the WebSocket Manager
     * @param {Object} options - Configuration options
     * @param {string} options.baseUrl - Base URL for WebSocket connections (without the ws:// prefix)
     * @param {Function} options.tokenProvider - Function that returns a JWT token
     * @param {Function} options.onConnectionChange - Callback for connection state changes
     * @param {number} options.maxReconnectAttempts - Maximum reconnection attempts (default: 10)
     * @param {number} options.initialReconnectDelay - Initial delay before reconnecting in ms (default: 1000)
     * @param {number} options.maxReconnectDelay - Maximum reconnection delay in ms (default: 30000)
     */
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || window.location.host;
        this.secure = window.location.protocol === 'https:';
        this.tokenProvider = options.tokenProvider || (() => null);
        this.onConnectionChange = options.onConnectionChange || (() => {});
        
        // Connection state
        this.connections = {};  // Map of connection IDs to WebSocket instances
        this.connectionState = {};  // Map of connection IDs to state objects
        
        // Reconnection settings
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.initialReconnectDelay = options.initialReconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;
        
        // Heartbeat to detect zombie connections
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.heartbeatTimer = null;
        
        // Start the heartbeat
        this._startHeartbeat();
        
        console.log('WebSocketManager initialized');
    }
    
    /**
     * Connect to a WebSocket endpoint
     * @param {string} endpoint - The endpoint to connect to (e.g., "/ws/devices/123/state")
     * @param {Object} options - Connection options
     * @param {Function} options.onMessage - Callback for incoming messages
     * @param {Function} options.onOpen - Callback when connection is established
     * @param {Function} options.onClose - Callback when connection is closed
     * @param {Function} options.onError - Callback for connection errors
     * @param {boolean} options.autoReconnect - Whether to automatically reconnect (default: true)
     * @returns {string} Connection ID that can be used to manage this connection
     */
    connect(endpoint, options = {}) {
        const connectionId = this._generateConnectionId();
        const protocol = this.secure ? 'wss://' : 'ws://';
        const url = `${protocol}${this.baseUrl}${endpoint}`;
        
        // Setup connection state
        this.connectionState[connectionId] = {
            url,
            endpoint,
            isConnected: false,
            reconnectAttempts: 0,
            reconnectDelay: this.initialReconnectDelay,
            autoReconnect: options.autoReconnect !== false,
            lastMessageTime: Date.now(),
            options
        };
        
        // Establish the connection
        this._establishConnection(connectionId);
        
        return connectionId;
    }
    
    /**
     * Send a message through a WebSocket connection
     * @param {string} connectionId - The connection ID
     * @param {Object|string} message - The message to send (will be JSON stringified if object)
     * @returns {boolean} Whether the message was sent successfully
     */
    send(connectionId, message) {
        const connection = this.connections[connectionId];
        const state = this.connectionState[connectionId];
        
        if (!connection || !state || !state.isConnected) {
            console.warn(`Cannot send message: connection ${connectionId} is not established`);
            return false;
        }
        
        try {
            const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
            connection.send(messageStr);
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    /**
     * Close a WebSocket connection
     * @param {string} connectionId - The connection ID to close
     * @param {number} code - Close code (default: 1000 - normal closure)
     * @param {string} reason - Close reason
     */
    close(connectionId, code = 1000, reason = 'Normal closure') {
        const connection = this.connections[connectionId];
        const state = this.connectionState[connectionId];
        
        if (!connection) {
            console.warn(`Cannot close: connection ${connectionId} not found`);
            return;
        }
        
        // Prevent reconnection
        if (state) {
            state.autoReconnect = false;
        }
        
        // Close the connection
        try {
            connection.close(code, reason);
        } catch (error) {
            console.error('Error closing WebSocket connection:', error);
        }
        
        // Clean up
        this._cleanupConnection(connectionId);
    }
    
    /**
     * Close all active WebSocket connections
     */
    closeAll() {
        Object.keys(this.connections).forEach(connectionId => {
            this.close(connectionId);
        });
    }
    
    /**
     * Check if a connection is active
     * @param {string} connectionId - The connection ID to check
     * @returns {boolean} Whether the connection is active and connected
     */
    isConnected(connectionId) {
        const state = this.connectionState[connectionId];
        return !!(state && state.isConnected);
    }
    
    /**
     * Update authentication token for all connections
     * This is useful when the JWT token has been refreshed
     */
    updateAuthentication() {
        // Refresh all connections to use the new token
        Object.keys(this.connections).forEach(connectionId => {
            const state = this.connectionState[connectionId];
            if (state && state.isConnected) {
                // Reconnect with new token
                this.reconnect(connectionId);
            }
        });
    }
    
    /**
     * Force reconnection of a specific connection
     * @param {string} connectionId - The connection ID to reconnect
     */
    reconnect(connectionId) {
        const connection = this.connections[connectionId];
        const state = this.connectionState[connectionId];
        
        if (!state) {
            console.warn(`Cannot reconnect: connection ${connectionId} not found`);
            return;
        }
        
        // Reset reconnection attempts
        state.reconnectAttempts = 0;
        state.reconnectDelay = this.initialReconnectDelay;
        state.isConnected = false;
        
        // Close existing connection
        if (connection) {
            try {
                connection.close(1000, 'Reconnecting');
            } catch (error) {
                // Ignore errors when closing
            }
        }
        
        // Establish new connection
        this._establishConnection(connectionId);
    }
    
    // ======================== Private Methods ========================
    
    /**
     * Generate a unique connection ID
     * @returns {string} Unique connection ID
     * @private
     */
    _generateConnectionId() {
        return `conn-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
    }
    
    /**
     * Establish a WebSocket connection
     * @param {string} connectionId - The connection ID
     * @private
     */
    _establishConnection(connectionId) {
        const state = this.connectionState[connectionId];
        if (!state) return;
        
        // Get auth token
        const token = this.tokenProvider();
        let url = new URL(state.url);
        
        // Clean up any existing connection
        if (this.connections[connectionId]) {
            try {
                this.connections[connectionId].close();
            } catch (error) {
                // Ignore errors when closing
            }
            delete this.connections[connectionId];
        }
        
        // Handle token authentication - add token to URL for WebSocket connections
        // since headers cannot be set directly for WebSockets
        if (token) {
            // Add token to URL query params (the server expects this)
            url.searchParams.append('token', token);
        }
        
        // Create new WebSocket connection with authentication in URL
        console.log(`Establishing WebSocket connection to ${url.toString()}`);
        const socket = new WebSocket(url);
        this.connections[connectionId] = socket;
        
        // As a fallback, also send token in first message after connection
        if (token) {
            socket.addEventListener('open', () => {
                // Send authentication message as fallback
                this.send(connectionId, {
                    type: 'authenticate',
                    token
                });
            });
        }
        
        // Setup event handlers
        socket.addEventListener('open', (event) => {
            console.log(`WebSocket connection established: ${state.endpoint}`);
            state.isConnected = true;
            state.reconnectAttempts = 0;
            state.reconnectDelay = this.initialReconnectDelay;
            state.lastMessageTime = Date.now();
            
            // Notify status change
            this.onConnectionChange(connectionId, true);
            
            // Call user callback
            if (state.options.onOpen) {
                state.options.onOpen(event);
            }
        });
        
        socket.addEventListener('message', (event) => {
            state.lastMessageTime = Date.now();
            
            try {
                // Parse the message
                let data = event.data;
                if (typeof data === 'string') {
                    try {
                        data = JSON.parse(data);
                    } catch (e) {
                        // Keep as string if not valid JSON
                    }
                }
                
                // Check for error messages
                if (data && data.error) {
                    console.warn(`WebSocket error message: ${data.error}`);
                    if (data.error.includes('authentication') || data.error.includes('permission')) {
                        // Authentication errors should not trigger reconnection
                        state.autoReconnect = false;
                    }
                }
                
                // Call user callback
                if (state.options.onMessage) {
                    state.options.onMessage(data, event);
                }
            } catch (error) {
                console.error('Error handling WebSocket message:', error);
            }
        });
        
        socket.addEventListener('close', (event) => {
            console.log(`WebSocket connection closed: ${state.endpoint}`, event.code, event.reason);
            state.isConnected = false;
            
            // Notify status change
            this.onConnectionChange(connectionId, false);
            
            // Call user callback
            if (state.options.onClose) {
                state.options.onClose(event);
            }
            
            // Handle reconnection
            if (state.autoReconnect) {
                this._scheduleReconnection(connectionId);
            } else {
                this._cleanupConnection(connectionId);
            }
        });
        
        socket.addEventListener('error', (error) => {
            console.error(`WebSocket error: ${state.endpoint}`, error);
            
            // Call user callback
            if (state.options.onError) {
                state.options.onError(error);
            }
        });
    }
    
    /**
     * Schedule a reconnection attempt
     * @param {string} connectionId - The connection ID
     * @private
     */
    _scheduleReconnection(connectionId) {
        const state = this.connectionState[connectionId];
        if (!state) return;
        
        state.reconnectAttempts += 1;
        
        // Check if max attempts reached
        if (state.reconnectAttempts > this.maxReconnectAttempts) {
            console.warn(`Max reconnect attempts reached for ${state.endpoint}`);
            this._cleanupConnection(connectionId);
            return;
        }
        
        // Use exponential backoff with jitter
        const delay = Math.min(
            state.reconnectDelay * (1 + Math.random() * 0.5),
            this.maxReconnectDelay
        );
        
        console.log(`Scheduling reconnection for ${state.endpoint} in ${delay}ms (attempt ${state.reconnectAttempts})`);
        
        // Schedule reconnection
        setTimeout(() => {
            if (this.connectionState[connectionId]) {
                state.reconnectDelay = Math.min(state.reconnectDelay * 1.5, this.maxReconnectDelay);
                this._establishConnection(connectionId);
            }
        }, delay);
    }
    
    /**
     * Clean up a connection
     * @param {string} connectionId - The connection ID
     * @private
     */
    _cleanupConnection(connectionId) {
        delete this.connections[connectionId];
        delete this.connectionState[connectionId];
    }
    
    /**
     * Start the heartbeat to detect zombie connections
     * @private
     */
    _startHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        
        this.heartbeatTimer = setInterval(() => {
            const now = Date.now();
            
            Object.keys(this.connectionState).forEach(connectionId => {
                const state = this.connectionState[connectionId];
                const connection = this.connections[connectionId];
                
                // Check for zombie connections (connected but no messages for too long)
                if (state && state.isConnected && connection) {
                    const timeSinceLastMessage = now - state.lastMessageTime;
                    
                    if (timeSinceLastMessage > this.heartbeatInterval * 2) {
                        console.warn(`Zombie connection detected: ${state.endpoint}, reconnecting...`);
                        this.reconnect(connectionId);
                    } else if (timeSinceLastMessage > this.heartbeatInterval) {
                        // Send heartbeat ping
                        try {
                            this.send(connectionId, { type: 'ping', timestamp: now });
                        } catch (error) {
                            // If ping fails, connection might be dead
                            this.reconnect(connectionId);
                        }
                    }
                }
            });
        }, this.heartbeatInterval);
    }
    
    /**
     * Stop the heartbeat
     * @private
     */
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    /**
     * Clean up all resources when the manager is no longer needed
     */
    destroy() {
        this.closeAll();
        this._stopHeartbeat();
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketManager };
} else {
    // For browser use
    window.WebSocketManager = WebSocketManager;
}
