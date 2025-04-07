/**
 * Data Source Indicator Module
 *
 * This module adds a visual indicator showing which data source is being used
 * by the application (PostgreSQL, SQLite, or Mock data).
 */

// Self-executing function to avoid polluting global namespace
(function() {
    // Create indicator element
    function createIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'data-source-indicator';
        indicator.classList.add('data-source-indicator');

        // Style the indicator
        Object.assign(indicator.style, {
            position: 'fixed',
            bottom: '10px',
            right: '10px',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold',
            zIndex: '9999',
            cursor: 'pointer',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            transition: 'opacity 0.3s'
        });

        // Add toggle functionality
        indicator.addEventListener('click', function() {
            if (indicator.classList.contains('minimized')) {
                indicator.classList.remove('minimized');
                indicator.style.opacity = '1';
                indicator.textContent = indicator.getAttribute('data-full-text');
            } else {
                indicator.classList.add('minimized');
                indicator.style.opacity = '0.6';
                indicator.textContent = 'DS';
            }
        });

        // Add to document
        document.body.appendChild(indicator);
        return indicator;
    }

    // Function to update the indicator based on the data source
    function updateIndicator(indicator, dataSource, reason) {
        // Set full text for expanded view
        const fullText = `Data: ${dataSource}${reason ? ` (${reason})` : ''}`;
        indicator.setAttribute('data-full-text', fullText);

        // Set current text based on minimized state
        if (indicator.classList.contains('minimized')) {
            indicator.textContent = 'DS';
        } else {
            indicator.textContent = fullText;
        }

        // Set color based on data source
        let bgColor, textColor;
        switch(dataSource.toLowerCase()) {
            case 'postgres':
            case 'postgresql':
                bgColor = '#336791'; // PostgreSQL blue
                textColor = 'white';
                break;
            case 'sqlite':
                bgColor = '#0f80cc'; // SQLite blue
                textColor = 'white';
                break;
            case 'mock':
                bgColor = '#ffa500'; // Orange for mock data
                textColor = 'black';
                break;
            default:
                bgColor = '#999999'; // Gray for unknown
                textColor = 'white';
        }

        indicator.style.backgroundColor = bgColor;
        indicator.style.color = textColor;
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        const indicator = createIndicator();

        // Start minimized
        indicator.classList.add('minimized');
        indicator.textContent = 'DS';
        indicator.style.opacity = '0.6';

        // Set default unknown state
        updateIndicator(indicator, 'Unknown', '');

        // Fetch data source information from API
        fetch('/api/health/data-source')
            .then(response => response.json())
            .then(data => {
                // Update indicator with real data
                const source = data.data_source || 'Unknown';
                const reason = data.reason || '';
                updateIndicator(indicator, source, reason);
            })
            .catch(error => {
                console.error('Error fetching data source info:', error);
                updateIndicator(indicator, 'Error', 'Could not determine');
            });
    });
})();
