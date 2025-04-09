/**
 * Web Components Testing Utilities
 *
 * This file provides utility functions and mocks for testing Web Components
 * in Jest with JSDOM.
 */

/**
 * Extracts the default property values from a component class's constructor
 * by analyzing the constructor body's source code
 */
function extractDefaultProperties(ComponentClass) {
  try {
    // Get constructor source code
    const constructorStr = ComponentClass.toString();

    // Find properties assigned with 'this.' in the constructor
    const propRegex = /this\.(\w+)\s*=\s*(.+?);/g;
    const properties = {};

    let match;
    while ((match = propRegex.exec(constructorStr)) !== null) {
      const propName = match[1];
      const propValueStr = match[2].trim();

      // Skip shadowRoot
      if (propName === 'shadowRoot') continue;

      // Try to evaluate the property value
      try {
        // Handle common literals
        if (propValueStr === 'null') {
          properties[propName] = null;
        } else if (propValueStr === 'true') {
          properties[propName] = true;
        } else if (propValueStr === 'false') {
          properties[propName] = false;
        } else if (propValueStr === '[]') {
          properties[propName] = [];
        } else if (propValueStr === '{}') {
          properties[propName] = {};
        } else if (!isNaN(Number(propValueStr))) {
          properties[propName] = Number(propValueStr);
        } else {
          // For more complex values, we'll set them directly in the tests
          properties[propName] = undefined;
        }
      } catch (e) {
        properties[propName] = undefined;
      }
    }

    return properties;
  } catch (error) {
    console.warn('Error extracting default properties:', error);
    return {};
  }
}

// Class decorator to patch HTMLElement inheritance issues in tests
export function patchHTMLElementClass(ComponentClass) {
  // Create a patched version of the component that doesn't extend HTMLElement
  // but has all the same methods and properties
  class PatchedComponent {
    constructor() {
      // Create a mock shadow DOM
      this.shadowRoot = {
        querySelector: jest.fn(),
        querySelectorAll: jest.fn().mockReturnValue([]),
        innerHTML: ''
      };

      // Common element properties
      this.getAttribute = jest.fn();
      this.setAttribute = jest.fn();
      this.addEventListener = jest.fn();
      this.removeEventListener = jest.fn();
      this.dispatchEvent = jest.fn();
      this.classList = {
        add: jest.fn(),
        remove: jest.fn(),
        toggle: jest.fn(),
        contains: jest.fn().mockReturnValue(false)
      };

      // Set up default component properties extracted from the original class
      const defaultProps = extractDefaultProperties(ComponentClass);
      Object.assign(this, defaultProps);

      // Initialize component's own methods
      // Get property descriptors from the original class prototype
      const originalProto = ComponentClass.prototype;
      Object.getOwnPropertyNames(originalProto).forEach(prop => {
        // Skip constructor
        if (prop === 'constructor') return;

        // If it's a method, copy it to the patched instance
        if (typeof originalProto[prop] === 'function') {
          this[prop] = originalProto[prop].bind(this);
        }
      });
    }

    // Mock attachShadow method
    attachShadow() {
      return this.shadowRoot;
    }

    // Common lifecycle methods that might be overridden
    connectedCallback() {}
    disconnectedCallback() {}
    attributeChangedCallback() {}
    adoptedCallback() {}
  }

  return PatchedComponent;
}

// Function to create and patch a specific component class
export function createPatchedComponent(ComponentClass) {
  const PatchedComponent = patchHTMLElementClass(ComponentClass);
  const instance = new PatchedComponent();

  // Handle specific component types with known properties
  if (ComponentClass.name === 'DeviceEvents') {
    // Manual initialization for DeviceEvents
    instance.device = null;
    instance.deviceId = null;
    instance.events = [];
    instance.isLoading = true;
    instance.error = null;
    instance.filterType = 'all';
    instance.currentPage = 1;
    instance.eventsPerPage = 10;
    instance.totalPages = 1;
  }

  return instance;
}
