"""
Quick test to check the structure of the operations API response.
"""
import requests
import json
import sys

def test_operations_api():
    """
    Test the operations API endpoint to verify the temperature_trends structure.
    """
    machine_id = "vm-106c55e5"  # Use the same ID from the error message
    api_url = f"http://localhost:8006/api/vending-machines/{machine_id}/operations"
    
    print(f"Testing API: {api_url}")
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        data = response.json()
        
        print("API Response Status:", response.status_code)
        print("\nStructure of response:")
        
        # Check if temperature_trends exists
        if "temperature" in data:
            print("\nTemperature trends field exists")
            
            # Check if average_temperature exists
            if data["temperature"] and "average_temperature" in data["temperature"]:
                print(f"average_temperature exists: {data['temperature']['average_temperature']}")
            else:
                print("ERROR: average_temperature field is missing or temperature is null")
                if data["temperature"] is None:
                    print("temperature field is null")
                else:
                    print("temperature field structure:", json.dumps(data["temperature"], indent=2))
        else:
            print("ERROR: temperature field is missing")
        
        # Pretty-print the whole response
        print("\nFull response:")
        print(json.dumps(data, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing API: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_operations_api()
    sys.exit(0 if success else 1)
