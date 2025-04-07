/**
 * Status Monitor - Direct fix for status duplication
 * 
 * This module uses a MutationObserver to detect and prevent status duplication
 * in the operations dashboard. It's a fail-safe mechanism that works even if
 * the other fixes don't catch all cases.
 */

class StatusMonitor {
    constructor() {
        this.initialized = false;
        this.observer = null;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        if (this.initialized) return;
        console.log('📊 Status Monitor: Initializing...');
        
        // Set up mutation observer configuration
        const config = { 
            childList: true, 
            subtree: true 
        };
        
        // Create a mutation observer to watch for status duplication
        this.observer = new MutationObserver((mutations) => {
            // Check for status container changes
            const statusContainerMutations = mutations.filter(mutation => {
                return mutation.target.classList && 
                       (mutation.target.classList.contains('status-container') || 
                        mutation.target.closest('.status-container'));
            });
            
            if (statusContainerMutations.length > 0) {
                this.checkForDuplicates();
            }
        });
        
        // Start observing once the operations tab is activated
        this.waitForOperationsTab();
        
        // Also check periodically as a backup
        setInterval(() => this.checkForDuplicates(), 2000);
        
        // Mark as initialized
        this.initialized = true;
        console.log('📊 Status Monitor: Initialized successfully');
    }
    
    waitForOperationsTab() {
        const operationsTab = document.getElementById('operations-tab-btn');
        if (operationsTab) {
            operationsTab.addEventListener('click', () => {
                // When operations tab is clicked, start observing after a short delay
                setTimeout(() => {
                    const statusContainer = document.querySelector('.status-container');
                    if (statusContainer && this.observer) {
                        console.log('📊 Status Monitor: Starting observation of status container');
                        this.observer.observe(statusContainer, { childList: true });
                        this.checkForDuplicates();
                    }
                }, 100);
            });
            console.log('📊 Status Monitor: Event listener added to operations tab');
        } else {
            // If tab button not found yet, try again in a moment
            setTimeout(() => this.waitForOperationsTab(), 500);
        }
    }
    
    checkForDuplicates() {
        const statusContainer = document.querySelector('.status-container');
        if (!statusContainer) return;
        
        // Get all status items
        const statusItems = statusContainer.querySelectorAll('.status-item');
        if (statusItems.length <= 5) return; // No duplication if 5 or fewer items
        
        console.warn(`📊 Status Monitor: Detected ${statusItems.length} status items (expected 5) - fixing duplication`);
        
        // Get a map of status item texts to identify duplicates
        const statusMap = new Map();
        statusItems.forEach(item => {
            const label = item.querySelector('.status-label')?.textContent.trim();
            if (label) {
                if (!statusMap.has(label)) {
                    statusMap.set(label, item);
                } else {
                    // This is a duplicate - mark for removal
                    item.classList.add('duplicate-status-item');
                }
            }
        });
        
        // Remove duplicate items
        const duplicates = statusContainer.querySelectorAll('.duplicate-status-item');
        duplicates.forEach(item => item.remove());
        
        console.log(`📊 Status Monitor: Removed ${duplicates.length} duplicate status items`);
    }
}

// Create global instance
window.statusMonitor = new StatusMonitor();

console.log('Status Monitor loaded: Active protection against status duplication');
