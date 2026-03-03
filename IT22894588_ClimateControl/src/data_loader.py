"""
Data Loader Module for Greenhouse Climate Control System.

This module handles loading and initial preprocessing of the greenhouse
climate dataset for training machine learning models.
"""

import pandas as pd
import os


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the greenhouse climate dataset from a CSV file.

    Args:
        file_path: Path to the CSV file containing the dataset.

    Returns:
        DataFrame containing the loaded dataset.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is empty or has invalid format.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("Dataset is empty")

    return df


def drop_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove the timestamp column from the dataset.

    Args:
        df: DataFrame containing the dataset with timestamp column.

    Returns:
        DataFrame with the timestamp column removed.
    """
    if 'timestamp' in df.columns:
        df = df.drop(columns=['timestamp'])
    return df


def get_features_and_labels(df: pd.DataFrame) -> tuple:
    """
    Split the dataset into features and target labels.

    Features: air_temp, humidity, soil_temp, target_temp, target_humidity,
              prev_fan_speed, prev_humidifier_mode
    Labels: fan_speed (regression), humidifier_mode (classification)

    Args:
        df: DataFrame containing the preprocessed dataset.

    Returns:
        Tuple of (X, y_fan_speed, y_humidifier_mode)
    """
    feature_columns = [
        'air_temp',
        'humidity',
        'soil_temp',
        'target_temp',
        'target_humidity',
        'prev_fan_speed',
        'prev_humidifier_mode'
    ]

    X = df[feature_columns]
    y_fan_speed = df['fan_speed']
    y_humidifier_mode = df['humidifier_mode']

    return X, y_fan_speed, y_humidifier_mode


if __name__ == "__main__":
    # Test the data loader
    dataset_path = "../DataSet/greenhouse_ai_climate_dataset_1500.csv"

    df = load_dataset(dataset_path)
    print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")

    df = drop_timestamp(df)
    print(f"\nAfter dropping timestamp: {len(df.columns)} columns")

    X, y_fan, y_humid = get_features_and_labels(df)
    print(f"\nFeatures shape: {X.shape}")
    print(f"Fan speed labels shape: {y_fan.shape}")
    print(f"Humidifier mode labels shape: {y_humid.shape}")

