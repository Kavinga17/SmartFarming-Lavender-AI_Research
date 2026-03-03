"""
Flask API Server for Greenhouse Climate Control System.

This server provides a REST API endpoint for predicting fan speed and
humidifier mode based on sensor data from ESP32 devices.
"""

import os
import warnings
from flask import Flask, request, jsonify
import joblib
import pandas as pd
from flask_cors import CORS
import numpy as np

# Suppress sklearn warnings about feature names
warnings.filterwarnings("ignore", category=UserWarning)


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
FAN_MODEL_PATH = os.path.join(MODELS_DIR, 'fan_model.pkl')
HUMIDIFIER_MODEL_PATH = os.path.join(MODELS_DIR, 'humidifier_model.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

# Feature names in expected order
FEATURE_NAMES = [
    'air_temp',
    'humidity',
    'soil_temp',
    'target_temp',
    'target_humidity',
    'prev_fan_speed',
    'prev_humidifier_mode'
]

# Global model variables
fan_model = None
humidifier_model = None
scaler = None


def load_models():
    """Load all pre-trained models and scaler."""
    global fan_model, humidifier_model, scaler

    print("Loading models...")

    if not os.path.exists(FAN_MODEL_PATH):
        raise FileNotFoundError(f"Fan model not found: {FAN_MODEL_PATH}")
    if not os.path.exists(HUMIDIFIER_MODEL_PATH):
        raise FileNotFoundError(f"Humidifier model not found: {HUMIDIFIER_MODEL_PATH}")
    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(f"Scaler not found: {SCALER_PATH}")

    fan_model = joblib.load(FAN_MODEL_PATH)
    print(f"  ✓ Fan model loaded: {FAN_MODEL_PATH}")

    humidifier_model = joblib.load(HUMIDIFIER_MODEL_PATH)
    print(f"  ✓ Humidifier model loaded: {HUMIDIFIER_MODEL_PATH}")

    scaler = joblib.load(SCALER_PATH)
    print(f"  ✓ Scaler loaded: {SCALER_PATH}")

    print("All models loaded successfully!")


@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict fan speed and humidifier mode from sensor data.

    Expects JSON payload with fields:
        - air_temp (float): Current air temperature
        - humidity (float): Current humidity percentage
        - soil_temp (float): Current soil temperature
        - target_temp (float): Target air temperature
        - target_humidity (float): Target humidity percentage
        - prev_fan_speed (float): Previous fan speed setting
        - prev_humidifier_mode (float): Previous humidifier mode (0-3)

    Returns JSON:
        {
            "fan_speed": <float>,
            "humidifier_mode": <int>
        }
    """
    try:
        # Get JSON data from request
        data = request.get_json()

        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate required fields
        missing_fields = [field for field in FEATURE_NAMES if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400

        # Extract features in correct order
        try:
            features = pd.DataFrame([[
                float(data['air_temp']),
                float(data['humidity']),
                float(data['soil_temp']),
                float(data['target_temp']),
                float(data['target_humidity']),
                float(data['prev_fan_speed']),
                float(data['prev_humidifier_mode'])
            ]], columns=FEATURE_NAMES)
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid field value: {str(e)}'}), 400

        # Scale features (convert to numpy array to avoid column name issues)
        features_scaled = scaler.transform(features.values)

        # Make predictions
        fan_speed = float(fan_model.predict(features_scaled)[0])
        humidifier_mode = int(humidifier_model.predict(features_scaled)[0])

        # Return predictions
        return jsonify({
            'fan_speed': round(fan_speed, 2),
            'humidifier_mode': humidifier_mode
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'models_loaded': all([fan_model, humidifier_model, scaler])
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information."""
    return jsonify({
        'service': 'Greenhouse Climate Control API',
        'version': '1.0.0',
        'endpoints': {
            'POST /predict': 'Predict fan speed and humidifier mode',
            'GET /health': 'Health check',
            'GET /': 'API information'
        },
        'required_fields': FEATURE_NAMES
    })


if __name__ == '__main__':
    # Load models at startup
    load_models()

    # Run Flask server
    # Host 0.0.0.0 allows connections from ESP32 over local network
    print("\n" + "=" * 50)
    print("🌱 Greenhouse Climate Control API Server")
    print("=" * 50)
    print("Server starting on http://0.0.0.0:5000")
    print("ESP32 can connect via your local IP address")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False)

