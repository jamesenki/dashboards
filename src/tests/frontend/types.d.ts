/**
 * TypeScript declaration file for IoTSphere UI tests
 *
 * This file extends global interfaces with properties used in our tests
 * that TypeScript doesn't recognize by default.
 */

// Extend the Window interface to include our global dashboard instances
interface Window {
  // Dashboard instances
  waterHeaterPredictionsDashboard?: any;
  waterHeaterHistoryDashboard?: any;
  waterHeaterOperationsDashboard?: any;
  waterHeaterDetail?: any;

  // Tab manager
  tabManager?: any;

  // Data loading state tracker
  dataLoadingState?: {
    detail: boolean;
    operations: boolean;
    history: boolean;
    predictions: boolean;
  };
}

// Extend the Element interface to include DOM properties used in our tests
interface Element {
  // Visual state properties
  offsetParent: Element | null;
  style: CSSStyleDeclaration;
}
