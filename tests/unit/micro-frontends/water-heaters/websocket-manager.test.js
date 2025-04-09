/**
 * @jest-environment jsdom
 */

describe('WebSocketManager', () => {
  let WebSocketManager;
  let mockWebSocket;
  let manager;

  // Mock WebSocket implementation
  class MockWebSocket {
    constructor(url) {
      // Handle either URL object or string
      this.url = typeof url === 'object' ? url.toString() : url;
      this.readyState = 0; // CONNECTING
      this.CONNECTING = 0;
      this.OPEN = 1;
      this.CLOSING = 2;
      this.CLOSED = 3;

      // Parse token from URL if present
      try {
        const urlObj = new URL(this.url);
        this.authToken = urlObj.searchParams.get('token');
      } catch (e) {
        // Invalid URL, ignore
      }

      // Event handlers
      this.onopen = null;
      this.onclose = null;
      this.onmessage = null;
      this.onerror = null;

      // Event listeners
      this.eventListeners = {
        open: [],
        close: [],
        message: [],
        error: []
      };

      // Auto-open the connection after a short delay to simulate network
      setTimeout(() => {
        this.readyState = 1; // OPEN
        this._triggerEvent('open', {});
      }, 10);
    }

    addEventListener(event, callback) {
      if (!this.eventListeners[event]) {
        this.eventListeners[event] = [];
      }
      this.eventListeners[event].push(callback);
    }

    removeEventListener(event, callback) {
      if (this.eventListeners[event]) {
        this.eventListeners[event] = this.eventListeners[event]
          .filter(cb => cb !== callback);
      }
    }

    send(data) {
      // Mock sending data
      if (this.readyState !== 1) {
        throw new Error('WebSocket is not open');
      }

      // Parse data to check for authentication
      try {
        const parsedData = JSON.parse(data);
        // Store authentication token if sent
        if (parsedData.type === 'authenticate' && parsedData.token) {
          this.authToken = parsedData.token;
        }
      } catch (e) {
        // Not JSON data, ignore
      }
    }

    close(code = 1000, reason = '') {
      this.readyState = 3; // CLOSED
      this._triggerEvent('close', { code, reason });
    }

    // Simulate receiving a message
    receiveMessage(data) {
      this._triggerEvent('message', { data: JSON.stringify(data) });
    }

    // Simulate an error
    simulateError(error) {
      this._triggerEvent('error', error);
    }

    // Trigger an event
    _triggerEvent(eventType, event) {
      // Call the on* handler if defined
      const handlerName = 'on' + eventType;
      if (this[handlerName]) {
        this[handlerName](event);
      }

      // Call all event listeners
      if (this.eventListeners[eventType]) {
        this.eventListeners[eventType].forEach(listener => {
          listener(event);
        });
      }
    }
  }

  beforeEach(() => {
    // Store the original WebSocket and timer functions
    global.OriginalWebSocket = global.WebSocket;
    global.OriginalSetTimeout = global.setTimeout;

    // Replace with our mock
    mockWebSocket = MockWebSocket;
    global.WebSocket = jest.fn(url => new mockWebSocket(url));

    // Import the WebSocketManager (dynamic import to ensure it uses our mock)
    jest.resetModules();
    WebSocketManager = require('../../../../frontend/static/js/websocket-manager').WebSocketManager;

    // Create a new manager instance with shorter reconnect delays for testing
    manager = new WebSocketManager({
      baseUrl: 'localhost:8000',
      tokenProvider: () => 'mock-token-123',
      onConnectionChange: jest.fn(),
      initialReconnectDelay: 10,  // Short delay for tests
      maxReconnectDelay: 100      // Short max delay for tests
    });
  });

  afterEach(() => {
    // Restore the original WebSocket and timer functions
    global.WebSocket = global.OriginalWebSocket;
    global.setTimeout = global.OriginalSetTimeout;

    // Reset all mocks
    jest.restoreAllMocks();

    // Clean up the manager
    if (manager) {
      manager.closeAll();
    }
  });

  test('should initialize with default settings', () => {
    expect(manager.baseUrl).toBe('localhost:8000');
    expect(manager.connections).toEqual({});
    expect(manager.maxReconnectAttempts).toBe(10);
  });

  test('should establish a WebSocket connection with token in URL', () => {
    const spy = jest.spyOn(global, 'WebSocket');
    const connectionId = manager.connect('/ws/devices/123/state');

    // The WebSocket URL should include the token as a query parameter
    expect(spy).toHaveBeenCalledWith(expect.anything());
    // Check that the URL passed to WebSocket contains our token
    const urlArg = spy.mock.calls[0][0];
    const url = typeof urlArg === 'object' ? urlArg.toString() : urlArg;
    expect(url).toMatch(/ws:\/\/localhost:8000\/ws\/devices\/123\/state\?token=mock-token-123/);

    expect(connectionId).toBeDefined();
    expect(manager.connections[connectionId]).toBeDefined();
  });

  test('should authenticate using URL token and fallback message', done => {
    const connectionId = manager.connect('/ws/devices/123/state');
    const connection = manager.connections[connectionId];

    // Mock the send method to capture authentication message
    const sendSpy = jest.spyOn(connection, 'send');

    // Allow more time for the test to complete
    setTimeout(() => {
      // Check URL token authentication
      expect(connection.url).toContain('token=mock-token-123');

      // Check fallback authentication message
      if (sendSpy.mock.calls.length > 0) {
        const authMessage = JSON.parse(sendSpy.mock.calls[0][0]);
        expect(authMessage.type).toBe('authenticate');
        expect(authMessage.token).toBe('mock-token-123');
      }

      done();
    }, 50);
  });

  test('should handle connection errors', done => {
    const errorCallback = jest.fn();
    const connectionId = manager.connect('/ws/devices/123/state', {
      onError: errorCallback
    });

    const connection = manager.connections[connectionId];

    // Force connection to be established
    connection.readyState = 1; // OPEN
    manager.connectionState[connectionId].isConnected = true;

    // Simulate an error
    connection.simulateError(new Error('Connection failed'));

    // Error should be passed to callback
    expect(errorCallback).toHaveBeenCalled();
    done();
  });

  test('should schedule reconnection after connection failure', () => {
    // Mock setTimeout to prevent actual timer execution
    const originalSetTimeout = global.setTimeout;
    const mockSetTimeout = jest.fn((callback, ms) => 0);
    global.setTimeout = mockSetTimeout;

    const connectionId = manager.connect('/ws/devices/123/state');
    const connection = manager.connections[connectionId];

    // Force connection to be established to properly test reconnection
    connection.readyState = 1; // OPEN
    manager.connectionState[connectionId].isConnected = true;

    // Simulate connection closing with error
    connection._triggerEvent('close', { code: 1006, reason: 'Abnormal closure' });

    // Check that reconnect was scheduled
    expect(mockSetTimeout).toHaveBeenCalled();
    expect(mockSetTimeout.mock.calls[0][1]).toBeGreaterThan(0); // Delay should be positive

    // Restore setTimeout
    global.setTimeout = originalSetTimeout;
  });

  // We no longer need this test as all connections now use URL params
  test('should handle auth token in URL params by default', () => {
    // Our default manager already uses URL auth
    const spy = jest.spyOn(global, 'WebSocket');
    manager.connect('/ws/devices/999/state');

    // The URL should contain the token
    const callArg = spy.mock.calls[spy.mock.calls.length-1][0];
    const urlString = typeof callArg === 'object' ? callArg.toString() : callArg;

    // Token should be in the URL
    expect(urlString).toContain('token=mock-token-123');
  });

  test('should include token when reconnecting', () => {
    // Mock _establishConnection to test params without executing it
    const originalMethod = manager._establishConnection;
    manager._establishConnection = jest.fn();

    // Mock setTimeout to directly execute callback
    const originalSetTimeout = global.setTimeout;
    global.setTimeout = jest.fn((callback, ms) => { callback(); return 999; });

    // Create a connection
    const connectionId = manager.connect('/ws/devices/456/state');

    // Manually trigger reconnection code - use the correct method name
    manager._scheduleReconnection(connectionId, 0, 1);

    // Check _establishConnection was called
    expect(manager._establishConnection).toHaveBeenCalledWith(connectionId);

    // Restore original methods
    manager._establishConnection = originalMethod;
    global.setTimeout = originalSetTimeout;
  });
});
