/**
 * Gauge Consistency Test
 * This script checks that all gauge charts on the dashboard have consistent styling and behavior
 */
(function() {
    // Create test UI
    function createTestUI() {
        const testUI = document.createElement('div');
        testUI.id = 'gauge-consistency-test';
        testUI.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
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
                <h2 style="margin: 0; color: #2196F3;">Gauge Consistency Test</h2>
                <button id="close-gauge-test" style="background: #555; border: none; color: white; padding: 3px 8px; cursor: pointer;">×</button>
            </div>
            <div style="margin-bottom: 10px;">
                <button id="run-gauge-test" style="background: #4CAF50; color: white; border: none; padding: 5px 10px; margin-right: 5px; cursor: pointer;">Run Test</button>
                <button id="fix-gauge-issues" style="background: #FF9800; color: white; border: none; padding: 5px 10px; cursor: pointer;">Fix Issues</button>
            </div>
            <div id="gauge-test-results" style="margin-top: 10px;"></div>
        `;
        
        document.body.appendChild(testUI);
        
        // Add event listeners
        document.getElementById('close-gauge-test').addEventListener('click', () => {
            testUI.remove();
        });
        
        document.getElementById('run-gauge-test').addEventListener('click', runGaugeTest);
        document.getElementById('fix-gauge-issues').addEventListener('click', fixGaugeIssues);
    }
    
    // Run the gauge consistency test
    function runGaugeTest() {
        const resultsDiv = document.getElementById('gauge-test-results');
        resultsDiv.innerHTML = '<p>Running test...</p>';
        
        // Get all gauge containers on the page
        const gaugeContainers = document.querySelectorAll('.gauge-container');
        
        if (!gaugeContainers.length) {
            resultsDiv.innerHTML = '<p style="color: orange;">No gauge containers found on the page!</p>';
            return;
        }
        
        logResult(`Found ${gaugeContainers.length} gauge containers`);
        
        // Test results
        const results = {
            containers: [],
            consistencyIssues: [],
            missingElements: []
        };
        
        // Check each gauge container
        gaugeContainers.forEach((container, index) => {
            const id = container.id || `unnamed-gauge-${index}`;
            const parentPanel = container.closest('.gauge-panel');
            const needle = container.querySelector('.gauge-needle');
            const valueEl = parentPanel ? parentPanel.querySelector('.gauge-value') : null;
            const titleEl = parentPanel ? parentPanel.querySelector('.gauge-title') : null;
            const limitsEl = parentPanel ? parentPanel.querySelector('.gauge-limits') : null;
            
            // Get computed styles
            const containerStyle = window.getComputedStyle(container);
            
            // Store container details
            results.containers.push({
                id,
                width: containerStyle.width,
                height: containerStyle.height,
                borderRadius: containerStyle.borderRadius,
                background: containerStyle.background,
                hasNeedle: !!needle,
                hasValue: !!valueEl,
                hasTitle: !!titleEl,
                hasLimits: !!limitsEl,
                needleStyle: needle ? window.getComputedStyle(needle) : null,
                valueStyle: valueEl ? window.getComputedStyle(valueEl) : null,
                titleStyle: titleEl ? window.getComputedStyle(titleEl) : null,
                limitsStyle: limitsEl ? window.getComputedStyle(limitsEl) : null
            });
            
            // Check for missing elements
            if (!needle) {
                results.missingElements.push(`${id}: Missing needle element`);
            }
            if (!valueEl) {
                results.missingElements.push(`${id}: Missing value element`);
            }
            if (!titleEl) {
                results.missingElements.push(`${id}: Missing title element`);
            }
            if (!limitsEl) {
                results.missingElements.push(`${id}: Missing limits element`);
            }
        });
        
        // Check for consistency issues
        if (results.containers.length > 1) {
            const reference = results.containers[0];
            
            for (let i = 1; i < results.containers.length; i++) {
                const current = results.containers[i];
                
                // Check container dimensions
                if (reference.width !== current.width || reference.height !== current.height) {
                    results.consistencyIssues.push(`${current.id}: Dimensions (${current.width} x ${current.height}) don't match reference (${reference.width} x ${reference.height})`);
                }
                
                // Check border radius
                if (reference.borderRadius !== current.borderRadius) {
                    results.consistencyIssues.push(`${current.id}: Border radius (${current.borderRadius}) doesn't match reference (${reference.borderRadius})`);
                }
                
                // Check background style
                if (reference.background !== current.background) {
                    results.consistencyIssues.push(`${current.id}: Background style doesn't match reference`);
                }
                
                // Check needle properties if both have needles
                if (reference.hasNeedle && current.hasNeedle) {
                    if (reference.needleStyle.backgroundColor !== current.needleStyle.backgroundColor) {
                        results.consistencyIssues.push(`${current.id}: Needle color doesn't match reference`);
                    }
                    if (reference.needleStyle.height !== current.needleStyle.height) {
                        results.consistencyIssues.push(`${current.id}: Needle height doesn't match reference`);
                    }
                }
                
                // Check value text styling if both have values
                if (reference.hasValue && current.hasValue) {
                    if (reference.valueStyle.fontSize !== current.valueStyle.fontSize) {
                        results.consistencyIssues.push(`${current.id}: Value font size (${current.valueStyle.fontSize}) doesn't match reference (${reference.valueStyle.fontSize})`);
                    }
                    if (reference.valueStyle.fontWeight !== current.valueStyle.fontWeight) {
                        results.consistencyIssues.push(`${current.id}: Value font weight doesn't match reference`);
                    }
                }
                
                // Check title text styling if both have titles
                if (reference.hasTitle && current.hasTitle) {
                    if (reference.titleStyle.fontSize !== current.titleStyle.fontSize) {
                        results.consistencyIssues.push(`${current.id}: Title font size doesn't match reference`);
                    }
                    if (reference.titleStyle.fontWeight !== current.titleStyle.fontWeight) {
                        results.consistencyIssues.push(`${current.id}: Title font weight doesn't match reference`);
                    }
                }
            }
        }
        
        // Display results
        resultsDiv.innerHTML = '';
        
        if (results.missingElements.length === 0 && results.consistencyIssues.length === 0) {
            logResult('✅ All gauges have consistent formatting', 'success');
        } else {
            if (results.missingElements.length > 0) {
                logResult('⚠️ Missing Elements:', 'warning');
                results.missingElements.forEach(issue => {
                    logResult(`- ${issue}`, 'warning');
                });
            }
            
            if (results.consistencyIssues.length > 0) {
                logResult('⚠️ Consistency Issues:', 'warning');
                results.consistencyIssues.forEach(issue => {
                    logResult(`- ${issue}`, 'warning');
                });
            }
        }
        
        // Show details for each gauge
        logResult('\nGauge Details:', 'info');
        results.containers.forEach(gauge => {
            logResult(`${gauge.id}:`, 'info');
            logResult(`- Size: ${gauge.width} x ${gauge.height}`, 'detail');
            logResult(`- Has Needle: ${gauge.hasNeedle}`, 'detail');
            logResult(`- Has Value: ${gauge.hasValue}`, 'detail');
            logResult(`- Has Title: ${gauge.hasTitle}`, 'detail');
            logResult(`- Has Limits: ${gauge.hasLimits}`, 'detail');
        });
        
        // Store results for fix function
        window.gaugeTestResults = results;
    }
    
    // Log a result to the results div
    function logResult(message, type = 'normal') {
        const resultsDiv = document.getElementById('gauge-test-results');
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
    
    // Fix gauge consistency issues
    function fixGaugeIssues() {
        const resultsDiv = document.getElementById('gauge-test-results');
        resultsDiv.innerHTML = '<p>Applying fixes...</p>';
        
        // Get all gauge containers on the page
        const gaugeContainers = document.querySelectorAll('.gauge-container');
        
        if (!gaugeContainers.length) {
            logResult('No gauge containers found on the page!', 'warning');
            return;
        }
        
        // Create a reference style from the first gauge or use defaults
        const referenceGauge = gaugeContainers[0];
        const referencePanel = referenceGauge.closest('.gauge-panel');
        
        // Apply fixes to all gauges
        gaugeContainers.forEach(container => {
            // Ensure container has consistent styling
            container.style.width = '120px';
            container.style.height = '120px';
            container.style.borderRadius = '50%';
            container.style.background = 'linear-gradient(165deg, #444 0%, #222 40%, #000 100%)';
            container.style.position = 'relative';
            container.style.margin = '10px auto';
            container.style.boxShadow = '0 0 10px rgba(0,0,0,0.2), inset 0 0 10px rgba(0,0,0,0.2)';
            
            // Make sure there's a needle
            let needle = container.querySelector('.gauge-needle');
            if (!needle) {
                needle = document.createElement('div');
                needle.className = 'gauge-needle';
                container.appendChild(needle);
            }
            
            // Style the needle
            needle.style.position = 'absolute';
            needle.style.width = '4px';
            needle.style.height = '50px';
            needle.style.background = '#ff5722';
            needle.style.bottom = '50%';
            needle.style.left = 'calc(50% - 2px)';
            needle.style.transformOrigin = 'bottom center';
            needle.style.transform = 'rotate(0deg)';
            needle.style.borderRadius = '4px 4px 0 0';
            needle.style.boxShadow = '0 0 5px rgba(0,0,0,0.5)';
            needle.style.zIndex = '2';
            
            // Add a center pivot point
            let pivot = container.querySelector('.gauge-pivot');
            if (!pivot) {
                pivot = document.createElement('div');
                pivot.className = 'gauge-pivot';
                container.appendChild(pivot);
            }
            
            pivot.style.position = 'absolute';
            pivot.style.width = '12px';
            pivot.style.height = '12px';
            pivot.style.background = '#555';
            pivot.style.borderRadius = '50%';
            pivot.style.bottom = 'calc(50% - 6px)';
            pivot.style.left = 'calc(50% - 6px)';
            pivot.style.boxShadow = '0 0 5px rgba(0,0,0,0.5)';
            pivot.style.zIndex = '3';
            
            // Find or create gauge panel parent
            let panel = container.closest('.gauge-panel');
            if (!panel) {
                panel = document.createElement('div');
                panel.className = 'gauge-panel';
                container.parentNode.insertBefore(panel, container);
                panel.appendChild(container);
            }
            
            // Style the gauge panel
            panel.style.textAlign = 'center';
            panel.style.padding = '10px';
            panel.style.background = 'rgba(255, 255, 255, 0.05)';
            panel.style.borderRadius = '5px';
            panel.style.margin = '10px';
            panel.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
            
            // Find or create title
            let title = panel.querySelector('.gauge-title');
            if (!title) {
                title = document.createElement('div');
                title.className = 'gauge-title';
                panel.insertBefore(title, panel.firstChild);
                
                // Set a default title based on ID
                if (container.id) {
                    let titleText = container.id.replace('-gauge', '').replace(/-/g, ' ');
                    titleText = titleText.split(' ').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' ');
                    title.textContent = titleText;
                } else {
                    title.textContent = 'Gauge';
                }
            }
            
            // Style the title
            title.style.fontWeight = 'bold';
            title.style.fontSize = '14px';
            title.style.marginBottom = '5px';
            title.style.color = '#fff';
            
            // Find or create value display
            let value = panel.querySelector('.gauge-value');
            if (!value) {
                value = document.createElement('div');
                value.className = 'gauge-value';
                panel.insertBefore(value, container.nextSibling);
                value.textContent = '0';
            }
            
            // Style the value
            value.style.fontSize = '20px';
            value.style.fontWeight = 'bold';
            value.style.margin = '5px 0';
            value.style.color = '#fff';
            
            // Find or create limits
            let limits = panel.querySelector('.gauge-limits');
            if (!limits) {
                limits = document.createElement('div');
                limits.className = 'gauge-limits';
                panel.appendChild(limits);
                limits.innerHTML = '<span class="min-limit">0</span><span class="max-limit">100</span>';
            }
            
            // Style the limits
            limits.style.display = 'flex';
            limits.style.justifyContent = 'space-between';
            limits.style.fontSize = '12px';
            limits.style.color = '#aaa';
            limits.style.padding = '0 10px';
        });
        
        // Run the test again to confirm fixes
        logResult('✅ Applied consistent formatting to all gauges', 'success');
        logResult('Running test again to verify...', 'info');
        setTimeout(runGaugeTest, 500);
    }
    
    // Add toggle button to the page
    function addToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.textContent = '📊 Test Gauges';
        toggleButton.style.cssText = `
            position: fixed;
            bottom: 70px; 
            right: 20px;
            z-index: 9998;
            background: #2196F3;
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
            const existingUI = document.getElementById('gauge-consistency-test');
            if (existingUI) {
                existingUI.remove();
            } else {
                createTestUI();
                runGaugeTest();
            }
        });
    }
    
    // Run when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Gauge Consistency Test tool loaded!');
        setTimeout(addToggleButton, 1000); // Add button after a small delay
    });
    
    // If DOM is already loaded, add the button now
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        addToggleButton();
    }
})();
