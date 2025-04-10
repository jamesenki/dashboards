/**
 * Performance Optimizer
 *
 * Improves page load and rendering performance by:
 * - Optimizing DOM operations
 * - Implementing efficient resource loading
 * - Deferring non-critical operations
 * - Reducing unnecessary reflows and repaints
 */

(function() {
  'use strict';

  // Performance metrics tracking
  const metrics = {
    pageLoadStart: Date.now(),
    domContentLoaded: 0,
    fullLoad: 0,
    tabSwitchTimes: {},
    dataLoadTimes: {},
    renderTimes: {}
  };

  // Initialize as soon as possible
  initialize();

  function initialize() {
    // Capture page load metrics
    document.addEventListener('DOMContentLoaded', () => {
      metrics.domContentLoaded = Date.now() - metrics.pageLoadStart;
      console.log(`🚀 DOM Content Loaded in ${metrics.domContentLoaded}ms`);

      // Run DOM optimizations
      optimizeDom();
    });

    window.addEventListener('load', () => {
      metrics.fullLoad = Date.now() - metrics.pageLoadStart;
      console.log(`🚀 Page fully loaded in ${metrics.fullLoad}ms`);

      // Run post-load optimizations
      optimizeAfterLoad();
    });

    // Set up performance observers if available
    setupPerformanceObservers();

    // Listen for tab changes to track performance
    if (window.OptimizedTabManager) {
      window.OptimizedTabManager.addEventListener('tabActivated', (tab) => {
        const switchStart = Date.now();

        // Record after a short delay to capture rendering time
        setTimeout(() => {
          const switchTime = Date.now() - switchStart;
          metrics.tabSwitchTimes[tab.id] = switchTime;
          console.log(`🚀 Tab ${tab.id} activated in ${switchTime}ms`);
        }, 50);
      });
    }
  }

  function optimizeDom() {
    // Defer image loading for images outside viewport
    lazyLoadImages();

    // Optimize heavy DOM elements
    optimizeHeavyElements();

    // Add passive event listeners where appropriate
    usePassiveEventListeners();
  }

  function optimizeAfterLoad() {
    // Clean up unused event listeners
    removeRedundantEventListeners();

    // Pre-connect to required origins
    addResourceHints();

    // Remove any unnecessary scripts or styles
    cleanupResources();
  }

  function lazyLoadImages() {
    // Check if IntersectionObserver is available
    if (!('IntersectionObserver' in window)) return;

    // Find all images that aren't already loaded
    const images = document.querySelectorAll('img[data-src]:not([loading="lazy"])');

    // Set up observer
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          imageObserver.unobserve(img);
        }
      });
    });

    // Observe each image
    images.forEach(img => {
      imageObserver.observe(img);
    });

    console.log(`🚀 Lazy loading set up for ${images.length} images`);
  }

  function optimizeHeavyElements() {
    // Find large tables or lists that could benefit from virtualization
    const largeTables = document.querySelectorAll('table > tbody > tr, ul > li, ol > li');

    if (largeTables.length > 100) {
      console.log(`🚀 Found ${largeTables.length} list/table items, consider virtualization`);

      // Apply minimal virtualization for large lists
      const containers = new Set(Array.from(largeTables).map(item => item.parentElement));

      containers.forEach(container => {
        if (container.children.length > 50) {
          // Only show a portion of items
          Array.from(container.children).forEach((child, index) => {
            if (index > 50) {
              child.style.display = 'none';
              child.classList.add('virtualized');
            }
          });

          // Add load more functionality
          const loadMoreBtn = document.createElement('button');
          loadMoreBtn.textContent = 'Load More';
          loadMoreBtn.className = 'load-more-btn';
          loadMoreBtn.style.margin = '10px 0';
          loadMoreBtn.style.padding = '5px 10px';

          loadMoreBtn.addEventListener('click', () => {
            const hiddenItems = container.querySelectorAll('.virtualized');

            // Show next batch
            Array.from(hiddenItems).slice(0, 20).forEach(item => {
              item.style.display = '';
              item.classList.remove('virtualized');
            });

            // Hide button if no more items
            if (container.querySelectorAll('.virtualized').length === 0) {
              loadMoreBtn.style.display = 'none';
            }
          });

          container.parentNode.insertBefore(loadMoreBtn, container.nextSibling);
        }
      });
    }
  }

  function usePassiveEventListeners() {
    // Add passive flag to non-critical event listeners
    const passiveListenerOpts = { passive: true };

    // Find scroll containers
    const scrollContainers = document.querySelectorAll('.scrollable, [data-scroll], .overflow-auto');

    scrollContainers.forEach(container => {
      const existingListeners = getEventListeners(container);

      // Re-register scroll events as passive
      if (existingListeners && existingListeners.scroll) {
        existingListeners.scroll.forEach(listener => {
          container.removeEventListener('scroll', listener.listener);
          container.addEventListener('scroll', listener.listener, passiveListenerOpts);
        });
      }
    });
  }

  function getEventListeners(element) {
    // This is a stub function since we can't actually access event listeners
    // In real implementations, you'd need to track listeners when adding them
    return null;
  }

  function removeRedundantEventListeners() {
    // Clean up any listeners that might no longer be needed
    // Since we can't directly access listeners, we apply this to common patterns

    // Remove scroll listeners from elements not in viewport
    const scrollContainers = document.querySelectorAll('.scrollable, [data-scroll]');

    scrollContainers.forEach(container => {
      const rect = container.getBoundingClientRect();
      const isVisible = (
        rect.top >= -rect.height &&
        rect.left >= -rect.width &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) + rect.height &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth) + rect.width
      );

      if (!isVisible) {
        container.dataset.scrollPaused = 'true';
      }
    });
  }

  function addResourceHints() {
    // Add preconnect for commonly used origins
    const origins = [
      window.location.origin, // Current origin
      'https://cdn.jsdelivr.net', // Common CDN
      'https://www.googletagmanager.com' // Analytics
    ];

    origins.forEach(origin => {
      if (!document.querySelector(`link[rel="preconnect"][href="${origin}"]`)) {
        const link = document.createElement('link');
        link.rel = 'preconnect';
        link.href = origin;
        document.head.appendChild(link);
      }
    });
  }

  function cleanupResources() {
    // Clean up any redundant styles or scripts

    // Find unused styles
    const styleTags = document.querySelectorAll('style');
    styleTags.forEach(style => {
      // Simple check for empty or commented-out styles
      if (!style.textContent.trim() || style.textContent.trim().startsWith('/*')) {
        style.remove();
      }
    });

    // Find duplicate scripts (same src)
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    const seenSrcs = new Set();

    scripts.forEach(script => {
      const src = script.src;
      if (seenSrcs.has(src)) {
        // Duplicate script
        script.remove();
      } else {
        seenSrcs.add(src);
      }
    });
  }

  function setupPerformanceObservers() {
    // Set up performance observers if available
    if (!('PerformanceObserver' in window)) return;

    try {
      // Observe paint timing
      const paintObserver = new PerformanceObserver((list) => {
        const paintMetrics = {};

        for (const entry of list.getEntries()) {
          paintMetrics[entry.name] = entry.startTime;
        }

        if (paintMetrics['first-paint']) {
          console.log(`🚀 First Paint: ${Math.round(paintMetrics['first-paint'])}ms`);
        }

        if (paintMetrics['first-contentful-paint']) {
          console.log(`🚀 First Contentful Paint: ${Math.round(paintMetrics['first-contentful-paint'])}ms`);
        }
      });

      paintObserver.observe({ entryTypes: ['paint'] });

      // Observe long tasks
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.warn(`⚠️ Long Task detected: ${Math.round(entry.duration)}ms`);
        }
      });

      longTaskObserver.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      console.log('Performance observers not fully supported');
    }
  }

  // Expose public API
  window.PerformanceOptimizer = {
    getMetrics: () => ({ ...metrics }),
    optimizeDom,
    lazyLoadImages
  };
})();
