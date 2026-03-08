"""Quick verification of models and scaler"""
import joblib
import pandas as pd

# Load models
scaler = joblib.load('../models/scaler.pkl')
fan_model = joblib.load('../models/fan_model.pkl')
humidifier_model = joblib.load('../models/humidifier_model.pkl')

print("Scaler feature names:", list(scaler.feature_names_in_))

# Test prediction
features = pd.DataFrame([[26.5, 80.0, 24.0, 24.0, 65.0, 30.0, 1.0]],
    columns=['air_temp','humidity','soil_temp','target_temp','target_humidity','prev_fan_speed','prev_humidifier_mode'])

print("Input features:", features.values.tolist())

features_scaled = scaler.transform(features)
print("Scaled features:", features_scaled.tolist())

fan_prediction = fan_model.predict(features_scaled)
print("Fan speed prediction:", fan_prediction[0])

humidifier_prediction = humidifier_model.predict(features_scaled)
print("Humidifier mode prediction:", humidifier_prediction[0])

print("\n✓ All models working correctly!")

