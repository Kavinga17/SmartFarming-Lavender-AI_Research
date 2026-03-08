"""
Evaluation Module for Greenhouse Climate Control System.

This module provides evaluation metrics for both regression (fan speed)
and classification (humidifier mode) models.
"""

import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score
)


def evaluate_regression_model(model, X_test: np.ndarray,
                              y_test: np.ndarray) -> dict:
    """
    Evaluate a regression model using MAE, RMSE, and R² metrics.

    Args:
        model: Trained regression model with predict method.
        X_test: Test features (scaled).
        y_test: True test labels.

    Returns:
        Dictionary containing MAE, RMSE, and R² scores.
    """
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2
    }

    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"R² Score: {r2:.4f}")

    return metrics


def evaluate_classification_model(model, X_test: np.ndarray,
                                  y_test: np.ndarray,
                                  class_labels: list = None) -> dict:
    """
    Evaluate a classification model using accuracy and confusion matrix.

    Args:
        model: Trained classification model with predict method.
        X_test: Test features (scaled).
        y_test: True test labels.
        class_labels: Optional list of class labels for display.

    Returns:
        Dictionary containing accuracy and confusion matrix.
    """
    if class_labels is None:
        class_labels = ['Off', 'Low', 'Medium', 'High']

    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    # Calculate additional metrics
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    metrics = {
        'Accuracy': acc,
        'Precision': precision,
        'Recall': recall,
        'F1_Score': f1,
        'Confusion_Matrix': cm
    }

    print(f"Accuracy: {acc:.4f}")
    print(f"Precision (weighted): {precision:.4f}")
    print(f"Recall (weighted): {recall:.4f}")
    print(f"F1 Score (weighted): {f1:.4f}")
    print("\nConfusion Matrix:")
    print(cm)

    # Print classification report
    print("\nClassification Report:")
    unique_labels = np.unique(np.concatenate([y_test, y_pred]))
    target_names = [class_labels[int(i)] for i in unique_labels if int(i) < len(class_labels)]
    print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))

    return metrics


def print_model_summary(regression_metrics: dict,
                        classification_metrics: dict) -> None:
    """
    Print a summary of both models' performance.

    Args:
        regression_metrics: Dictionary of regression model metrics.
        classification_metrics: Dictionary of classification model metrics.
    """
    print("\n" + "=" * 60)
    print("GREENHOUSE CLIMATE CONTROL - MODEL EVALUATION SUMMARY")
    print("=" * 60)

    print("\n📊 FAN SPEED MODEL (Regression)")
    print("-" * 40)
    print(f"  MAE:  {regression_metrics['MAE']:.4f}")
    print(f"  RMSE: {regression_metrics['RMSE']:.4f}")
    print(f"  R²:   {regression_metrics['R2']:.4f}")

    print("\n🌡️ HUMIDIFIER MODE MODEL (Classification)")
    print("-" * 40)
    print(f"  Accuracy:  {classification_metrics['Accuracy']:.4f}")
    print(f"  Precision: {classification_metrics['Precision']:.4f}")
    print(f"  Recall:    {classification_metrics['Recall']:.4f}")
    print(f"  F1 Score:  {classification_metrics['F1_Score']:.4f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Test evaluation with trained models
    from data_loader import load_dataset, drop_timestamp, get_features_and_labels
    from preprocess import preprocess_pipeline
    from train_fan_model import create_fan_model, train_fan_model
    from train_humidifier_model import create_humidifier_model, train_humidifier_model

    # Load and preprocess data
    dataset_path = "../DataSet/greenhouse_ai_climate_dataset_1500.csv"
    df = load_dataset(dataset_path)
    df = drop_timestamp(df)
    X, y_fan, y_humid = get_features_and_labels(df)

    # Preprocess data
    processed_data = preprocess_pipeline(X, y_fan, y_humid)

    # Train fan model
    fan_model = create_fan_model()
    fan_model = train_fan_model(
        fan_model,
        processed_data['X_train_fan'],
        processed_data['y_train_fan']
    )

    # Train humidifier model
    humid_model = create_humidifier_model()
    humid_model = train_humidifier_model(
        humid_model,
        processed_data['X_train_humid'],
        processed_data['y_train_humid']
    )

    # Evaluate both models
    print("\n" + "=" * 50)
    print("FAN SPEED MODEL EVALUATION")
    print("=" * 50)
    fan_metrics = evaluate_regression_model(
        fan_model,
        processed_data['X_test_fan'],
        processed_data['y_test_fan']
    )

    print("\n" + "=" * 50)
    print("HUMIDIFIER MODE MODEL EVALUATION")
    print("=" * 50)
    humid_metrics = evaluate_classification_model(
        humid_model,
        processed_data['X_test_humid'],
        processed_data['y_test_humid']
    )

    # Print summary
    print_model_summary(fan_metrics, humid_metrics)

