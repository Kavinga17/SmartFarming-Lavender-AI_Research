"""
Preprocessing Module for Greenhouse Climate Control System.

This module handles data preprocessing including train-test splitting
and feature scaling for machine learning model training.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os


def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2,
               random_state: int = 42) -> tuple:
    """
    Split data into training and testing sets.

    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Proportion of data to use for testing (default: 0.2).
        random_state: Random seed for reproducibility (default: 42).

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    return X_train, X_test, y_train, y_test


def create_scaler(X_train: pd.DataFrame) -> StandardScaler:
    """
    Create and fit a StandardScaler on training data.

    Args:
        X_train: Training feature DataFrame.

    Returns:
        Fitted StandardScaler object.
    """
    scaler = StandardScaler()
    scaler.fit(X_train)
    return scaler


def scale_features(X: pd.DataFrame, scaler: StandardScaler) -> np.ndarray:
    """
    Scale features using a fitted StandardScaler.

    Args:
        X: Feature DataFrame to scale.
        scaler: Fitted StandardScaler object.

    Returns:
        Scaled features as numpy array.
    """
    return scaler.transform(X)


def save_scaler(scaler: StandardScaler, file_path: str) -> None:
    """
    Save a fitted scaler to a file.

    Args:
        scaler: Fitted StandardScaler object.
        file_path: Path where to save the scaler.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    joblib.dump(scaler, file_path)
    print(f"Scaler saved to: {file_path}")


def load_scaler(file_path: str) -> StandardScaler:
    """
    Load a fitted scaler from a file.

    Args:
        file_path: Path to the saved scaler file.

    Returns:
        Loaded StandardScaler object.

    Raises:
        FileNotFoundError: If the scaler file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Scaler file not found: {file_path}")
    return joblib.load(file_path)


def preprocess_pipeline(X: pd.DataFrame, y_fan: pd.Series, y_humid: pd.Series,
                        test_size: float = 0.2, random_state: int = 42,
                        save_scaler_path: str = None) -> dict:
    """
    Complete preprocessing pipeline for the greenhouse dataset.

    Args:
        X: Feature DataFrame.
        y_fan: Fan speed target Series.
        y_humid: Humidifier mode target Series.
        test_size: Proportion of data to use for testing (default: 0.2).
        random_state: Random seed for reproducibility (default: 42).
        save_scaler_path: Path to save the fitted scaler (optional).

    Returns:
        Dictionary containing all preprocessed data and the scaler.
    """
    # Split data for fan speed model
    X_train_fan, X_test_fan, y_train_fan, y_test_fan = split_data(
        X, y_fan, test_size, random_state
    )

    # Split data for humidifier model (using same split for consistency)
    X_train_humid, X_test_humid, y_train_humid, y_test_humid = split_data(
        X, y_humid, test_size, random_state
    )

    # Create and fit scaler on training data
    scaler = create_scaler(X_train_fan)

    # Scale features
    X_train_fan_scaled = scale_features(X_train_fan, scaler)
    X_test_fan_scaled = scale_features(X_test_fan, scaler)
    X_train_humid_scaled = scale_features(X_train_humid, scaler)
    X_test_humid_scaled = scale_features(X_test_humid, scaler)

    # Save scaler if path provided
    if save_scaler_path:
        save_scaler(scaler, save_scaler_path)

    return {
        'X_train_fan': X_train_fan_scaled,
        'X_test_fan': X_test_fan_scaled,
        'y_train_fan': y_train_fan,
        'y_test_fan': y_test_fan,
        'X_train_humid': X_train_humid_scaled,
        'X_test_humid': X_test_humid_scaled,
        'y_train_humid': y_train_humid,
        'y_test_humid': y_test_humid,
        'scaler': scaler,
        'feature_names': list(X.columns)
    }


if __name__ == "__main__":
    # Test the preprocessing module
    from data_loader import load_dataset, drop_timestamp, get_features_and_labels

    dataset_path = "../DataSet/greenhouse_ai_climate_dataset_1500.csv"

    # Load and prepare data
    df = load_dataset(dataset_path)
    df = drop_timestamp(df)
    X, y_fan, y_humid = get_features_and_labels(df)

    # Run preprocessing pipeline
    processed_data = preprocess_pipeline(
        X, y_fan, y_humid,
        save_scaler_path="../models/scaler.pkl"
    )

    print(f"Training set size: {len(processed_data['X_train_fan'])}")
    print(f"Test set size: {len(processed_data['X_test_fan'])}")
    print(f"Feature names: {processed_data['feature_names']}")

