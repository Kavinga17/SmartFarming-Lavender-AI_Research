"""
Prediction Module for Greenhouse Climate Control System.

This module provides functionality to make predictions using trained
models for fan speed and humidifier mode control.
"""

import os
import sys
import numpy as np
import joblib
from typing import Tuple


# Model and scaler paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
FAN_MODEL_PATH = os.path.join(MODELS_DIR, 'fan_model.pkl')
HUMIDIFIER_MODEL_PATH = os.path.join(MODELS_DIR, 'humidifier_model.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

# Feature names in order
FEATURE_NAMES = [
    'air_temp',
    'humidity',
    'soil_temp',
    'target_temp',
    'target_humidity',
    'prev_fan_speed',
    'prev_humidifier_mode'
]

# Humidifier mode labels
HUMIDIFIER_LABELS = {
    0: "Off",
    1: "Low",
    2: "Medium",
    3: "High"
}


class GreenhousePredictor:
    """
    Predictor class for greenhouse climate control.

    This class handles loading models and making predictions for
    fan speed and humidifier mode based on sensor inputs.
    """

    def __init__(self, fan_model_path: str = None,
                 humidifier_model_path: str = None,
                 scaler_path: str = None):
        """
        Initialize the predictor by loading models and scaler.

        Args:
            fan_model_path: Path to the fan model file.
            humidifier_model_path: Path to the humidifier model file.
            scaler_path: Path to the scaler file.
        """
        self.fan_model_path = fan_model_path or FAN_MODEL_PATH
        self.humidifier_model_path = humidifier_model_path or HUMIDIFIER_MODEL_PATH
        self.scaler_path = scaler_path or SCALER_PATH

        self.fan_model = None
        self.humidifier_model = None
        self.scaler = None

        self._load_models()

    def _load_models(self) -> None:
        """Load all required models and scaler."""
        try:
            print("Loading models...")
            self.fan_model = joblib.load(self.fan_model_path)
            print(f"  ✓ Fan model loaded from: {self.fan_model_path}")

            self.humidifier_model = joblib.load(self.humidifier_model_path)
            print(f"  ✓ Humidifier model loaded from: {self.humidifier_model_path}")

            self.scaler = joblib.load(self.scaler_path)
            print(f"  ✓ Scaler loaded from: {self.scaler_path}")
            print("All models loaded successfully!\n")

        except FileNotFoundError as e:
            print(f"Error: Could not load model - {e}")
            print("Please ensure all models are trained before making predictions.")
            raise

    def predict(self, air_temp: float, humidity: float, soil_temp: float,
                target_temp: float, target_humidity: float,
                prev_fan_speed: float, prev_humidifier_mode: float) -> Tuple[float, int, str]:
        """
        Make predictions for fan speed and humidifier mode.

        Args:
            air_temp: Current air temperature (°C).
            humidity: Current humidity (%).
            soil_temp: Current soil temperature (°C).
            target_temp: Target air temperature (°C).
            target_humidity: Target humidity (%).
            prev_fan_speed: Previous fan speed setting.
            prev_humidifier_mode: Previous humidifier mode (0-3).

        Returns:
            Tuple of (predicted_fan_speed, predicted_humidifier_mode, humidifier_label)
        """
        # Prepare input features as DataFrame to preserve feature names
        import pandas as pd
        features = pd.DataFrame([[
            air_temp,
            humidity,
            soil_temp,
            target_temp,
            target_humidity,
            prev_fan_speed,
            prev_humidifier_mode
        ]], columns=FEATURE_NAMES)

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Make predictions
        fan_speed = self.fan_model.predict(features_scaled)[0]
        humidifier_mode = int(self.humidifier_model.predict(features_scaled)[0])
        humidifier_label = HUMIDIFIER_LABELS.get(humidifier_mode, "Unknown")

        return fan_speed, humidifier_mode, humidifier_label

    def predict_batch(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions for multiple samples at once.

        Args:
            features: 2D array of shape (n_samples, 7) with feature values.

        Returns:
            Tuple of (fan_speed_predictions, humidifier_mode_predictions)
        """
        # Scale features
        features_scaled = self.scaler.transform(features)

        # Make predictions
        fan_speeds = self.fan_model.predict(features_scaled)
        humidifier_modes = self.humidifier_model.predict(features_scaled).astype(int)

        return fan_speeds, humidifier_modes


def predict_single(air_temp: float, humidity: float, soil_temp: float,
                   target_temp: float, target_humidity: float,
                   prev_fan_speed: float, prev_humidifier_mode: float) -> dict:
    """
    Convenience function for making a single prediction.

    Args:
        air_temp: Current air temperature (°C).
        humidity: Current humidity (%).
        soil_temp: Current soil temperature (°C).
        target_temp: Target air temperature (°C).
        target_humidity: Target humidity (%).
        prev_fan_speed: Previous fan speed setting.
        prev_humidifier_mode: Previous humidifier mode (0-3).

    Returns:
        Dictionary containing predictions and input values.
    """
    predictor = GreenhousePredictor()
    fan_speed, humid_mode, humid_label = predictor.predict(
        air_temp, humidity, soil_temp,
        target_temp, target_humidity,
        prev_fan_speed, prev_humidifier_mode
    )

    return {
        'input': {
            'air_temp': air_temp,
            'humidity': humidity,
            'soil_temp': soil_temp,
            'target_temp': target_temp,
            'target_humidity': target_humidity,
            'prev_fan_speed': prev_fan_speed,
            'prev_humidifier_mode': prev_humidifier_mode
        },
        'predictions': {
            'fan_speed': round(fan_speed, 2),
            'humidifier_mode': humid_mode,
            'humidifier_mode_label': humid_label
        }
    }


def print_prediction(result: dict) -> None:
    """
    Pretty print a prediction result.

    Args:
        result: Dictionary from predict_single function.
    """
    print("\n" + "=" * 50)
    print("🌱 GREENHOUSE CLIMATE CONTROL PREDICTION")
    print("=" * 50)

    print("\n📥 INPUT SENSOR VALUES:")
    print("-" * 30)
    for key, value in result['input'].items():
        print(f"  {key}: {value}")

    print("\n📤 PREDICTED CONTROL OUTPUTS:")
    print("-" * 30)
    print(f"  🌀 Fan Speed: {result['predictions']['fan_speed']}")
    print(f"  💧 Humidifier Mode: {result['predictions']['humidifier_mode']} ({result['predictions']['humidifier_mode_label']})")
    print("\n" + "=" * 50)


def interactive_prediction() -> None:
    """Run an interactive prediction session."""
    print("\n" + "=" * 50)
    print("🌱 GREENHOUSE CLIMATE CONTROL - INTERACTIVE MODE")
    print("=" * 50)
    print("\nEnter sensor values to get predictions.")
    print("Type 'quit' or 'exit' to stop.\n")

    try:
        predictor = GreenhousePredictor()
    except FileNotFoundError:
        return

    while True:
        try:
            print("-" * 50)
            user_input = input("\nAir Temperature (°C): ").strip()
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            air_temp = float(user_input)

            humidity = float(input("Humidity (%): ").strip())
            soil_temp = float(input("Soil Temperature (°C): ").strip())
            target_temp = float(input("Target Temperature (°C): ").strip())
            target_humidity = float(input("Target Humidity (%): ").strip())
            prev_fan_speed = float(input("Previous Fan Speed: ").strip())
            prev_humidifier_mode = float(input("Previous Humidifier Mode (0-3): ").strip())

            # Make prediction
            fan_speed, humid_mode, humid_label = predictor.predict(
                air_temp, humidity, soil_temp,
                target_temp, target_humidity,
                prev_fan_speed, prev_humidifier_mode
            )

            print("\n📤 PREDICTIONS:")
            print(f"  🌀 Fan Speed: {fan_speed:.2f}")
            print(f"  💧 Humidifier Mode: {humid_mode} ({humid_label})")

        except ValueError:
            print("Invalid input. Please enter numeric values.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--interactive':
            interactive_prediction()
        elif len(sys.argv) == 8:
            # Command line prediction mode
            try:
                result = predict_single(
                    float(sys.argv[1]),  # air_temp
                    float(sys.argv[2]),  # humidity
                    float(sys.argv[3]),  # soil_temp
                    float(sys.argv[4]),  # target_temp
                    float(sys.argv[5]),  # target_humidity
                    float(sys.argv[6]),  # prev_fan_speed
                    float(sys.argv[7])   # prev_humidifier_mode
                )
                print_prediction(result)
            except ValueError as e:
                print(f"Error: Invalid argument - {e}")
                print("\nUsage: python predict.py <air_temp> <humidity> <soil_temp> "
                      "<target_temp> <target_humidity> <prev_fan_speed> <prev_humidifier_mode>")
        else:
            print("Usage:")
            print("  Interactive mode: python predict.py --interactive")
            print("  Single prediction: python predict.py <air_temp> <humidity> <soil_temp> "
                  "<target_temp> <target_humidity> <prev_fan_speed> <prev_humidifier_mode>")
    else:
        # Demo prediction with sample values
        print("Running demo prediction with sample values...")
        result = predict_single(
            air_temp=26.5,
            humidity=75.0,
            soil_temp=24.0,
            target_temp=24.0,
            target_humidity=65.0,
            prev_fan_speed=50.0,
            prev_humidifier_mode=1.0
        )
        print_prediction(result)

        print("\nTo run interactive mode: python predict.py --interactive")
        print("To make a single prediction: python predict.py <air_temp> <humidity> <soil_temp> "
              "<target_temp> <target_humidity> <prev_fan_speed> <prev_humidifier_mode>")

