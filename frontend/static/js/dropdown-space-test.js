// Test script to demonstrate updated dropdown formatting with spaces
(function() {
    // Sample machine data from API
    const machines = [
        {
            "id":"vm-92cfeda3",
            "name":"PolarDelight - FrostyPlus 92cf",
            "location_business_name":"LAX Terminal",
            "location_type":"TRANSPORTATION",
            "sub_location":"CAFETERIA",
            "location":"Building C - Bathroom",
            "status":"OPERATIONAL"
        },
        {
            "id":"vm-77436414",
            "name":"PolarDelight - CoolVend 7743",
            "location_business_name":"Red Rocks Amphitheater",
            "location_type":"OTHER",
            "sub_location":"BREAK_ROOM",
            "location":"Warehouse - Suite 101",
            "status":"NEEDS_RESTOCK"
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

    console.log("=== UPDATED DROPDOWN FORMAT (SPACES) ===");

    // Process machines with the updated format (spaces instead of pipes)
    machines.forEach((machine, index) => {
        // Updated format: spaces instead of pipes
        const displayText = [
            getStringValue(machine.name),
            getStringValue(machine.location_business_name),
            getStringValue(machine.location_type),
            getStringValue(machine.sub_location)
        ].join(' ');

        console.log(`\nMachine ${index + 1}:`);
        console.log(`Machine ID: ${machine.id}`);
        console.log(`Individual Values:`);
        console.log(`  - name: "${getStringValue(machine.name)}"`);
        console.log(`  - location_business_name: "${getStringValue(machine.location_business_name)}"`);
        console.log(`  - location_type: "${getStringValue(machine.location_type)}"`);
        console.log(`  - sub_location: "${getStringValue(machine.sub_location)}"`);
        console.log(`\nFormatted Output (with spaces):`);
        console.log(`"${displayText}"`);
    });

    // Test with special characters and edge cases
    const specialCases = [
        {
            "id":"vm-special1",
            "name":"Test Machine 1",
            "location_business_name": "Business with spaces",
            "location_type":"TYPE_WITH_UNDERSCORES",
            "sub_location":"Sub Location"
        },
        {
            "id":"vm-special2",
            "name":"Name With Multiple Words",
            "location_business_name": null,
            "location_type":"OFFICE",
            "sub_location":"HALLWAY"
        }
    ];

    console.log("\n=== SPECIAL CASES WITH SPACES ===");
    specialCases.forEach((machine, index) => {
        const displayText = [
            getStringValue(machine.name),
            getStringValue(machine.location_business_name),
            getStringValue(machine.location_type),
            getStringValue(machine.sub_location)
        ].join(' ');

        console.log(`\nSpecial Case ${index + 1}:`);
        console.log(`Formatted Output (with spaces):`);
        console.log(`"${displayText}"`);
    });
})();
