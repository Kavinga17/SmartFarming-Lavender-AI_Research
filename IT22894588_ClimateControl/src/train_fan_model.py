"""
Fan Speed Model Training Module for Greenhouse Climate Control System.

This module handles training the RandomForestRegressor model for
predicting fan speed based on sensor data.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor


def create_fan_model(n_estimators: int = 100, max_depth: int = None,
                     min_samples_split: int = 2, min_samples_leaf: int = 1,
                     random_state: int = 42) -> RandomForestRegressor:
    """
    Create a RandomForestRegressor model for fan speed prediction.

    Args:
        n_estimators: Number of trees in the forest (default: 100).
        max_depth: Maximum depth of the trees (default: None).
        min_samples_split: Minimum samples required to split a node (default: 2).
        min_samples_leaf: Minimum samples required at a leaf node (default: 1).
        random_state: Random seed for reproducibility (default: 42).

    Returns:
        Configured RandomForestRegressor model.
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1  # Use all available cores
    )
    return model


def train_fan_model(model: RandomForestRegressor, X_train: np.ndarray,
                    y_train: np.ndarray) -> RandomForestRegressor:
    """
    Train the fan speed model on the provided data.

    Args:
        model: RandomForestRegressor model to train.
        X_train: Training features (scaled).
        y_train: Training labels (fan speeds).

    Returns:
        Trained RandomForestRegressor model.
    """
    print("Training fan speed model...")
    model.fit(X_train, y_train)
    print("Fan speed model training completed!")
    return model


def save_fan_model(model: RandomForestRegressor, file_path: str) -> None:
    """
    Save the trained fan model to a file.

    Args:
        model: Trained RandomForestRegressor model.
        file_path: Path where to save the model.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    joblib.dump(model, file_path)
    print(f"Fan model saved to: {file_path}")


def load_fan_model(file_path: str) -> RandomForestRegressor:
    """
    Load a trained fan model from a file.

    Args:
        file_path: Path to the saved model file.

    Returns:
        Loaded RandomForestRegressor model.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fan model file not found: {file_path}")
    return joblib.load(file_path)


def get_feature_importance(model: RandomForestRegressor,
                           feature_names: list) -> dict:
    """
    Get feature importance scores from the trained model.

    Args:
        model: Trained RandomForestRegressor model.
        feature_names: List of feature names.

    Returns:
        Dictionary mapping feature names to importance scores.
    """
    importance = model.feature_importances_
    return dict(zip(feature_names, importance))


if __name__ == "__main__":
    # Full training pipeline for fan model
    from data_loader import load_dataset, drop_timestamp, get_features_and_labels
    from preprocess import preprocess_pipeline
    from evaluate import evaluate_regression_model

    # Load and preprocess data
    dataset_path = "../DataSet/greenhouse_ai_climate_dataset_1500.csv"
    df = load_dataset(dataset_path)
    df = drop_timestamp(df)
    X, y_fan, y_humid = get_features_and_labels(df)

    # Preprocess data
    processed_data = preprocess_pipeline(
        X, y_fan, y_humid,
        save_scaler_path="../models/scaler.pkl"
    )

    # Create and train model
    model = create_fan_model(n_estimators=100, random_state=42)
    model = train_fan_model(
        model,
        processed_data['X_train_fan'],
        processed_data['y_train_fan']
    )

    # Evaluate model
    print("\n" + "=" * 50)
    print("Fan Speed Model Evaluation")
    print("=" * 50)
    metrics = evaluate_regression_model(
        model,
        processed_data['X_test_fan'],
        processed_data['y_test_fan']
    )

    # Print feature importance
    print("\nFeature Importance:")
    importance = get_feature_importance(model, processed_data['feature_names'])
    for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {score:.4f}")

    # Save model
    save_fan_model(model, "../models/fan_model.pkl")

