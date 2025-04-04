/**
 * Debug Helper Script
 * This script helps diagnose UI issues by inserting visible indicators
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add debug indicator to show this script is loaded
    const debugDiv = document.createElement('div');
    debugDiv.style.position = 'fixed';
    debugDiv.style.top = '10px';
    debugDiv.style.right = '10px';
    debugDiv.style.backgroundColor = 'red';
    debugDiv.style.color = 'white';
    debugDiv.style.padding = '5px';
    debugDiv.style.zIndex = '9999';
    debugDiv.textContent = 'DEBUG ACTIVE';
    document.body.appendChild(debugDiv);

    // Create a function to check and report on tab system
    window.debugTabs = function() {
        console.log('DEBUG: Checking tabs...');

        // Check if we're on a detail page with tabs
        const tabButtons = document.querySelectorAll('.tab-btn');
        console.log(`DEBUG: Found ${tabButtons.length} tab buttons`);

        tabButtons.forEach((btn, index) => {
            console.log(`DEBUG: Tab ${index + 1}: ${btn.textContent} (${btn.id})`);
            console.log(`DEBUG: Active state: ${btn.classList.contains('active')}`);
        });

        // Check tab content
        const tabContents = document.querySelectorAll('.tab-content');
        console.log(`DEBUG: Found ${tabContents.length} tab content elements`);

        tabContents.forEach((content, index) => {
            console.log(`DEBUG: Content ${index + 1}: ${content.id}`);
            console.log(`DEBUG: Display state: ${content.classList.contains('active') ? 'visible' : 'hidden'}`);
        });

        // Check water heater operations dashboard
        const opsDashboard = document.getElementById('water-heater-operations-dashboard');
        if (opsDashboard) {
            console.log('DEBUG: Operations dashboard element found');
            console.log(`DEBUG: Content: "${opsDashboard.innerHTML.substring(0, 50)}..."`);
        } else {
            console.log('DEBUG: Operations dashboard element NOT found');
        }
    };

    // Auto-debug if we detect a water heater page
    if (window.location.pathname.includes('/water-heaters/')) {
        console.log('DEBUG: Detected water heater detail page');

        // Allow time for other scripts to initialize
        setTimeout(() => {
            window.debugTabs();

            // DISABLED: Automatic tab activation removed to prevent unwanted navigation
            // This followed TDD principles - tests should define behavior, not the debug scripts
            // The operations tab should only activate when explicitly clicked by the user

            // Display available tabs without forcing navigation
            const opsTabBtn = document.getElementById('operations-tab-btn');
            if (opsTabBtn) {
                console.log('DEBUG: Operations tab available but not auto-activated');
            }
        }, 1000);
    }
});
