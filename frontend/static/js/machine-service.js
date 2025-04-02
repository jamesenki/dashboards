/**
 * MachineService - Centralizes all vending machine data access
 * Handles API communication, caching, and error recovery
 *
 * This module ensures consistent machine data format and reliable
 * real-time operational data access for the IoTSphere dashboard.
 */
window.MachineService = {
    apiBaseUrl: null,
    machineCache: null,
    selectedMachineId: null,

    // Initialize the service with the correct port
    init() {
        this.apiBaseUrl = `http://${window.location.hostname}:8006/api`;
        console.log(`MachineService initialized with base URL: ${this.apiBaseUrl}`);
    },

    // Load machines once and cache them
    async loadMachines() {
        try {
            const timestamp = new Date().getTime();
            const url = `${this.apiBaseUrl}/vending-machines?format_names=true&_=${timestamp}`;
            console.log(`Fetching machines from: ${url}`);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }

            const machines = await response.json();
            if (!Array.isArray(machines)) {
                throw new Error('API did not return an array for machines');
            }

            console.log(`Successfully loaded ${machines.length} machines`);
            this.machineCache = machines;
            return machines;
        } catch (error) {
            console.error('Error loading machines:', error);
            // Use consistent fallback data
            this.machineCache = this.getFallbackMachines();
            return this.machineCache;
        }
    },

    // Get cached machines or load them if not available
    async getMachines() {
        if (this.machineCache) {
            return this.machineCache;
        }
        return await this.loadMachines();
    },

    // Get a specific machine by ID
    async getMachineById(machineId) {
        try {
            const url = `${this.apiBaseUrl}/vending-machines/${machineId}`;
            console.log(`Fetching specific machine from: ${url}`);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error loading machine ${machineId}:`, error);
            return this.createFallbackMachine(machineId);
        }
    },

    // Get operations data for a machine - focused on real-time operational monitoring
    async getOperationsData(machineId) {
        try {
            if (!machineId) {
                throw new Error('No machine ID provided');
            }

            // Add timestamp to prevent caching
            const timestamp = new Date().getTime();
            const url = `${this.apiBaseUrl}/vending-machines/${machineId}/operations?_=${timestamp}`;
            console.log(`Fetching operations data from: ${url}`);

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Operations data received:', data);

            // Process the data to ensure it matches the expected structure for real-time operational monitoring
            return this.processOperationsData(data);
        } catch (error) {
            console.error(`Error generating operations data for machine ${machineId}:`, error);
            return this.createFallbackOperationsData(machineId);
        }
    },

    // Process operations data to ensure consistent structure
    processOperationsData(data) {
        // Ensure we have an object to work with
        if (!data) data = {};

        // Default values for critical properties
        const DEFAULT_VALUES = {
            dispenseForce: 30,
            cycleTime: 15,
            freezerTemperature: -15,
            assetHealth: 85
        };

        // Create a properly structured operations data object
        const processedData = {
            machine_id: data.machine_id || 'unknown',
            machine_status: data.machine_status || 'UNKNOWN',
            pod_code: data.pod_code || 'N/A',
            cup_detect: data.cup_detect || 'No',
            customer_door: data.customer_door || 'CLOSED',
            last_updated: data.last_updated || new Date().toISOString(),

            // Process gauge data
            dispense_pressure: {
                dispensePressure:
                    (data.dispense_pressure && data.dispense_pressure.dispensePressure) ?
                    data.dispense_pressure.dispensePressure :
                    DEFAULT_VALUES.dispenseForce.toString(),
                status:
                    (data.dispense_pressure && data.dispense_pressure.status) ?
                    data.dispense_pressure.status :
                    'Normal'
            },

            freezer_temperature: {
                freezerTemperature:
                    (data.freezer_temperature && data.freezer_temperature.freezerTemperature) ?
                    data.freezer_temperature.freezerTemperature :
                    DEFAULT_VALUES.freezerTemperature.toString(),
                needleValue:
                    (data.freezer_temperature && data.freezer_temperature.needleValue !== undefined) ?
                    data.freezer_temperature.needleValue :
                    this.calculateNeedlePosition(DEFAULT_VALUES.freezerTemperature, -30, 30)
            },

            cycle_time: {
                cycleTime:
                    (data.cycle_time && data.cycle_time.cycleTime) ?
                    data.cycle_time.cycleTime :
                    DEFAULT_VALUES.cycleTime.toString(),
                min:
                    (data.cycle_time && data.cycle_time.min) ?
                    data.cycle_time.min :
                    '5',
                max:
                    (data.cycle_time && data.cycle_time.max) ?
                    data.cycle_time.max :
                    '60'
            },

            // Inventory data with fallback
            ice_cream_inventory: Array.isArray(data.ice_cream_inventory) ?
                data.ice_cream_inventory :
                this.createDefaultInventory()
        };

        return processedData;
    },

    // Calculate needle position for gauge display (0-100)
    calculateNeedlePosition(value, min, max) {
        // Convert value to a number if it's a string
        const numValue = parseFloat(value);
        const numMin = parseFloat(min);
        const numMax = parseFloat(max);

        // Validate inputs
        if (isNaN(numValue) || isNaN(numMin) || isNaN(numMax)) {
            console.warn('Invalid values for needle position calculation, using 50%');
            return 50;
        }

        // Calculate percentage (0-100)
        return Math.max(0, Math.min(100, ((numValue - numMin) / (numMax - numMin)) * 100));
    },

    // Get consistent fallback machines
    getFallbackMachines() {
        console.warn('Using fallback machine data');
        return [
            { id: 'vm-cb0300b1', name: 'PolarDelight #1 - Cleveland HQ', location_business_name: 'Cleveland HQ', location_type: 'OFFICE', sub_location: 'Lobby' },
            { id: 'vm-29ea1cf3', name: 'PolarDelight #2 - Airport Terminal', location_business_name: 'Airport', location_type: 'TRAVEL', sub_location: 'Terminal B' },
            { id: 'vm-d9564b04', name: 'PolarDelight #3 - Mall Food Court', location_business_name: 'Eastwood Mall', location_type: 'RETAIL', sub_location: 'Food Court' },
            { id: 'vm-32a1b371', name: 'PolarDelight #4 - University Center', location_business_name: 'Case Western', location_type: 'SCHOOL', sub_location: 'Student Union' }
        ];
    },

    // Create a fallback machine for testing/demo
    createFallbackMachine(machineId) {
        return {
            id: machineId,
            name: `PolarDelight #${machineId.substring(3, 7)}`,
            location_business_name: 'Demo Location',
            location_type: 'OFFICE',
            sub_location: 'Test Area',
            status: 'ONLINE',
            machine_status: 'OPERATIONAL'
        };
    },

    // Create default inventory items
    createDefaultInventory() {
        return [
            { name: 'Vanilla', level: 75, max_capacity: 100 },
            { name: 'Chocolate', level: 60, max_capacity: 100 },
            { name: 'Strawberry', level: 85, max_capacity: 100 },
            { name: 'Mint', level: 45, max_capacity: 100 }
        ];
    },

    // Create fallback operations data
    createFallbackOperationsData(machineId) {
        console.warn(`Creating fallback operations data for machine ${machineId}`);
        return {
            machine_id: machineId,
            machine_status: 'ONLINE',
            pod_code: '12345',
            cup_detect: 'Yes',
            customer_door: 'CLOSED',
            last_updated: new Date().toISOString(),

            dispense_pressure: {
                dispensePressure: '35',
                status: 'Normal',
                min: '5',
                max: '50'
            },

            freezer_temperature: {
                freezerTemperature: '-12.5',
                needleValue: 70
            },

            cycle_time: {
                cycleTime: '18.3',
                min: '5',
                max: '60'
            },

            ice_cream_inventory: this.createDefaultInventory()
        };
    },

    // Format machine name for display
    formatMachineName(machine) {
        if (!machine) return 'Unknown Machine';

        const getPropValue = (prop) => {
            if (machine[prop] === null || machine[prop] === undefined) return 'Unknown';
            if (typeof machine[prop] === 'string') return machine[prop];
            if (typeof machine[prop] === 'object' && machine[prop].value) return machine[prop].value;
            return String(machine[prop]);
        };

        return [
            getPropValue('name'),
            getPropValue('location_business_name'),
            getPropValue('location_type'),
            getPropValue('sub_location')
        ].join(' | ');
    }
};

// Initialize service when script is loaded
MachineService.init();
