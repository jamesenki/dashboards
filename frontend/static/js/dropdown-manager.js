/**
 * DropdownManager - Handles vending machine dropdown synchronization and selection
 * Keeps multiple dropdowns in sync and dispatches appropriate actions when selections change
 * 
 * This module ensures consistent machine selection across the Operations tab and Asset Health tab,
 * focusing on real-time operational monitoring as in the original Angular implementation.
 */
const DropdownManager = {
    // Initialize both dropdowns
    async initializeDropdowns(initialMachineId = null) {
        console.log('Initializing machine dropdowns');
        
        // Make sure MachineService is initialized
        if (!MachineService.apiBaseUrl) {
            MachineService.init();
        }
        
        try {
            const machines = await MachineService.getMachines();
            this.populateDropdowns(machines);
            
            // Set initial machine if provided
            if (initialMachineId) {
                this.selectMachine(initialMachineId);
            } else if (machines && machines.length > 0) {
                this.selectMachine(machines[0].id);
            }
            
            // Set up event listeners
            this.setupEventListeners();
            console.log('Dropdown initialization complete');
        } catch (error) {
            console.error('Error initializing dropdowns:', error);
            // Use fallback data in case of error
            const fallbackMachines = MachineService.getFallbackMachines();
            this.populateDropdowns(fallbackMachines);
            
            if (initialMachineId) {
                this.selectMachine(initialMachineId);
            } else if (fallbackMachines.length > 0) {
                this.selectMachine(fallbackMachines[0].id);
            }
            
            // Setup event listeners even in error case
            this.setupEventListeners();
        }
    },
    
    // Populate both dropdowns with machine data
    populateDropdowns(machines) {
        console.log(`Populating dropdowns with ${machines.length} machines`);
        const assetSelector = document.getElementById('machine-selector');
        const operationsSelector = document.getElementById('operations-machine-selector');
        
        if (!assetSelector && !operationsSelector) {
            console.error('No dropdown selectors found in the DOM');
            return;
        }
        
        // Clear existing options
        if (assetSelector) assetSelector.innerHTML = '<option value="">-- Select Vending Machine --</option>';
        if (operationsSelector) operationsSelector.innerHTML = '<option value="">-- Select Vending Machine --</option>';
        
        if (!machines || machines.length === 0) {
            console.error('No machines to populate dropdowns');
            return;
        }
        
        // Add options to both dropdowns
        machines.forEach(machine => {
            const displayText = MachineService.formatMachineName(machine);
            
            if (assetSelector) {
                const option = document.createElement('option');
                option.value = machine.id;
                option.textContent = displayText;
                assetSelector.appendChild(option);
            }
            
            if (operationsSelector) {
                const option = document.createElement('option');
                option.value = machine.id;
                option.textContent = displayText;
                operationsSelector.appendChild(option);
            }
        });
        
        console.log(`Dropdowns populated with ${machines.length} machines`);
    },
    
    // Set up event listeners for both dropdowns
    setupEventListeners() {
        console.log('Setting up dropdown event listeners');
        const assetSelector = document.getElementById('machine-selector');
        const operationsSelector = document.getElementById('operations-machine-selector');
        
        // Asset health dropdown change event
        if (assetSelector) {
            assetSelector.onchange = () => {
                const selectedId = assetSelector.value;
                if (selectedId) {
                    this.handleMachineSelection(selectedId, 'asset-health');
                }
            };
        }
        
        // Operations dropdown change event
        if (operationsSelector) {
            operationsSelector.onchange = () => {
                const selectedId = operationsSelector.value;
                if (selectedId) {
                    this.handleMachineSelection(selectedId, 'operations');
                }
            };
        }
        
        console.log('Event listeners set up for both dropdowns');
    },
    
    // Handle machine selection (keeps dropdowns in sync)
    handleMachineSelection(machineId, source) {
        console.log(`Machine ${machineId} selected from ${source} dropdown`);
        MachineService.selectedMachineId = machineId;
        
        // Keep dropdowns in sync
        this.syncDropdowns(machineId);
        
        // Update URL without reloading
        window.history.pushState({}, '', `/vending-machines/${machineId}`);
        
        // Provide visual feedback
        if (source === 'asset-health') {
            const header = document.querySelector('#asset-health-selection-header');
            if (header) {
                header.classList.add('selection-changed');
                setTimeout(() => {
                    header.classList.remove('selection-changed');
                }, 300);
            }
            
            // Load machine data for asset health tab
            if (typeof loadMachineData === 'function') {
                loadMachineData(machineId);
            } else {
                console.error('loadMachineData function not available');
            }
        } else if (source === 'operations') {
            const header = document.querySelector('.operations-summary-container .asset-selection-header');
            if (header) {
                header.classList.add('selection-changed');
                setTimeout(() => {
                    header.classList.remove('selection-changed');
                }, 300);
            }
            
            // Set global variable for operations tab
            window.operationalMachineId = machineId;
            
            // Load operations data for the operations tab
            if (typeof loadRealtimeOperationsData === 'function') {
                loadRealtimeOperationsData(machineId, 'operations-summary-content');
            } else {
                console.error('loadRealtimeOperationsData function not available');
            }
        }
    },
    
    // Keep all dropdowns in sync with the selected machine
    syncDropdowns(machineId) {
        const assetSelector = document.getElementById('machine-selector');
        const operationsSelector = document.getElementById('operations-machine-selector');
        
        if (assetSelector) assetSelector.value = machineId;
        if (operationsSelector) operationsSelector.value = machineId;
        
        console.log(`Synchronized all dropdowns to machine ID: ${machineId}`);
    },
    
    // Select a machine programmatically
    selectMachine(machineId) {
        if (!machineId) {
            console.error('No machine ID provided for selection');
            return;
        }
        
        console.log(`Programmatically selecting machine: ${machineId}`);
        this.syncDropdowns(machineId);
        this.handleMachineSelection(machineId, 'asset-health');
    },
    
    // Check if we have proper initialization
    diagnoseDropdowns() {
        const assetSelector = document.getElementById('machine-selector');
        const operationsSelector = document.getElementById('operations-machine-selector');
        
        console.log('Dropdown Diagnostics:');
        console.log(`Asset selector exists: ${!!assetSelector}`);
        console.log(`Operations selector exists: ${!!operationsSelector}`);
        
        if (assetSelector) {
            console.log(`Asset selector options: ${assetSelector.options.length}`);
            console.log(`Asset selector value: ${assetSelector.value}`);
        }
        
        if (operationsSelector) {
            console.log(`Operations selector options: ${operationsSelector.options.length}`);
            console.log(`Operations selector value: ${operationsSelector.value}`);
        }
        
        return {
            assetSelectorExists: !!assetSelector,
            operationsSelectorExists: !!operationsSelector,
            assetSelectorOptions: assetSelector ? assetSelector.options.length : 0,
            operationsSelectorOptions: operationsSelector ? operationsSelector.options.length : 0,
            assetSelectorValue: assetSelector ? assetSelector.value : null,
            operationsSelectorValue: operationsSelector ? operationsSelector.value : null
        };
    }
};
