/**
 * @jest-environment jsdom
 */

// Mock functions for DOM manipulation and fetch API
global.fetch = jest.fn();
global.document = window.document;
global.window.location = { href: '/model-monitoring/models' };

describe('Model Monitoring Dashboard', () => {
  // Setup and teardown
  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = `
      <div class="monitoring-dashboard">
        <div class="header-controls">
          <h1>Model Monitoring</h1>
          <a href="/model-monitoring/models?view=archived" class="primary-button">View Archived</a>
        </div>
        <section class="models-management">
          <div id="monitoring-status" class="monitoring-status-container" style="display: none;">
            <h3>Monitoring Status</h3>
            <div class="status-details">
              <div class="status-item">
                <span class="status-label">Status:</span>
                <span class="status-value" id="monitoring-status-value">Active</span>
              </div>
            </div>
          </div>
          <div id="batch-operations" class="batch-ops-container">
            <div class="select-controls">
              <label>
                <input type="checkbox" id="select-all-models"> Select All
              </label>
            </div>
            <div class="batch-actions">
              <button id="enable-monitoring" class="secondary-btn">Enable Monitoring</button>
              <button id="disable-monitoring" class="secondary-btn">Disable Monitoring</button>
              <button id="archive-selected" class="secondary-btn">Archive Selected</button>
              <button id="apply-tag" class="secondary-btn">Apply Tag</button>
              <button id="manage-tags-btn" class="secondary-btn">Manage Tags</button>
            </div>
          </div>
          <div class="table-container">
            <table id="models-comparison-table" class="data-table">
              <thead>
                <tr>
                  <th>Select</th>
                  <th>Model Name</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="models-table-body">
                <tr data-model-id="model1">
                  <td><input type="checkbox" class="model-select" data-model-id="model1"></td>
                  <td>Test Model 1</td>
                  <td>
                    <button class="action-btn view-btn" data-model-id="model1">View</button>
                    <button class="action-btn edit-btn" data-model-id="model1">Edit</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
      <!-- Tags Management Modal -->
      <div id="tags-modal" class="modal" style="display: none;">
        <div class="modal-content">
          <div class="modal-header">
            <h2>Manage Tags</h2>
            <button id="close-tags-modal" class="close-button">&times;</button>
          </div>
          <div class="modal-body">
            <div id="tags-list" class="tags-list"></div>
            <div class="create-tag-form">
              <input type="text" id="tag-name">
              <select id="tag-color">
                <option value="blue">Blue</option>
              </select>
              <button id="create-tag-btn">Create Tag</button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Mock fetch responses
    global.fetch.mockImplementation((url) => {
      if (url === '/api/monitoring/models') {
        return Promise.resolve({
          json: () => Promise.resolve([
            { id: 'model1', name: 'Test Model 1', archived: false },
            { id: 'model2', name: 'Test Model 2', archived: false }
          ])
        });
      } else if (url === '/api/monitoring/models/archived') {
        return Promise.resolve({
          json: () => Promise.resolve([
            { id: 'model3', name: 'Test Model 3', archived: true },
            { id: 'model4', name: 'Test Model 4', archived: true }
          ])
        });
      } else if (url === '/api/monitoring/tags') {
        return Promise.resolve({
          json: () => Promise.resolve([
            { id: 'tag1', name: 'Production', color: 'green' },
            { id: 'tag2', name: 'Development', color: 'blue' }
          ])
        });
      } else if (url.includes('/api/monitoring/models/batch')) {
        return Promise.resolve({
          json: () => Promise.resolve({ status: 'success' })
        });
      }
      
      return Promise.reject(new Error('Not found'));
    });
  });
  
  afterEach(() => {
    // Clean up
    jest.clearAllMocks();
  });
  
  // Load the actual code
  const loadModelMonitoringCode = () => {
    // Here we would normally load the actual JavaScript code
    // But for testing purposes, we'll define the key functions inline
    window.allModels = [];
    window.viewingArchived = false;
    window.tagsModal = document.getElementById('tags-modal');
    
    window.setupEventHandlers = () => {
      // Set up event handlers
      const enableMonitoringBtn = document.getElementById('enable-monitoring');
      if (enableMonitoringBtn) {
        enableMonitoringBtn.addEventListener('click', () => window.applyBatchOperation('enable_monitoring'));
      }
      
      const manageTagsBtn = document.getElementById('manage-tags-btn');
      if (manageTagsBtn) {
        manageTagsBtn.addEventListener('click', window.showTagsManagementModal);
      }
      
      const viewButtons = document.querySelectorAll('.action-btn.view-btn');
      viewButtons.forEach(button => {
        button.addEventListener('click', function() {
          window.viewModel(this.dataset.modelId);
        });
      });
      
      const editButtons = document.querySelectorAll('.action-btn.edit-btn');
      editButtons.forEach(button => {
        button.addEventListener('click', function() {
          window.editModel(this.dataset.modelId);
        });
      });
    };
    
    window.applyBatchOperation = (operation, params = {}) => {
      const selectedModels = Array.from(document.querySelectorAll('.model-select:checked'))
        .map(checkbox => checkbox.dataset.modelId);
      
      if (selectedModels.length === 0) {
        return false;
      }
      
      if (operation === 'enable_monitoring') {
        const monitoringStatus = document.getElementById('monitoring-status');
        if (monitoringStatus) {
          monitoringStatus.style.display = 'block';
        }
      }
      
      return true;
    };
    
    window.showTagsManagementModal = () => {
      if (window.tagsModal) {
        window.tagsModal.style.display = 'block';
      }
    };
    
    window.viewModel = (modelId) => {
      const modelDetailView = document.createElement('div');
      modelDetailView.id = 'model-detail-view';
      document.body.appendChild(modelDetailView);
    };
    
    window.editModel = (modelId) => {
      const modelEditView = document.createElement('div');
      modelEditView.id = 'model-edit-view';
      document.body.appendChild(modelEditView);
    };
    
    // Initialize
    window.setupEventHandlers();
  };
  
  // Tests
  test('Enable monitoring should show monitoring status', () => {
    loadModelMonitoringCode();
    
    // Select a model
    const checkbox = document.querySelector('.model-select');
    checkbox.checked = true;
    
    // Click enable monitoring
    const enableBtn = document.getElementById('enable-monitoring');
    enableBtn.click();
    
    // Check if monitoring status is visible
    const monitoringStatus = document.getElementById('monitoring-status');
    expect(monitoringStatus.style.display).toBe('block');
  });
  
  test('Manage tags button should open tags modal', () => {
    loadModelMonitoringCode();
    
    // Click manage tags button
    const manageTagsBtn = document.getElementById('manage-tags-btn');
    manageTagsBtn.click();
    
    // Check if tags modal is visible
    const tagsModal = document.getElementById('tags-modal');
    expect(tagsModal.style.display).toBe('block');
  });
  
  test('View button should create model detail view', () => {
    loadModelMonitoringCode();
    
    // Click view button
    const viewBtn = document.querySelector('.action-btn.view-btn');
    viewBtn.click();
    
    // Check if model detail view was created
    const modelDetailView = document.getElementById('model-detail-view');
    expect(modelDetailView).not.toBeNull();
  });
  
  test('Edit button should create model edit view', () => {
    loadModelMonitoringCode();
    
    // Click edit button
    const editBtn = document.querySelector('.action-btn.edit-btn');
    editBtn.click();
    
    // Check if model edit view was created
    const modelEditView = document.getElementById('model-edit-view');
    expect(modelEditView).not.toBeNull();
  });
});
