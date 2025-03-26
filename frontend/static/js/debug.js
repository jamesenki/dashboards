/**
 * Debug script to help identify API issues
 */
console.log('Debug script loaded');

async function testWaterHeaterApi() {
  try {
    // Get the server hostname and port for direct API access
    const apiHost = window.location.hostname;
    const apiUrl = `http://${apiHost}:8006/api/water-heaters/`;
    
    console.log('Fetching water heaters directly from:', apiUrl);
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      mode: 'cors'
    });
    console.log('Response status:', response.status, response.statusText);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Water heaters data:', data);
      console.log('First water heater:', data[0]);
      
      // Check data structure for potential issues
      if (data && Array.isArray(data)) {
        console.log('Received array of', data.length, 'water heaters');
        
        // Check for required properties
        const firstItem = data[0];
        if (firstItem) {
          const expectedProps = ['id', 'name', 'type', 'status', 'current_temperature', 'target_temperature', 'mode', 'heater_status'];
          const missingProps = expectedProps.filter(prop => firstItem[prop] === undefined);
          
          if (missingProps.length > 0) {
            console.error('Missing required properties:', missingProps);
          } else {
            console.log('All required properties present');
          }
        }
      } else {
        console.error('Expected an array of water heaters but got:', typeof data);
      }
    } else {
      console.error('Failed to fetch water heaters:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('Error testing water heater API:', error);
  }
}

// Run the test when the script loads
testWaterHeaterApi();
