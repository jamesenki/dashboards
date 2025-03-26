/**
 * Reload Monitor - Debug utility for tracking page refresh activity
 */
(function() {
    // Record page load in session storage to track refresh count
    try {
        let refreshCount = sessionStorage.getItem('refreshCount') || 0;
        refreshCount = parseInt(refreshCount) + 1;
        sessionStorage.setItem('refreshCount', refreshCount);
        
        console.log(`[RELOAD-MONITOR] Page load #${refreshCount} detected`);
        console.log(`[RELOAD-MONITOR] Page URL: ${window.location.href}`);
        console.log(`[RELOAD-MONITOR] Hash: ${window.location.hash}`);
        
        // Log all script elements that have been loaded
        const scripts = document.querySelectorAll('script');
        console.log(`[RELOAD-MONITOR] Total scripts loaded: ${scripts.length}`);
        scripts.forEach((script, index) => {
            console.log(`[RELOAD-MONITOR] Script #${index}: ${script.src || 'inline script'}`);
        });
        
        // Monitor for any redirect or location changes
        const originalAssign = window.location.assign;
        window.location.assign = function(url) {
            console.log(`[RELOAD-MONITOR] location.assign called with: ${url}`);
            return originalAssign.apply(this, arguments);
        };
        
        const originalReplace = window.location.replace;
        window.location.replace = function(url) {
            console.log(`[RELOAD-MONITOR] location.replace called with: ${url}`);
            return originalReplace.apply(this, arguments);
        };
        
        // Override reload
        const originalReload = window.location.reload;
        window.location.reload = function() {
            console.log(`[RELOAD-MONITOR] location.reload called`);
            return originalReload.apply(this, arguments);
        };
        
        // Setup a global error handler
        window.addEventListener('error', function(event) {
            console.error(`[RELOAD-MONITOR] Error: ${event.message} at ${event.filename}:${event.lineno}`);
        });
        
        // Report if this was loaded after a hashchange
        window.addEventListener('hashchange', function(event) {
            console.log(`[RELOAD-MONITOR] Hash changed from ${event.oldURL} to ${event.newURL}`);
        });

        // Create a visible indicator on the page
        const indicator = document.createElement('div');
        indicator.style.position = 'fixed';
        indicator.style.top = '5px';
        indicator.style.right = '5px';
        indicator.style.background = 'rgba(255,0,0,0.7)';
        indicator.style.color = 'white';
        indicator.style.padding = '5px 10px';
        indicator.style.borderRadius = '4px';
        indicator.style.zIndex = '9999';
        indicator.style.fontWeight = 'bold';
        indicator.textContent = `Reload #${refreshCount}`;
        
        // Add indicator when DOM is ready
        if (document.body) {
            document.body.appendChild(indicator);
        } else {
            window.addEventListener('DOMContentLoaded', function() {
                document.body.appendChild(indicator);
            });
        }
    } catch (e) {
        console.error(`[RELOAD-MONITOR] Error in monitor script: ${e.message}`);
    }
})();
