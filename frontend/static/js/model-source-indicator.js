/**
 * Model Source Indicator
 * 
 * This script adds visual indicators to model cards to show if the data
 * is coming from the real database or mock data.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Function to add source indicators to model cards
    function addSourceIndicators() {
        // Find all elements with model data
        const modelElements = document.querySelectorAll('[data-model-id]');
        
        if (modelElements.length === 0) {
            // If no model elements found yet, try again in a moment
            setTimeout(addSourceIndicators, 500);
            return;
        }
        
        console.log(`Found ${modelElements.length} model elements to check for data sources`);
        
        // Process each model element
        modelElements.forEach(element => {
            // Check if this element already has a source indicator
            if (element.querySelector('.data-source-badge')) {
                return; // Skip if already processed
            }
            
            // Get the model data
            const modelId = element.getAttribute('data-model-id');
            const dataSource = element.getAttribute('data-source');
            
            if (!dataSource) {
                console.log(`Model ${modelId} has no data-source attribute`);
                return;
            }
            
            // Create a badge element to show the source
            const badge = document.createElement('span');
            badge.className = 'data-source-badge';
            badge.textContent = dataSource === 'mock' ? '(mock)' : '';
            
            // Style the badge
            badge.style.fontSize = '0.8em';
            badge.style.padding = '2px 6px';
            badge.style.borderRadius = '4px';
            badge.style.marginLeft = '5px';
            
            if (dataSource === 'mock') {
                badge.style.backgroundColor = '#ffecb3';
                badge.style.color = '#b78120';
                
                // Add the badge to the element
                const titleElement = element.querySelector('h3, h4, .card-title, .model-name') || element;
                titleElement.appendChild(badge);
                
                // Also add a class to the parent for CSS styling
                element.classList.add('mock-data-source');
            }
        });
    }
    
    // Initial run
    addSourceIndicators();
    
    // Also run when content changes (for dynamic content loading)
    const observer = new MutationObserver(function(mutations) {
        addSourceIndicators();
    });
    
    // Observe the entire document for content changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Add global styles
    const style = document.createElement('style');
    style.textContent = `
        .mock-data-source {
            border-left: 3px solid #ffecb3 !important;
        }
        
        .data-source-badge {
            display: inline-block;
            vertical-align: middle;
        }
    `;
    document.head.appendChild(style);
});
