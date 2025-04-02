/**
 * Tests for Machine Dropdown Functionality
 *
 * This test suite validates the machine dropdown components in the vending machine dashboard,
 * ensuring they load, populate, and sync correctly.
 */

// Mock DOM elements
const mockDOM = {
    dropdowns: {
        'machine-selector': { value: '', options: [], addEventListener: jest.fn(), innerHTML: '' },
        'operations-machine-selector': { value: '', options: [], addEventListener: jest.fn(), innerHTML: '' }
    },
    createElement: function(tag) {
        return {
            value: '',
            textContent: '',
            classList: { add: jest.fn(), remove: jest.fn() },
            style: {},
            appendChild: jest.fn()
        };
    }
};

// Mock global objects
global.document = {
    getElementById: function(id) {
        return mockDOM.dropdowns[id] || null;
    },
    createElement: mockDOM.createElement,
    querySelector: jest.fn().mockReturnValue({ classList: { add: jest.fn(), remove: jest.fn() } })
};

global.window = {
    location: {
        hostname: 'localhost'
    },
    history: {
        pushState: jest.fn()
    }
};

global.fetch = jest.fn();
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Mock implementations
jest.mock('loadMachineData', () => jest.fn());
jest.mock('loadRealtimeOperationsData', () => jest.fn());

// Mock machine data
const mockMachines = [
    {
        id: 'vm-123',
        name: 'Test Machine 1',
        location_business_name: 'Test Location',
        location_type: 'OFFICE',
        sub_location: 'Test Area'
    },
    {
        id: 'vm-456',
        name: 'Test Machine 2',
        location_business_name: 'Another Location',
        location_type: 'RETAIL',
        sub_location: 'Another Area'
    }
];

// Test suite
describe('Machine Dropdown Functionality', () => {
    // Reset mocks before each test
    beforeEach(() => {
        jest.clearAllMocks();
        mockDOM.dropdowns['machine-selector'].value = '';
        mockDOM.dropdowns['machine-selector'].innerHTML = '';
        mockDOM.dropdowns['operations-machine-selector'].value = '';
        mockDOM.dropdowns['operations-machine-selector'].innerHTML = '';

        // Mock successful fetch
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockMachines
        });
    });

    // Test loading machines from API
    test('loads machines from API successfully', async () => {
        const machines = await MachineService.loadMachines();

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/vending-machines?format_names=true'));
        expect(machines).toEqual(mockMachines);
        expect(MachineService.machineCache).toEqual(mockMachines);
    });

    // Test handling API failures
    test('handles API failures gracefully', async () => {
        // Clear previous mock implementation
        global.fetch.mockReset();

        // Mock API failure
        global.fetch.mockRejectedValueOnce(new Error('API connection failed'));

        const machines = await MachineService.loadMachines();

        expect(fetch).toHaveBeenCalledTimes(1);
        expect(console.error).toHaveBeenCalledWith(expect.stringContaining('Error loading machines'), expect.any(Error));
        expect(machines).toEqual(MachineService.getFallbackMachines());
    });

    // Test populating dropdowns
    test('populates both dropdowns with machine data', async () => {
        await DropdownManager.initializeDropdowns();

        // Check that dropdown inner HTML was updated for both dropdowns
        expect(mockDOM.dropdowns['machine-selector'].innerHTML).toEqual(expect.stringContaining('<option value="">'));
        expect(mockDOM.dropdowns['operations-machine-selector'].innerHTML).toEqual(expect.stringContaining('<option value="">'));

        // Verify event listeners were added
        expect(mockDOM.dropdowns['machine-selector'].addEventListener).toHaveBeenCalled();
        expect(mockDOM.dropdowns['operations-machine-selector'].addEventListener).toHaveBeenCalled();
    });

    // Test machine selection and dropdown synchronization
    test('keeps dropdowns in sync when machine is selected', () => {
        // Initialize with test data
        DropdownManager.initializeDropdowns('vm-123');

        // Simulate selection in asset health dropdown
        DropdownManager.handleMachineSelection('vm-456', 'asset-health');

        // Both dropdowns should have the same value
        expect(mockDOM.dropdowns['machine-selector'].value).toBe('vm-456');
        expect(mockDOM.dropdowns['operations-machine-selector'].value).toBe('vm-456');

        // Simulate selection in operations dropdown
        DropdownManager.handleMachineSelection('vm-123', 'operations');

        // Both dropdowns should have updated
        expect(mockDOM.dropdowns['machine-selector'].value).toBe('vm-123');
        expect(mockDOM.dropdowns['operations-machine-selector'].value).toBe('vm-123');
    });

    // Test machine name formatting
    test('formats machine names correctly', () => {
        const machine = mockMachines[0];
        const formattedName = MachineService.formatMachineName(machine);

        expect(formattedName).toBe('Test Machine 1 | Test Location | OFFICE | Test Area');
    });

    // Test handling missing properties in machine data
    test('handles missing properties in machine data', () => {
        const incompleteData = { id: 'vm-789', name: 'Incomplete Machine' };
        const formattedName = MachineService.formatMachineName(incompleteData);

        expect(formattedName).toBe('Incomplete Machine | Unknown | Unknown | Unknown');
    });

    // Test URL history updates
    test('updates URL when machine is selected', () => {
        DropdownManager.handleMachineSelection('vm-123', 'asset-health');

        expect(window.history.pushState).toHaveBeenCalledWith(
            {},
            '',
            '/vending-machines/vm-123'
        );
    });
});

// Run tests
runTests();
