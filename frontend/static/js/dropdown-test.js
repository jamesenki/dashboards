// Test script to demonstrate dropdown formatting
(function() {
    // Sample machine data from API
    const machines = [
        {
            "id":"vm-67f187fe",
            "name":"PolarDelight - FrostyPlus 67f1",
            "location_business_name":"LAX Terminal",
            "location_type":"TRANSPORTATION",
            "sub_location":"CAFETERIA",
            "location":"Building C - Bathroom",
            "status":"OPERATIONAL"
        },
        {
            "id":"vm-2e2e5dac",
            "name":"PolarDelight - CoolVend 2e2e",
            "location_business_name":"Red Rocks Amphitheater",
            "location_type":"OTHER",
            "sub_location":"BREAK_ROOM",
            "location":"Warehouse - Suite 101",
            "status":"NEEDS_RESTOCK"
        },
        {
            "id":"vm-249424e9",
            "name":"PolarDelight - AutoSell 2494",
            "location_business_name":"Adobe Offices",
            "location_type":"OFFICE",
            "sub_location":"CAFETERIA",
            "location":"East Tower - Suite 101",
            "status":"NEEDS_RESTOCK"
        },
        {
            "id":"vm-4c76c181",
            "name":"PolarDelight - SuperVend 4c76",
            "location_business_name":"Wendy's",
            "location_type":"FAST_FOOD",
            "sub_location":"DINING_AREA",
            "location":"West Tower - Boiler Room",
            "status":"OPERATIONAL"
        },
        {
            "id":"vm-e683c97c",
            "name":"PolarDelight - SuperVend e683",
            "location_business_name":"Port Authority Bus Terminal",
            "location_type":"TRANSPORTATION",
            "sub_location":"DINING_AREA", 
            "location":"South Wing - Laundry Room",
            "status":"OPERATIONAL"
        }
    ];

    // Helper function to get a proper string value (same as in original code)
    function getStringValue(value) {
        if (value === null || value === undefined) return 'Unknown';
        
        // If it's already a string, just return it
        if (typeof value === 'string') return value;
        
        // If it's an object with a value property (like an enum), get that
        if (typeof value === 'object' && value.value) return value.value;
        
        // Otherwise convert to string
        return String(value);
    }

    // Test with various edge cases
    const testCases = [
        // Normal case (all fields present)
        machines[0],
        
        // Case with missing fields
        {
            "id":"vm-test1",
            "name":"Test Machine 1",
            "location_business_name": null,
            "location_type":"OFFICE"
            // Missing sub_location
        },
        
        // Case with different data types
        {
            "id":"vm-test2",
            "name":"Test Machine 2",
            "location_business_name": { "value": "Complex Object" },
            "location_type": 123,  // Number
            "sub_location": true   // Boolean
        },
        
        // Case with special characters
        {
            "id":"vm-test3",
            "name":"Test | Machine | 3",
            "location_business_name": "Business & Name",
            "location_type": "Type-With-Dashes",
            "sub_location": "Sub_Location_Underscores"
        }
    ];

    console.log("=== DROPDOWN FORMAT TEST RESULTS ===");
    
    // Process each test case
    testCases.forEach((machine, index) => {
        // Format as in the original function
        const displayText = [
            getStringValue(machine.name),
            getStringValue(machine.location_business_name),
            getStringValue(machine.location_type),
            getStringValue(machine.sub_location)
        ].join(' | ');
        
        console.log(`\nTest Case ${index + 1}:`);
        console.log(`Machine ID: ${machine.id}`);
        console.log(`Individual Values:`);
        console.log(`  - name: "${getStringValue(machine.name)}"`);
        console.log(`  - location_business_name: "${getStringValue(machine.location_business_name)}"`);
        console.log(`  - location_type: "${getStringValue(machine.location_type)}"`);
        console.log(`  - sub_location: "${getStringValue(machine.sub_location)}"`);
        console.log(`\nFormatted Output:`);
        console.log(`"${displayText}"`);
    });

    // Process all real machines from API
    console.log("\n=== REAL API DATA RESULTS ===");
    machines.forEach((machine, index) => {
        const displayText = [
            getStringValue(machine.name),
            getStringValue(machine.location_business_name),
            getStringValue(machine.location_type),
            getStringValue(machine.sub_location)
        ].join(' | ');
        
        console.log(`${index + 1}. "${displayText}"`);
    });
})();
