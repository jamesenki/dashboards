/**
 * Mock User Service
 * 
 * This file provides a mock implementation of the user service
 * for use in BDD tests. It simulates the behavior of the real service
 * without actually connecting to a user database.
 */

/**
 * Creates a mock user service for testing
 */
function mockUserService() {
  // In-memory storage for users
  const users = new Map();
  
  // Define mock roles and permissions
  const roles = {
    'FACILITY_MANAGER': {
      permissions: ['READ_DEVICES', 'REGISTER_DEVICE', 'UPDATE_DEVICE', 'VIEW_DASHBOARDS', 'VIEW_ANALYTICS']
    },
    'SERVICE_TECHNICIAN': {
      permissions: ['READ_DEVICES', 'UPDATE_DEVICE', 'RECORD_MAINTENANCE', 'VIEW_TELEMETRY', 'VIEW_DIAGNOSTICS']
    },
    'END_USER': {
      permissions: ['READ_OWN_DEVICES', 'CONTROL_OWN_DEVICES', 'VIEW_OWN_DASHBOARDS']
    },
    'SYSTEM_ADMIN': {
      permissions: ['READ_DEVICES', 'REGISTER_DEVICE', 'UPDATE_DEVICE', 'DELETE_DEVICE', 'MANAGE_USERS', 'MANAGE_SYSTEM']
    },
    'ENERGY_MANAGER': {
      permissions: ['READ_DEVICES', 'VIEW_ANALYTICS', 'VIEW_ENERGY_REPORTS']
    },
    'MANUFACTURER': {
      permissions: ['READ_OWN_BRAND_DEVICES', 'VIEW_TELEMETRY', 'VIEW_ANALYTICS']
    },
    'BMS_INTEGRATOR': {
      permissions: ['READ_DEVICES', 'VIEW_TELEMETRY', 'CONTROL_DEVICES']
    }
  };
  
  // Add some pre-defined users
  users.set('facility-manager-1', {
    id: 'facility-manager-1',
    username: 'facility.manager',
    email: 'facility.manager@example.com',
    roles: ['FACILITY_MANAGER'],
    permissions: roles['FACILITY_MANAGER'].permissions,
    metadata: { facilityIds: ['facility-1', 'facility-2'] }
  });
  
  users.set('service-tech-1', {
    id: 'service-tech-1',
    username: 'service.tech',
    email: 'service.tech@example.com',
    roles: ['SERVICE_TECHNICIAN'],
    permissions: roles['SERVICE_TECHNICIAN'].permissions,
    metadata: { certifications: ['AquaTherm Certified', 'HVAC-R'] }
  });
  
  // Add an admin user
  users.set('admin-1', {
    id: 'admin-1',
    username: 'admin.user',
    email: 'admin@example.com',
    roles: ['ADMIN', 'SYSTEM_ADMIN'],  // Include both ADMIN and SYSTEM_ADMIN for flexibility
    permissions: roles['SYSTEM_ADMIN'] ? roles['SYSTEM_ADMIN'].permissions : ['MANAGE_USERS', 'MANAGE_SYSTEM', 'READ_DEVICES'],
    metadata: { isSystemAdmin: true }
  });
  
  // Add a technician user
  users.set('tech-1', {
    id: 'tech-1',
    username: 'tech.user',
    email: 'tech@example.com',
    roles: ['TECHNICIAN', 'SERVICE_TECHNICIAN'],  // Include both TECHNICIAN and SERVICE_TECHNICIAN for flexibility
    permissions: roles['SERVICE_TECHNICIAN'] ? roles['SERVICE_TECHNICIAN'].permissions : ['READ_DEVICES', 'UPDATE_DEVICE', 'RECORD_MAINTENANCE'],
    metadata: { certifications: ['HVAC Certified'] }
  });
  
  users.set('system-admin-1', {
    id: 'system-admin-1',
    username: 'system.admin',
    email: 'system.admin@example.com',
    roles: ['SYSTEM_ADMIN'],
    permissions: roles['SYSTEM_ADMIN'].permissions,
    metadata: {}
  });
  
  users.set('end-user-1', {
    id: 'end-user-1',
    username: 'end.user',
    email: 'end.user@example.com',
    roles: ['END_USER'],
    permissions: roles['END_USER'].permissions,
    metadata: { deviceIds: ['device-101', 'device-102'] }
  });
  
  return {
    /**
     * Reset the mock to initial state
     */
    reset() {
      // Clear any dynamically added users, keep the pre-defined ones
    },
    
    /**
     * Get a user by role
     * @param {string} role The role to find a user for
     * @returns {Promise<Object>} A user with the specified role
     */
    async getUserByRole(role) {
      // Find a user with the specified role
      for (const user of users.values()) {
        if (user.roles.includes(role)) {
          return user;
        }
      }
      
      // If no existing user has this role, create a mock user with this role
      if (roles[role]) {
        const mockUser = {
          id: `mock-${role.toLowerCase()}-user`,
          username: `mock.${role.toLowerCase()}.user`,
          email: `mock.${role.toLowerCase()}.user@example.com`,
          roles: [role],
          permissions: roles[role].permissions,
          metadata: {}
        };
        
        // Add to users collection for future use
        users.set(mockUser.id, mockUser);
        return mockUser;
      }
      
      // Return null if the role doesn't exist
      return null;
    },
    
    /**
     * Authenticate a user
     * @param {Object} credentials User credentials or role to impersonate
     * @returns {Promise<Object>} The authenticated user
     */
    async authenticate(credentials) {
      // For test purposes, we can authenticate by role or by username
      if (credentials.role) {
        // Find a user with the specified role
        for (const user of users.values()) {
          if (user.roles.includes(credentials.role)) {
            return {
              ...user,
              token: `mock-token-${user.id}`
            };
          }
        }
        
        // If no user with the role exists, create one
        const userId = `${credentials.role.toLowerCase()}-${Date.now()}`;
        const newUser = {
          id: userId,
          username: `${credentials.role.toLowerCase()}.user`,
          email: `${credentials.role.toLowerCase()}.user@example.com`,
          roles: [credentials.role],
          permissions: roles[credentials.role] ? roles[credentials.role].permissions : [],
          metadata: {}
        };
        
        users.set(userId, newUser);
        
        return {
          ...newUser,
          token: `mock-token-${userId}`
        };
      } else if (credentials.username) {
        // Find user by username
        for (const user of users.values()) {
          if (user.username === credentials.username) {
            return {
              ...user,
              token: `mock-token-${user.id}`
            };
          }
        }
      }
      
      throw new Error('Authentication failed');
    },
    
    /**
     * Check if a user has a specific permission
     * @param {string} userId User ID
     * @param {string} permission Permission to check
     * @returns {Promise<boolean>} True if the user has the permission
     */
    async hasPermission(userId, permission) {
      const user = users.get(userId);
      
      if (!user) {
        return false;
      }
      
      return user.permissions.includes(permission);
    },
    
    /**
     * Check if a user has access to a device
     * @param {string} userId User ID
     * @param {string} deviceId Device ID
     * @returns {Promise<boolean>} True if the user has access
     */
    async hasDeviceAccess(userId, deviceId) {
      const user = users.get(userId);
      
      if (!user) {
        return false;
      }
      
      // System admins have access to all devices
      if (user.roles.includes('SYSTEM_ADMIN')) {
        return true;
      }
      
      // Facility managers have access to all devices
      if (user.roles.includes('FACILITY_MANAGER')) {
        return true;
      }
      
      // Service technicians have access to all devices
      if (user.roles.includes('SERVICE_TECHNICIAN')) {
        return true;
      }
      
      // End users only have access to their own devices
      if (user.roles.includes('END_USER')) {
        return user.metadata.deviceIds && user.metadata.deviceIds.includes(deviceId);
      }
      
      return false;
    },
    
    /**
     * Authenticate a user - alias for 'authenticate' method to maintain compatibility with tests
     * @param {Object} credentials User credentials or role to impersonate
     * @returns {Promise<Object>} The authenticated user
     */
    async authenticateUser(credentials) {
      // Simply call the existing authenticate method to avoid duplication
      return this.authenticate(credentials);
    }
  };
}

module.exports = { mockUserService };
