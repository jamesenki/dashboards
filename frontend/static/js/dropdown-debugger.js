/**
 * Dropdown Debugger - For testing the dropdown formatting function
 */

function debugDropdownFormat(machineData) {
    console.log('%c DROPDOWN DEBUGGER ACTIVE', 'background: blue; color: white; font-size: 16px; padding: 5px;');

    // Create debug output area if it doesn't exist
    let debugOutput = document.getElementById('dropdown-debug-output');
    if (!debugOutput) {
        debugOutput = document.createElement('div');
        debugOutput.id = 'dropdown-debug-output';
        debugOutput.style.cssText = 'position: fixed; top: 50px; right: 10px; width: 500px; max-height: 80%; overflow-y: auto; background: rgba(0,0,0,0.8); color: #00ff00; padding: 15px; font-family: monospace; font-size: 12px; z-index: 9999; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.5);';
        document.body.appendChild(debugOutput);
    }

    // Helper function to get a proper string value from any type of field (copied from original)
    function getStringValue(value) {
        if (value === null || value === undefined) return 'Unknown';

        // If it's already a string, just return it
        if (typeof value === 'string') return value;

        // If it's an object with a value property (like an enum), get that
        if (typeof value === 'object' && value.value) return value.value;

        // Otherwise convert to string
        return String(value);
    }

    // Clear previous output
    debugOutput.innerHTML = '<h3>Dropdown Format Debugger</h3>';

    // Add test controls
    debugOutput.innerHTML += `
        <div style="margin-bottom: 10px;">
            <button id="run-dropdown-test" style="background: #4CAF50; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-right: 5px;">Run Test</button>
            <button id="clear-dropdown-test" style="background: #f44336; color: white; border: none; padding: 5px 10px; cursor: pointer;">Clear</button>
            <button id="close-dropdown-test" style="background: #555; color: white; border: none; padding: 5px 10px; cursor: pointer; float: right;">Close</button>
        </div>
    `;

    // Analyze the data
    let processedResults = [];

    if (!machineData || !Array.isArray(machineData) || machineData.length === 0) {
        addToDebugLog('⚠️ No machine data provided or empty array');
        return;
    }

    addToDebugLog(`Processing ${machineData.length} machines...`);

    // Process each machine
    machineData.forEach((machine, index) => {
        try {
            // First check if all required properties exist
            const propertyCheck = {
                'name': machine.hasOwnProperty('name'),
                'location_business_name': machine.hasOwnProperty('location_business_name'),
                'location_type': machine.hasOwnProperty('location_type'),
                'sub_location': machine.hasOwnProperty('sub_location'),
                'id': machine.hasOwnProperty('id')
            };

            // Get the values using the same function as the original code
            const values = {
                'name': getStringValue(machine.name),
                'location_business_name': getStringValue(machine.location_business_name),
                'location_type': getStringValue(machine.location_type),
                'sub_location': getStringValue(machine.sub_location)
            };

            // Format exactly as in the original function
            const displayText = [
                values.name,
                values.location_business_name,
                values.location_type,
                values.sub_location
            ].join(' | ');

            // Store result
            processedResults.push({
                index,
                id: machine.id,
                propertyCheck,
                values,
                displayText
            });

        } catch (error) {
            addToDebugLog(`⚠️ Error processing machine ${index}: ${error.message}`);
        }
    });

    // Display results
    processedResults.forEach(result => {
        addToDebugLog(`Machine ${result.index} (${result.id}):`);

        // Show property check results
        const missingProps = Object.entries(result.propertyCheck)
            .filter(([_, exists]) => !exists)
            .map(([prop, _]) => prop);

        if (missingProps.length > 0) {
            addToDebugLog(`  ⚠️ Missing properties: ${missingProps.join(', ')}`, 'warning');
        }

        // Show values
        Object.entries(result.values).forEach(([prop, value]) => {
            const isDefault = value === 'Unknown';
            addToDebugLog(`  ${prop}: ${value}`, isDefault ? 'default' : 'normal');
        });

        // Show final display text
        addToDebugLog(`  Display: "${result.displayText}"`, 'result');
    });

    // Add click handlers for buttons
    document.getElementById('run-dropdown-test').addEventListener('click', () => {
        // Fetch fresh data and rerun
        fetchMachineData();
    });

    document.getElementById('clear-dropdown-test').addEventListener('click', () => {
        debugOutput.innerHTML = '<h3>Dropdown Format Debugger</h3>';
        addToDebugLog('Output cleared');
    });

    document.getElementById('close-dropdown-test').addEventListener('click', () => {
        debugOutput.remove();
    });

    function addToDebugLog(message, type = 'info') {
        const logEntry = document.createElement('div');
        let style = '';

        switch (type) {
            case 'warning':
                style = 'color: orange;';
                break;
            case 'error':
                style = 'color: red;';
                break;
            case 'result':
                style = 'color: cyan; font-weight: bold;';
                break;
            case 'default':
                style = 'color: #999;';
                break;
            default:
                style = 'color: #00ff00;';
        }

        logEntry.style.cssText = style;
        logEntry.textContent = message;
        debugOutput.appendChild(logEntry);
    }

    function fetchMachineData() {
        addToDebugLog('Fetching fresh machine data...');

        fetch('/api/vending-machines')
            .then(response => response.json())
            .then(data => {
                addToDebugLog(`✅ Fetched ${data.length} machines`);
                debugDropdownFormat(data);
            })
            .catch(error => {
                addToDebugLog(`⚠️ Error fetching machine data: ${error.message}`, 'error');
            });
    }
}

// Auto-initialize when included on a page
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dropdown debugger loaded and ready');

    // Create a floating button to activate the debugger
    const debugButton = document.createElement('button');
    debugButton.textContent = '🔍 Debug Dropdown';
    debugButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; background: #2196F3; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-weight: bold;';
    document.body.appendChild(debugButton);

    debugButton.addEventListener('click', () => {
        // Get current machine data from the global context if available
        let machineData = window.machineData || [];
        if (!machineData || !machineData.length) {
            // Try to fetch it
            fetch('/api/vending-machines')
                .then(response => response.json())
                .then(data => {
                    debugDropdownFormat(data);
                })
                .catch(error => {
                    console.error('Error fetching machine data:', error);
                    // Still try to run with empty data to show the UI
                    debugDropdownFormat([]);
                });
        } else {
            debugDropdownFormat(machineData);
        }
    });
});
