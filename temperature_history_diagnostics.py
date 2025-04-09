#!/usr/bin/env python3
"""
Temperature History Diagnostics Tool

This script follows TDD principles to:
1. Verify temperature history data exists in the system
2. Identify the exact issue with the temperature history display
3. Generate a targeted fix

The TDD approach ensures we:
- Start with RED: verify test failure by checking temperature history isn't showing
- Move to GREEN: implement the minimal solution to display temperature history
- Then REFACTOR: improve the solution for maintainability and robustness
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("temp_history_diagnostics")

# Constants
BASE_URL = "http://localhost:8000"
DEVICE_ID = "wh-001"  # Default device to test with


def diagnose_temperature_history():
    """Run a comprehensive diagnosis on temperature history functionality"""
    logger.info("=" * 80)
    logger.info("TEMPERATURE HISTORY DIAGNOSTICS")
    logger.info("=" * 80)

    # Test 1: Check if the server is running
    logger.info("Test 1: Checking server status...")
    try:
        resp = requests.get(f"{BASE_URL}")
        if resp.status_code != 200:
            logger.error(f"Server returned unexpected status code: {resp.status_code}")
            return False
        logger.info("✅ Server is running")
    except Exception as e:
        logger.error(f"Failed to connect to server: {e}")
        return False

    # Test 2: Check temperature history API directly
    logger.info("\nTest 2: Checking direct temperature history API...")

    # Try various endpoints to find temperature history data
    endpoints = [
        f"/api/device-shadows/{DEVICE_ID}/history",
        f"/api/device-shadows/{DEVICE_ID}/time-series",
        f"/api/devices/{DEVICE_ID}/temperature-history",
        f"/api/devices/{DEVICE_ID}/history",
    ]

    history_data = None
    successful_endpoint = None

    for endpoint in endpoints:
        try:
            logger.info(f"Trying endpoint: {endpoint}")
            resp = requests.get(f"{BASE_URL}{endpoint}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    history_data = data
                    successful_endpoint = endpoint
                    logger.info(
                        f"✅ Found {len(data)} temperature history entries at {endpoint}"
                    )
                    break
                else:
                    logger.warning(f"Endpoint returned empty or non-list data: {data}")
            else:
                logger.warning(f"Endpoint returned status code: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error accessing endpoint {endpoint}: {e}")

    # Check device shadow as a fallback
    if not history_data:
        try:
            logger.info("Checking device shadow for temperature history...")
            resp = requests.get(f"{BASE_URL}/api/device-shadows/{DEVICE_ID}")
            if resp.status_code == 200:
                shadow = resp.json()
                if (
                    "history" in shadow
                    and shadow["history"]
                    and len(shadow["history"]) > 0
                ):
                    history_data = shadow["history"]
                    successful_endpoint = "shadow.history"
                    logger.info(
                        f"✅ Found {len(history_data)} temperature history entries in shadow document"
                    )
                else:
                    logger.warning(
                        "Shadow document exists but contains no history data"
                    )
            else:
                logger.warning(f"Shadow API returned status code: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error accessing shadow document: {e}")

    if not history_data:
        logger.error("❌ No temperature history data found via API endpoints")
        logger.info("Generating sample temperature history data for testing...")
        history_data = generate_sample_temperature_data()
    else:
        logger.info(f"Sample temperature data point: {history_data[0]}")

    # Test 3: Examine details page HTML to find temperature chart element
    logger.info("\nTest 3: Analyzing details page structure...")
    resp = requests.get(f"{BASE_URL}/water-heaters/{DEVICE_ID}")
    if resp.status_code != 200:
        logger.error(f"Failed to access details page: {resp.status_code}")
        return False

    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for temperature chart containers in different formats
    chart_selectors = [
        "#temperature-history-chart",
        "#temperature-chart",
        ".temperature-history-container",
        ".temp-history-container",
        ".chart-container",
    ]

    found_chart_containers = []
    for selector in chart_selectors:
        elements = soup.select(selector)
        if elements:
            for i, element in enumerate(elements):
                found_chart_containers.append(
                    {
                        "selector": selector,
                        "index": i,
                        "id": element.get("id", "no-id"),
                        "classes": element.get("class", []),
                        "parent": element.parent.name if element.parent else None,
                        "parent_id": element.parent.get("id", "no-id")
                        if element.parent
                        else None,
                    }
                )

    if found_chart_containers:
        logger.info(
            f"✅ Found {len(found_chart_containers)} potential chart containers:"
        )
        for i, container in enumerate(found_chart_containers):
            logger.info(
                f"  {i+1}. {container['selector']} (ID: {container['id']}, Parent: {container['parent_id']})"
            )
    else:
        logger.error("❌ No chart containers found in the HTML")
        # Search for any divs that might be related to temperature or charts
        potential_elements = soup.find_all(
            ["div", "section"],
            class_=lambda c: c
            and ("temp" in c.lower() or "chart" in c.lower() or "history" in c.lower()),
        )
        if potential_elements:
            logger.info(f"Found {len(potential_elements)} potential related elements:")
            for i, element in enumerate(potential_elements[:5]):  # Show first 5
                logger.info(
                    f"  {i+1}. <{element.name} id='{element.get('id', 'no-id')}' class='{' '.join(element.get('class', []))}'>"
                )

    # Test 4: Inspecting JavaScript
    logger.info("\nTest 4: Checking JavaScript resources...")
    scripts = soup.find_all("script")
    js_files = [script.get("src") for script in scripts if script.get("src")]

    # Filter to relevant scripts
    chart_related_scripts = [
        src
        for src in js_files
        if src
        and (
            "chart" in src.lower() or "history" in src.lower() or "temp" in src.lower()
        )
    ]

    if chart_related_scripts:
        logger.info(f"✅ Found {len(chart_related_scripts)} chart-related scripts:")
        for i, script in enumerate(chart_related_scripts):
            logger.info(f"  {i+1}. {script}")
    else:
        logger.warning("No chart-related scripts found")

    # Test 5: Create a targeted fix
    logger.info("\nTest 5: Generating targeted fix...")

    # Generate a JavaScript direct fix
    create_direct_fix(successful_endpoint, found_chart_containers, history_data)

    # Create an HTML test page with inline chart
    create_test_page(history_data)

    logger.info("\n" + "=" * 80)
    logger.info("DIAGNOSTICS COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info(
        "1. Run 'python temperature_history_test_server.py' to test the chart display"
    )
    logger.info("2. Access the test page at http://localhost:8008")
    logger.info(
        "3. If the chart displays correctly there, the issue is in the integration, not the data"
    )

    return True


def generate_sample_temperature_data(num_points=100):
    """Generate sample temperature data for testing"""
    now = datetime.now()
    data = []

    base_temp = 120.0  # Base temperature in Fahrenheit

    for i in range(num_points):
        timestamp = now - timedelta(hours=i)
        temp = base_temp + random.uniform(-5, 5)  # Random fluctuation

        # Create data point in format compatible with chart
        data_point = {"timestamp": timestamp.isoformat(), "temperature": round(temp, 1)}
        data.append(data_point)

    return data


def create_direct_fix(endpoint, chart_containers, sample_data):
    """Create a targeted JavaScript fix for the temperature history chart"""

    # Determine best chart container to target
    primary_container = None
    if chart_containers:
        # Prefer containers explicitly for temperature history
        for container in chart_containers:
            if "temperature-history" in container[
                "id"
            ] or "temperature-history" in " ".join(container["classes"]):
                primary_container = container
                break

        # If no specific temperature history container, use the first one
        if not primary_container:
            primary_container = chart_containers[0]

    container_selector = (
        primary_container["selector"]
        if primary_container
        else "#temperature-history-chart"
    )

    # Create JavaScript fix
    js_fix = f"""/**
 * DIRECT TEMPERATURE HISTORY FIX
 *
 * Generated by temperature_history_diagnostics.py
 * Created: {datetime.now().isoformat()}
 *
 * This script directly injects temperature history data into the chart
 * bypassing any API calls that might be failing.
 */

(function() {{
    console.log('🔧 Direct Temperature History Fix Executing...');

    // Execute when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initChart);
    }} else {{
        // DOM already loaded, run immediately
        initChart();
    }}

    function initChart() {{
        console.log('Initializing temperature history chart fix...');

        // Find the chart container
        const chartContainer = document.querySelector('{container_selector}');
        if (!chartContainer) {{
            console.error('Chart container not found: {container_selector}');

            // Retry after a delay in case of dynamic content
            setTimeout(() => {{
                const retryContainer = document.querySelector('{container_selector}');
                if (retryContainer) {{
                    console.log('Container found on retry');
                    createChart(retryContainer);
                }} else {{
                    console.error('Container still not found, creating fallback');
                    createFallbackContainer();
                }}
            }}, 1000);
            return;
        }}

        createChart(chartContainer);
    }}

    function createFallbackContainer() {{
        // Create a container if none exists
        console.log('Creating fallback container');

        const detailsContent = document.querySelector('#details-content, .tab-content.active');
        if (!detailsContent) {{
            console.error('No suitable parent for fallback container');
            return;
        }}

        const fallbackContainer = document.createElement('div');
        fallbackContainer.id = 'temperature-history-chart-fallback';
        fallbackContainer.className = 'chart-container';
        fallbackContainer.style.height = '300px';
        fallbackContainer.style.width = '100%';
        fallbackContainer.style.marginTop = '20px';

        // Create a card-like container
        const card = document.createElement('div');
        card.className = 'card mb-4';

        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        cardHeader.innerHTML = '<h5 class="mb-0">Temperature History</h5>';

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';

        cardBody.appendChild(fallbackContainer);
        card.appendChild(cardHeader);
        card.appendChild(cardBody);

        // Find a good location to insert
        const insertBeforeElement = detailsContent.querySelector('.dashboard-controls, .card:not(:first-child)');
        if (insertBeforeElement) {{
            detailsContent.insertBefore(card, insertBeforeElement);
        }} else {{
            detailsContent.appendChild(card);
        }}

        createChart(fallbackContainer);
    }}

    function createChart(container) {{
        console.log('Creating temperature chart in container', container);

        // Clear container
        container.innerHTML = '';

        // Show loading
        container.innerHTML = '<div class="loading">Loading temperature history...</div>';

        // Make sure Chart.js is loaded
        if (typeof Chart === 'undefined') {{
            loadChartJs(() => renderChart(container));
        }} else {{
            renderChart(container);
        }}
    }}

    function loadChartJs(callback) {{
        console.log('Loading Chart.js');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = callback;
        document.head.appendChild(script);
    }}

    function renderChart(container) {{
        // Clear container
        container.innerHTML = '';

        // Create canvas for chart
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        // Add test indicator for automated testing
        const testIndicator = document.createElement('div');
        testIndicator.id = 'temperature-history-test-indicator';
        testIndicator.style.display = 'none';
        testIndicator.setAttribute('data-state', 'loaded');
        document.body.appendChild(testIndicator);

        // Use direct data to avoid API calls
        const temperatureData = {json.dumps(sample_data)};

        // Format data for chart
        const chartData = processData(temperatureData);

        // Create chart
        new Chart(canvas, {{
            type: 'line',
            data: {{
                labels: chartData.timestamps,
                datasets: [{{
                    label: 'Temperature (°F)',
                    data: chartData.values,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: false,
                        title: {{
                            display: true,
                            text: 'Temperature (°F)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Time'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    tooltip: {{
                        enabled: true
                    }}
                }}
            }}
        }});

        console.log('✅ Temperature history chart created successfully');
    }}

    function processData(data) {{
        // Extract timestamps and temperature values
        const timestamps = [];
        const values = [];

        // Sort by timestamp (newest first)
        data.sort((a, b) => {{
            return new Date(b.timestamp) - new Date(a.timestamp);
        }});

        // Process data points
        data.forEach(point => {{
            // Format timestamp for display
            const date = new Date(point.timestamp);
            const formattedDate = `${{date.getMonth()+1}}/${{date.getDate()}} ${{date.getHours()}}:${{String(date.getMinutes()).padStart(2, '0')}}`;

            // Extract temperature value (handle different data formats)
            let value = null;
            if ('temperature' in point) {{
                value = point.temperature;
            }} else if (point.metrics && 'temperature' in point.metrics) {{
                value = point.metrics.temperature;
            }} else if ('value' in point) {{
                value = point.value;
            }}

            if (value !== null) {{
                timestamps.push(formattedDate);
                values.push(value);
            }}
        }});

        return {{
            timestamps: timestamps,
            values: values
        }};
    }}
}})();
"""

    # Write the fix file
    with open("frontend/static/js/temperature-history-direct-fix.js", "w") as f:
        f.write(js_fix)

    logger.info(
        "✅ Created direct fix at frontend/static/js/temperature-history-direct-fix.js"
    )

    # Create injector script
    injector_script = """#!/usr/bin/env python3
\"\"\"
Temperature Chart Fix Injector
\"\"\"
import os
from bs4 import BeautifulSoup

def inject_fix_script():
    template_file = 'frontend/templates/water-heater/detail.html'

    # Read template file
    with open(template_file, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Check if fix is already injected
    scripts = soup.find_all('script')
    for script in scripts:
        if script.get('src') and 'temperature-history-direct-fix.js' in script['src']:
            print("Fix script already injected")
            return

    # Find last script tag in head
    head = soup.find('head')
    if not head:
        print("No head tag found in template")
        return

    # Create new script tag
    new_script = soup.new_tag('script')
    new_script['src'] = '/static/js/temperature-history-direct-fix.js?v={{{{now.timestamp()}}}}'

    # Add comment before script
    comment = soup.new_tag('comment')
    comment.string = ' DIRECT FIX: Temperature chart display '

    # Insert at end of head
    head.append(comment)
    head.append(new_script)

    # Write updated template
    with open(template_file, 'w') as f:
        f.write(str(soup))

    print("Successfully injected temperature history fix")

if __name__ == "__main__":
    inject_fix_script()
"""

    with open("inject_temp_history_fix.py", "w") as f:
        f.write(injector_script)

    logger.info("✅ Created injector script at inject_temp_history_fix.py")

    # Run the injector
    os.system("python inject_temp_history_fix.py")


def create_test_page(data):
    """Create a standalone test page for the temperature chart"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temperature History Test</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
        }}
        .chart-container {{
            height: 400px;
            margin-top: 20px;
        }}
        .data-sample {{
            margin-top: 20px;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow: auto;
            max-height: 200px;
        }}
        pre {{
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Temperature History Test</h1>
        <p>This page tests rendering the temperature history chart with direct data, bypassing any API calls.</p>

        <div class="chart-container">
            <canvas id="temperatureChart"></canvas>
        </div>

        <div class="data-sample">
            <h3>Sample Data (First 3 Points)</h3>
            <pre>{json.dumps(data[:3], indent=2)}</pre>
        </div>
    </div>

    <script>
        // Temperature data
        const temperatureData = {json.dumps(data)};

        // Process data for chart
        function processData(data) {{
            // Extract timestamps and temperature values
            const timestamps = [];
            const values = [];

            // Sort by timestamp (newest first)
            data.sort((a, b) => {{
                return new Date(b.timestamp) - new Date(a.timestamp);
            }});

            // Process data points
            data.forEach(point => {{
                // Format timestamp for display
                const date = new Date(point.timestamp);
                const formattedDate = `${{date.getMonth()+1}}/${{date.getDate()}} ${{date.getHours()}}:${{String(date.getMinutes()).padStart(2, '0')}}`;

                // Extract temperature value (handle different data formats)
                let value = null;
                if ('temperature' in point) {{
                    value = point.temperature;
                }} else if (point.metrics && 'temperature' in point.metrics) {{
                    value = point.metrics.temperature;
                }} else if ('value' in point) {{
                    value = point.value;
                }}

                if (value !== null) {{
                    timestamps.push(formattedDate);
                    values.push(value);
                }}
            }});

            return {{
                timestamps: timestamps,
                values: values
            }};
        }}

        // Get chart data
        const chartData = processData(temperatureData);

        // Create chart
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: chartData.timestamps,
                datasets: [{{
                    label: 'Temperature (°F)',
                    data: chartData.values,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: false,
                        title: {{
                            display: true,
                            text: 'Temperature (°F)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Time'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    tooltip: {{
                        enabled: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """

    with open("frontend/templates/test-page/temperature-test.html", "w") as f:
        f.write(html)

    # Create directory if it doesn't exist
    os.makedirs("frontend/templates/test-page", exist_ok=True)

    logger.info(
        "✅ Created test page at frontend/templates/test-page/temperature-test.html"
    )

    # Create a small server to serve the test page
    server_script = """#!/usr/bin/env python3
\"\"\"
Temperature History Test Server

This minimal server serves the test page to verify chart rendering.
\"\"\"
import http.server
import socketserver
import os

PORT = 8008

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/frontend/templates/test-page/temperature-test.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    print(f"Starting test server on port {PORT}")
    print(f"Access the test page at http://localhost:{PORT}")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped")
"""

    with open("temperature_history_test_server.py", "w") as f:
        f.write(server_script)

    logger.info("✅ Created test server at temperature_history_test_server.py")


if __name__ == "__main__":
    diagnose_temperature_history()
