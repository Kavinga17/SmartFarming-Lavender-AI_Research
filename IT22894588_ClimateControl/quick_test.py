#!/usr/bin/env python3
"""Quick test script for the API."""

import requests
import json

def test_api():
    base_url = "http://127.0.0.1:5000"

    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Health test failed: {e}")
        return

    # Test predict endpoint
    print("Testing predict endpoint...")
    test_data = {
        "air_temp": 28.5,
        "humidity": 65.0,
        "soil_temp": 22.0,
        "target_temp": 25.0,
        "target_humidity": 60.0,
        "prev_fan_speed": 50.0,
        "prev_humidifier_mode": 1.0
    }

    try:
        response = requests.post(f"{base_url}/predict",
                               json=test_data,
                               timeout=10)
        print(f"Predict: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Predict test failed: {e}")
        return

    print("✅ API tests completed successfully!")

if __name__ == "__main__":
    test_api()
