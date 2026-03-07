"""
Flask API Server for Greenhouse Climate Control System.
Supports fan modes: off, manual, auto.
Supports humidifier modes: off, manual, auto.
Humidifier levels: 0=off, 1=low, 2=medium, 3=high
"""

import os
import warnings
from flask import Flask, request, jsonify
import joblib
import pandas as pd
from flask_cors import CORS
from datetime import datetime, UTC
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
CORS(app)

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
FAN_MODEL_PATH = os.path.join(MODELS_DIR, 'fan_model.pkl')
HUMIDIFIER_MODEL_PATH = os.path.join(MODELS_DIR, 'humidifier_model.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

FEATURE_NAMES = [
    'air_temp', 'humidity', 'soil_temp',
    'target_temp', 'target_humidity',
    'prev_fan_speed', 'prev_humidifier_mode'
]

fan_model = None
humidifier_model = None
scaler = None

latest_sensor_data = {
    'air_temp': 0.0,
    'humidity': 0.0,
    'soil_temp': 0.0,
    'timestamp': None
}

fan_control = {
    'mode': 'auto',
    'manual_speed': 0,
    'manual_on': False
}

humidifier_control = {
    'mode': 'auto',
    'manual_level': 0   # 0=off, 1=low, 2=medium, 3=high
}


def load_models():
    global fan_model, humidifier_model, scaler
    print("Loading models...")
    if not os.path.exists(FAN_MODEL_PATH):
        raise FileNotFoundError(f"Fan model not found: {FAN_MODEL_PATH}")
    if not os.path.exists(HUMIDIFIER_MODEL_PATH):
        raise FileNotFoundError(f"Humidifier model not found: {HUMIDIFIER_MODEL_PATH}")
    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(f"Scaler not found: {SCALER_PATH}")

    fan_model = joblib.load(FAN_MODEL_PATH)
    humidifier_model = joblib.load(HUMIDIFIER_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    # ── Inspect humidifier model output classes so we know what it predicts ──
    if hasattr(humidifier_model, 'classes_'):
        print(f"Humidifier model classes: {humidifier_model.classes_}")
    print("All models loaded successfully!")


def normalize_humidifier_prediction(raw_pred: int) -> int:
    """
    Normalise whatever the model outputs to 0-3 (off/low/medium/high).

    Common cases:
      • Model trained with labels 0,1,2,3 → already correct
      • Model trained with labels 1,2,3   → subtract 1  (1=low→0 would be wrong;
        treat 1=off,2=low,3=med,4=high is unlikely — handle the real case below)
      • Model trained with labels 0,1,2,3 but meaning off/high/med/low →
        re-map via the serverLevelToPhysical table (not needed here; Arduino handles it)

    This function only ensures the value is clamped to [0, 3].
    """
    return int(np.clip(raw_pred, 0, 3))


# ════════════════════════════════════════
#  FAN CONTROL ENDPOINTS
# ════════════════════════════════════════

@app.route('/fan/mode', methods=['POST'])
def set_fan_mode():
    data = request.get_json()
    if not data or 'mode' not in data:
        return jsonify({'error': 'Missing "mode" field'}), 400
    mode = data['mode']
    if mode not in ('off', 'manual', 'auto'):
        return jsonify({'error': 'mode must be "off", "manual", or "auto"'}), 400
    fan_control['mode'] = mode
    return jsonify({'success': True, 'fan_control': fan_control})


@app.route('/fan/manual', methods=['POST'])
def set_fan_manual():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400
    if 'on' in data:
        fan_control['manual_on'] = bool(data['on'])
    if 'speed' in data:
        speed = int(data['speed'])
        if not (1 <= speed <= 100):
            return jsonify({'error': 'speed must be between 1 and 100'}), 400
        fan_control['manual_speed'] = speed
    return jsonify({'success': True, 'fan_control': fan_control})


@app.route('/fan/state', methods=['GET'])
def get_fan_state():
    return jsonify(fan_control)


# ════════════════════════════════════════
#  HUMIDIFIER CONTROL ENDPOINTS
# ════════════════════════════════════════

@app.route('/humidifier/mode', methods=['POST'])
def set_humidifier_mode():
    """
    Set humidifier mode.
    Body: { "mode": "off" | "manual" | "auto" }
    """
    data = request.get_json()
    if not data or 'mode' not in data:
        return jsonify({'error': 'Missing "mode" field'}), 400
    mode = data['mode']
    if mode not in ('off', 'manual', 'auto'):
        return jsonify({'error': 'mode must be "off", "manual", or "auto"'}), 400
    humidifier_control['mode'] = mode
    return jsonify({'success': True, 'humidifier_control': humidifier_control})


@app.route('/humidifier/manual', methods=['POST'])
def set_humidifier_manual():
    """
    Set manual humidifier level (only effective when mode = "manual").
    Body: { "level": 0 | 1 | 2 | 3 }
      0 = off, 1 = low, 2 = medium, 3 = high
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400
    if 'level' in data:
        level = int(data['level'])
        if level not in (0, 1, 2, 3):
            return jsonify({'error': 'level must be 0 (off), 1 (low), 2 (medium), or 3 (high)'}), 400
        humidifier_control['manual_level'] = level
    return jsonify({'success': True, 'humidifier_control': humidifier_control})


@app.route('/humidifier/state', methods=['GET'])
def get_humidifier_state():
    return jsonify(humidifier_control)


# ════════════════════════════════════════
#  PREDICT  (called by Arduino every loop)
# ════════════════════════════════════════

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400

        missing_fields = [f for f in FEATURE_NAMES if f not in data]
        if missing_fields:
            return jsonify({'error': 'Missing required fields', 'missing': missing_fields}), 400

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

        latest_sensor_data.update({
            'air_temp': float(data['air_temp']),
            'humidity': float(data['humidity']),
            'soil_temp': float(data['soil_temp']),
            'timestamp': datetime.now(UTC).isoformat()
        })

        features_scaled = scaler.transform(features.values)
        ai_fan_speed        = float(fan_model.predict(features_scaled)[0])
        raw_hum_prediction  = humidifier_model.predict(features_scaled)[0]

        # Normalise: clamp to [0,3]
        ai_humidifier_level = normalize_humidifier_prediction(int(raw_hum_prediction))

        print(f"[PREDICT] raw_hum={raw_hum_prediction}  normalised={ai_humidifier_level}  "
              f"hum_mode={humidifier_control['mode']}")

        # ── Effective fan speed ──
        fan_mode = fan_control['mode']
        if fan_mode == 'off':
            effective_fan_speed = 0.0
        elif fan_mode == 'manual':
            effective_fan_speed = float(fan_control['manual_speed']) if fan_control['manual_on'] else 0.0
        else:
            effective_fan_speed = round(ai_fan_speed, 2)

        # ── Effective humidifier level ──
        hum_mode = humidifier_control['mode']
        if hum_mode == 'off':
            effective_humidifier_level = 0
        elif hum_mode == 'manual':
            effective_humidifier_level = int(humidifier_control['manual_level'])
        else:  # auto — use AI prediction
            effective_humidifier_level = ai_humidifier_level

        print(f"[PREDICT] effective_hum_level={effective_humidifier_level}")

        return jsonify({
            # Fan
            'fan_speed':            round(ai_fan_speed, 2),
            'effective_fan_speed':  effective_fan_speed,
            'fan_mode':             fan_mode,
            # Humidifier
            'humidifier_mode':          ai_humidifier_level,        # normalised AI value
            'effective_humidifier_level': effective_humidifier_level, # ← Arduino uses THIS
            'humidifier_control_mode':  hum_mode,
            # Sensors echo
            'air_temp':   float(data['air_temp']),
            'humidity':   float(data['humidity']),
            'soil_temp':  float(data['soil_temp'])
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


# ════════════════════════════════════════
#  MISC ENDPOINTS
# ════════════════════════════════════════

@app.route('/sensors', methods=['GET'])
def sensors():
    return jsonify(latest_sensor_data)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': all([fan_model, humidifier_model, scaler])
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Greenhouse Climate Control API',
        'version': '3.1.0',
        'endpoints': {
            'POST /predict':            'Predict fan speed + humidifier level',
            'POST /fan/mode':           'Set fan mode: off | manual | auto',
            'POST /fan/manual':         'Set manual fan on/off + speed (1-100)',
            'GET  /fan/state':          'Get fan control state',
            'POST /humidifier/mode':    'Set humidifier mode: off | manual | auto',
            'POST /humidifier/manual':  'Set manual level: 0=off 1=low 2=med 3=high',
            'GET  /humidifier/state':   'Get humidifier control state',
            'GET  /sensors':            'Latest sensor readings',
            'GET  /health':             'Health check',
        }
    })


if __name__ == '__main__':
    load_models()
    print("\n" + "=" * 50)
    print("🌱 Greenhouse Climate Control API Server v3.1")
    print("=" * 50)
    print("Server starting on http://0.0.0.0:5000")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)