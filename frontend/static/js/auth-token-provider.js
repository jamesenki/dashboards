/**
 * Authentication token provider for IoTSphere application
 * This module handles token retrieval, storage, and generation of test tokens
 * for development environments.
 */

class AuthTokenProvider {
  constructor() {
    this.tokenKey = 'auth_token';
    this.testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken';
  }

  /**
   * Get authentication token - uses test token in development
   * @returns {string} The authentication token
   */
  getToken() {
    // Check for development mode
    const isDevelopment = window.location.hostname === 'localhost' ||
                          window.location.hostname === '127.0.0.1';

    // In development, use test token if no auth token exists
    if (isDevelopment) {
      const storedToken = localStorage.getItem(this.tokenKey);
      if (!storedToken) {
        console.log('Development environment detected, using test token');
        this.setToken(this.testToken);
        return this.testToken;
      }
      return storedToken;
    }

    // In production, just return the stored token
    return localStorage.getItem(this.tokenKey) || null;
  }

  /**
   * Set authentication token
   * @param {string} token - The token to store
   */
  setToken(token) {
    localStorage.setItem(this.tokenKey, token);
  }

  /**
   * Clear authentication token
   */
  clearToken() {
    localStorage.removeItem(this.tokenKey);
  }
}

// Create global instance
window.authTokenProvider = new AuthTokenProvider();
