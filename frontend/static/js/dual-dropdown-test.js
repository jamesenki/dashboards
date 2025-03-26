/**
 * Dual Dropdown Test Script
 * Tests both the Asset Health and Operations Summary dropdown selectors
 */
(function() {
    // Create test UI
    function createTestUI() {
        const testUI = document.createElement('div');
        testUI.id = 'dual-dropdown-test';
        testUI.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            background: rgba(0,0,0,0.85);
            color: #fff;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        `;
        
        testUI.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h2 style="margin: 0; color: #2196F3;">Dropdown Comparison Test</h2>
                <button id="close-dropdown-test" style="background: #555; border: none; color: white; padding: 3px 8px; cursor: pointer;">×</button>
            </div>
            <div style="margin-bottom: 10px;">
                <button id="run-dropdown-test" style="background: #4CAF50; color: white; border: none; padding: 5px 10px; margin-right: 5px; cursor: pointer;">Compare Dropdowns</button>
                <button id="fix-dropdown-issues" style="background: #FF9800; color: white; border: none; padding: 5px 10px; cursor: pointer;">Sync Formats</button>
            </div>
            <div id="dropdown-test-results" style="margin-top: 10px;"></div>
        `;
        
        document.body.appendChild(testUI);
        
        // Add event listeners
        document.getElementById('close-dropdown-test').addEventListener('click', () => {
            testUI.remove();
        });
        
        document.getElementById('run-dropdown-test').addEventListener('click', runDropdownTest);
        document.getElementById('fix-dropdown-issues').addEventListener('click', fixDropdownIssues);
    }
    
    // Run the dropdown comparison test
    function runDropdownTest() {
        const resultsDiv = document.getElementById('dropdown-test-results');
        resultsDiv.innerHTML = '<p>Running dropdown comparison...</p>';
        
        // Get both dropdowns
        const assetHealthDropdown = document.getElementById('machine-selector');
        const operationsDropdown = document.getElementById('operations-machine-selector');
        
        if (!assetHealthDropdown && !operationsDropdown) {
            resultsDiv.innerHTML = '<p style="color: orange;">No dropdown selectors found on the page!</p>';
            return;
        }
        
        // Test results
        const results = {
            assetHealth: {
                found: !!assetHealthDropdown,
                optionCount: assetHealthDropdown ? assetHealthDropdown.options.length : 0,
                options: []
            },
            operations: {
                found: !!operationsDropdown,
                optionCount: operationsDropdown ? operationsDropdown.options.length : 0,
                options: []
            },
            mismatches: []
        };
        
        // Process Asset Health dropdown
        if (assetHealthDropdown) {
            logResult(`Asset Health Dropdown: Found with ${assetHealthDropdown.options.length} options`);
            
            // Get option details
            for (let i = 0; i < assetHealthDropdown.options.length; i++) {
                const option = assetHealthDropdown.options[i];
                results.assetHealth.options.push({
                    index: i,
                    value: option.value,
                    text: option.textContent,
                    format: detectFormat(option.textContent)
                });
            }
        } else {
            logResult('Asset Health Dropdown: Not found', 'warning');
        }
        
        // Process Operations dropdown
        if (operationsDropdown) {
            logResult(`Operations Dropdown: Found with ${operationsDropdown.options.length} options`);
            
            // Get option details
            for (let i = 0; i < operationsDropdown.options.length; i++) {
                const option = operationsDropdown.options[i];
                results.operations.options.push({
                    index: i,
                    value: option.value,
                    text: option.textContent,
                    format: detectFormat(option.textContent)
                });
            }
        } else {
            logResult('Operations Dropdown: Not found', 'warning');
        }
        
        // Compare formats
        if (results.assetHealth.found && results.operations.found) {
            // Compare default options
            if (results.assetHealth.options[0]?.text !== results.operations.options[0]?.text) {
                results.mismatches.push(`Default option text mismatch: "${results.assetHealth.options[0]?.text}" vs "${results.operations.options[0]?.text}"`);
            }
            
            // Check if the number of options match
            if (results.assetHealth.optionCount !== results.operations.optionCount) {
                results.mismatches.push(`Option count mismatch: ${results.assetHealth.optionCount} vs ${results.operations.optionCount}`);
            }
            
            // Compare option pairs
            const minOptionCount = Math.min(results.assetHealth.optionCount, results.operations.optionCount);
            for (let i = 1; i < minOptionCount; i++) {
                const assetOption = results.assetHealth.options[i];
                const opsOption = results.operations.options[i];
                
                // Compare machine IDs (values)
                if (assetOption.value !== opsOption.value) {
                    results.mismatches.push(`Option ${i} value mismatch: "${assetOption.value}" vs "${opsOption.value}"`);
                } else {
                    // If IDs match but display text doesn't, we have a formatting mismatch
                    if (assetOption.text !== opsOption.text) {
                        results.mismatches.push(`Option ${i} (ID: ${assetOption.value}) text format mismatch:\n  Asset Health: "${assetOption.text}"\n  Operations: "${opsOption.text}"`);
                    }
                }
            }
        }
        
        // Display comparison results
        if (results.mismatches.length === 0) {
            logResult('✅ Both dropdowns have consistent formatting', 'success');
        } else {
            logResult('⚠️ Format inconsistencies detected:', 'warning');
            results.mismatches.forEach(issue => {
                logResult(`- ${issue}`, 'warning');
            });
        }
        
        // Show format details for each dropdown
        if (results.assetHealth.found) {
            logResult('\nAsset Health Dropdown Format:', 'info');
            const sampleOption = results.assetHealth.options.find(opt => opt.value && opt.text && opt.text !== 'Select a machine');
            if (sampleOption) {
                logResult(`Example: "${sampleOption.text}"`, 'detail');
                logResult(`Format: ${sampleOption.format}`, 'detail');
            }
        }
        
        if (results.operations.found) {
            logResult('\nOperations Dropdown Format:', 'info');
            const sampleOption = results.operations.options.find(opt => opt.value && opt.text && opt.text !== 'Select a machine');
            if (sampleOption) {
                logResult(`Example: "${sampleOption.text}"`, 'detail');
                logResult(`Format: ${sampleOption.format}`, 'detail');
            }
        }
        
        // Store results for fix function
        window.dropdownTestResults = results;
    }
    
    // Detect the format of a dropdown option text
    function detectFormat(text) {
        if (!text || text === 'Select a machine') return 'default';
        
        if (text.includes(' | ')) {
            return 'pipe-delimited';
        } else if (text.includes(', ')) {
            return 'comma-delimited';
        } else {
            return 'space-separated';
        }
    }
    
    // Log a result to the results div
    function logResult(message, type = 'normal') {
        const resultsDiv = document.getElementById('dropdown-test-results');
        const p = document.createElement('p');
        p.style.margin = '3px 0';
        
        switch (type) {
            case 'success':
                p.style.color = '#4CAF50';
                break;
            case 'warning':
                p.style.color = '#FF9800';
                break;
            case 'error':
                p.style.color = '#F44336';
                break;
            case 'info':
                p.style.color = '#2196F3';
                p.style.fontWeight = 'bold';
                break;
            case 'detail':
                p.style.color = '#BBBBBB';
                p.style.marginLeft = '10px';
                break;
            default:
                p.style.color = '#FFFFFF';
        }
        
        p.textContent = message;
        resultsDiv.appendChild(p);
    }
    
    // Fix dropdown inconsistencies
    function fixDropdownIssues() {
        const resultsDiv = document.getElementById('dropdown-test-results');
        resultsDiv.innerHTML = '<p>Applying fixes to make dropdowns consistent...</p>';
        
        // Get machines data first
        fetch('/api/vending-machines')
            .then(response => response.json())
            .then(machines => {
                if (!machines || !machines.length) {
                    logResult('No machine data available!', 'error');
                    return;
                }
                
                logResult(`Retrieved ${machines.length} machines to format consistently`, 'info');
                
                // Helper function to get a proper string value (same as in original code)
                function getStringValue(value) {
                    if (value === null || value === undefined) return 'Unknown';
                    if (typeof value === 'string') return value;
                    if (typeof value === 'object' && value.value) return value.value;
                    return String(value);
                }
                
                // Format all the options in both dropdowns
                updateAssetHealthDropdown(machines, getStringValue);
                updateOperationsDropdown(machines, getStringValue);
                
                logResult('✅ Applied consistent formatting to both dropdowns', 'success');
                logResult('Running comparison again to verify...', 'info');
                setTimeout(runDropdownTest, 500);
            })
            .catch(error => {
                logResult(`Error retrieving machine data: ${error.message}`, 'error');
            });
    }
    
    // Update the Asset Health dropdown with consistent formatting
    function updateAssetHealthDropdown(machines, getStringValue) {
        const dropdown = document.getElementById('machine-selector');
        if (!dropdown) {
            logResult('Asset Health dropdown not found', 'warning');
            return;
        }
        
        // Save the currently selected value
        const selectedValue = dropdown.value;
        
        // Clear existing options
        dropdown.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.textContent = 'Select a machine';
        defaultOption.value = '';
        dropdown.appendChild(defaultOption);
        
        // Add machine options with consistent formatting
        machines.forEach(machine => {
            const option = document.createElement('option');
            option.value = machine.id;
            
            // Format with spaces (same as we updated in the main function)
            const displayText = [
                getStringValue(machine.name),
                getStringValue(machine.location_business_name),
                getStringValue(machine.location_type),
                getStringValue(machine.sub_location)
            ].join(' ');
            
            option.textContent = displayText;
            dropdown.appendChild(option);
        });
        
        // Restore selected value
        dropdown.value = selectedValue;
        
        logResult('✓ Updated Asset Health dropdown', 'success');
    }
    
    // Update the Operations dropdown with the same consistent formatting
    function updateOperationsDropdown(machines, getStringValue) {
        const dropdown = document.getElementById('operations-machine-selector');
        if (!dropdown) {
            logResult('Operations dropdown not found', 'warning');
            return;
        }
        
        // Save the currently selected value
        const selectedValue = dropdown.value;
        
        // Clear existing options
        dropdown.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.textContent = 'Select a machine';
        defaultOption.value = '';
        dropdown.appendChild(defaultOption);
        
        // Add machine options with consistent formatting
        machines.forEach(machine => {
            const option = document.createElement('option');
            option.value = machine.id;
            
            // Format with spaces (same as we updated in the main function)
            const displayText = [
                getStringValue(machine.name),
                getStringValue(machine.location_business_name),
                getStringValue(machine.location_type),
                getStringValue(machine.sub_location)
            ].join(' ');
            
            option.textContent = displayText;
            dropdown.appendChild(option);
        });
        
        // Restore selected value
        dropdown.value = selectedValue;
        
        logResult('✓ Updated Operations dropdown', 'success');
    }
    
    // Add toggle button to the page
    function addToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.textContent = '🔄 Compare Dropdowns';
        toggleButton.style.cssText = `
            position: fixed;
            bottom: 120px; 
            right: 20px;
            z-index: 9998;
            background: #673AB7;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;
        
        document.body.appendChild(toggleButton);
        
        toggleButton.addEventListener('click', () => {
            // Remove existing test UI if present
            const existingUI = document.getElementById('dual-dropdown-test');
            if (existingUI) {
                existingUI.remove();
            } else {
                createTestUI();
                runDropdownTest();
            }
        });
    }
    
    // Run when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Dual Dropdown Test tool loaded!');
        setTimeout(addToggleButton, 1000); // Add button after a small delay
    });
    
    // If DOM is already loaded, add the button now
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        addToggleButton();
    }
})();
