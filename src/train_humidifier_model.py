"""
Humidifier Model Training Module for Greenhouse Climate Control System.

This module handles training the RandomForestClassifier model for
predicting humidifier mode based on sensor data.
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def create_humidifier_model(n_estimators: int = 100, max_depth: int = None,
                            min_samples_split: int = 2, min_samples_leaf: int = 1,
                            random_state: int = 42) -> RandomForestClassifier:
    """
    Create a RandomForestClassifier model for humidifier mode prediction.

    Args:
        n_estimators: Number of trees in the forest (default: 100).
        max_depth: Maximum depth of the trees (default: None).
        min_samples_split: Minimum samples required to split a node (default: 2).
        min_samples_leaf: Minimum samples required at a leaf node (default: 1).
        random_state: Random seed for reproducibility (default: 42).

    Returns:
        Configured RandomForestClassifier model.
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1  # Use all available cores
    )
    return model


def train_humidifier_model(model: RandomForestClassifier, X_train: np.ndarray,
                           y_train: np.ndarray) -> RandomForestClassifier:
    """
    Train the humidifier mode model on the provided data.

    Args:
        model: RandomForestClassifier model to train.
        X_train: Training features (scaled).
        y_train: Training labels (humidifier modes: 0=Off, 1=Low, 2=Medium, 3=High).

    Returns:
        Trained RandomForestClassifier model.
    """
    print("Training humidifier mode model...")
    model.fit(X_train, y_train)
    print("Humidifier mode model training completed!")
    return model


def save_humidifier_model(model: RandomForestClassifier, file_path: str) -> None:
    """
    Save the trained humidifier model to a file.

    Args:
        model: Trained RandomForestClassifier model.
        file_path: Path where to save the model.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    joblib.dump(model, file_path)
    print(f"Humidifier model saved to: {file_path}")


def load_humidifier_model(file_path: str) -> RandomForestClassifier:
    """
    Load a trained humidifier model from a file.

    Args:
        file_path: Path to the saved model file.

    Returns:
        Loaded RandomForestClassifier model.

    Raises:
        FileNotFoundError: If the model file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Humidifier model file not found: {file_path}")
    return joblib.load(file_path)


def get_feature_importance(model: RandomForestClassifier,
                           feature_names: list) -> dict:
    """
    Get feature importance scores from the trained model.

    Args:
        model: Trained RandomForestClassifier model.
        feature_names: List of feature names.

    Returns:
        Dictionary mapping feature names to importance scores.
    """
    importance = model.feature_importances_
    return dict(zip(feature_names, importance))


def get_humidifier_mode_label(mode: int) -> str:
    """
    Convert humidifier mode number to human-readable label.

    Args:
        mode: Humidifier mode (0, 1, 2, or 3).

    Returns:
        Human-readable label for the mode.
    """
    labels = {
        0: "Off",
        1: "Low",
        2: "Medium",
        3: "High"
    }
    return labels.get(mode, "Unknown")


if __name__ == "__main__":
    # Full training pipeline for humidifier model
    from data_loader import load_dataset, drop_timestamp, get_features_and_labels
    from preprocess import preprocess_pipeline
    from evaluate import evaluate_classification_model

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
    model = create_humidifier_model(n_estimators=100, random_state=42)
    model = train_humidifier_model(
        model,
        processed_data['X_train_humid'],
        processed_data['y_train_humid']
    )

    # Evaluate model
    print("\n" + "=" * 50)
    print("Humidifier Mode Model Evaluation")
    print("=" * 50)
    metrics = evaluate_classification_model(
        model,
        processed_data['X_test_humid'],
        processed_data['y_test_humid']
    )

    # Print feature importance
    print("\nFeature Importance:")
    importance = get_feature_importance(model, processed_data['feature_names'])
    for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {score:.4f}")

    # Save model
    save_humidifier_model(model, "../models/humidifier_model.pkl")

