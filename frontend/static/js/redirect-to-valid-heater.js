/**
 * Helper to provide a button to a valid water heater detail page
 * This handles the case where water heater IDs change on server restart
 *
 * IMPORTANT: This script should NEVER automatically redirect, only provide
 * a button for the user to click manually if they want to navigate
 */
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Only run this on the main water heaters list page
        if (window.location.pathname !== '/' && window.location.pathname !== '/water-heaters') {
            console.log('Not on water heaters list page, skipping helper button');
            return;
        }

        const api = new ApiClient();

        // Get the first available water heater
        const heaters = await api.request('GET', '/water-heaters/');

        if (heaters && heaters.length > 0) {
            const firstHeaterId = heaters[0].id;

            // Create a button to navigate to a valid water heater
            const container = document.querySelector('.container') || document.body;
            const alertBox = document.createElement('div');
            alertBox.className = 'alert alert-info mt-4';
            alertBox.innerHTML = `
                <h4>Testing Water Heater History Dashboard</h4>
                <p>Click the button below to access a valid water heater detail page with history data:</p>
                <a href="/water-heaters/${firstHeaterId}" class="btn btn-primary">
                    View Water Heater ${firstHeaterId}
                </a>
            `;

            // Insert at the top of the container
            container.insertBefore(alertBox, container.firstChild);

            console.log(`Added button to navigate to water heater: ${firstHeaterId}`);
        } else {
            console.error('No water heaters found in the system');
        }
    } catch (error) {
        console.error('Error setting up navigation helper:', error);
    }
});
