"""Test script for the Flask API."""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """Test health endpoint."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health check: {r.status_code}")
        print(f"Response: {r.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_predict():
    """Test predict endpoint."""
    data = {
        "air_temp": 26.5,
        "humidity": 75.0,
        "soil_temp": 24.0,
        "target_temp": 24.0,
        "target_humidity": 65.0,
        "prev_fan_speed": 50.0,
        "prev_humidifier_mode": 1.0
    }
    try:
        r = requests.post(f"{BASE_URL}/predict", json=data, timeout=5)
        print(f"Predict: {r.status_code}")
        print(f"Response: {r.json()}")
        return True
    except Exception as e:
        print(f"Predict failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Flask API...")
    print("=" * 40)
    test_health()
    print("-" * 40)
    test_predict()

