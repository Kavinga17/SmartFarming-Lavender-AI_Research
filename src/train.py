"""
Main Training Script for Greenhouse Climate Control System.

This script orchestrates the complete training pipeline:
1. Load and preprocess data
2. Train fan speed regression model
3. Train humidifier classification model
4. Evaluate both models
5. Save models and scaler
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data_loader import load_dataset, drop_timestamp, get_features_and_labels
from preprocess import preprocess_pipeline
from train_fan_model import create_fan_model, train_fan_model, save_fan_model, get_feature_importance
from train_humidifier_model import create_humidifier_model, train_humidifier_model, save_humidifier_model
from evaluate import evaluate_regression_model, evaluate_classification_model, print_model_summary


def main():
    """Main training function."""
    print("=" * 60)
    print("🌱 GREENHOUSE CLIMATE CONTROL - MODEL TRAINING PIPELINE")
    print("=" * 60)

    # Paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dataset_path = os.path.join(base_dir, "DataSet", "greenhouse_ai_climate_dataset_1500.csv")
    models_dir = os.path.join(base_dir, "models")

    # Create models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)

    # Step 1: Load dataset
    print("\n📂 Step 1: Loading dataset...")
    print("-" * 40)
    df = load_dataset(dataset_path)
    print(f"  Loaded {len(df)} samples with {len(df.columns)} columns")

    # Step 2: Drop timestamp column
    print("\n🔧 Step 2: Preprocessing data...")
    print("-" * 40)
    df = drop_timestamp(df)
    print(f"  Dropped timestamp column, remaining columns: {len(df.columns)}")

    # Step 3: Split features and labels
    print("\n📊 Step 3: Splitting features and labels...")
    print("-" * 40)
    X, y_fan, y_humid = get_features_and_labels(df)
    print(f"  Features shape: {X.shape}")
    print(f"  Fan speed labels: {len(y_fan)} samples")
    print(f"  Humidifier mode labels: {len(y_humid)} samples")
    print(f"  Humidifier mode distribution:")
    for mode in sorted(y_humid.unique()):
        count = (y_humid == mode).sum()
        print(f"    Mode {int(mode)}: {count} samples ({count/len(y_humid)*100:.1f}%)")

    # Step 4: Train-test split and scaling
    print("\n✂️ Step 4: Train-test split (80/20) and feature scaling...")
    print("-" * 40)
    scaler_path = os.path.join(models_dir, "scaler.pkl")
    processed_data = preprocess_pipeline(
        X, y_fan, y_humid,
        test_size=0.2,
        random_state=42,
        save_scaler_path=scaler_path
    )
    print(f"  Training samples: {len(processed_data['X_train_fan'])}")
    print(f"  Test samples: {len(processed_data['X_test_fan'])}")

    # Step 5: Train fan speed model
    print("\n🌀 Step 5: Training fan speed model (RandomForestRegressor)...")
    print("-" * 40)
    fan_model = create_fan_model(n_estimators=100, random_state=42)
    fan_model = train_fan_model(
        fan_model,
        processed_data['X_train_fan'],
        processed_data['y_train_fan']
    )

    # Step 6: Train humidifier model
    print("\n💧 Step 6: Training humidifier model (RandomForestClassifier)...")
    print("-" * 40)
    humid_model = create_humidifier_model(n_estimators=100, random_state=42)
    humid_model = train_humidifier_model(
        humid_model,
        processed_data['X_train_humid'],
        processed_data['y_train_humid']
    )

    # Step 7: Evaluate models
    print("\n📈 Step 7: Evaluating models...")
    print("-" * 40)

    print("\n🌀 Fan Speed Model (Regression):")
    fan_metrics = evaluate_regression_model(
        fan_model,
        processed_data['X_test_fan'],
        processed_data['y_test_fan']
    )

    print("\n💧 Humidifier Mode Model (Classification):")
    humid_metrics = evaluate_classification_model(
        humid_model,
        processed_data['X_test_humid'],
        processed_data['y_test_humid']
    )

    # Step 8: Print feature importance
    print("\n🔍 Feature Importance Analysis:")
    print("-" * 40)

    print("\n  Fan Speed Model:")
    fan_importance = get_feature_importance(fan_model, processed_data['feature_names'])
    for feature, score in sorted(fan_importance.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score * 50)
        print(f"    {feature:25s}: {score:.4f} {bar}")

    print("\n  Humidifier Mode Model:")
    from train_humidifier_model import get_feature_importance as get_humid_importance
    humid_importance = get_humid_importance(humid_model, processed_data['feature_names'])
    for feature, score in sorted(humid_importance.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score * 50)
        print(f"    {feature:25s}: {score:.4f} {bar}")

    # Step 9: Save models
    print("\n💾 Step 8: Saving models...")
    print("-" * 40)
    fan_model_path = os.path.join(models_dir, "fan_model.pkl")
    humid_model_path = os.path.join(models_dir, "humidifier_model.pkl")

    save_fan_model(fan_model, fan_model_path)
    save_humidifier_model(humid_model, humid_model_path)

    # Final summary
    print_model_summary(fan_metrics, humid_metrics)

    print("\n✅ Training pipeline completed successfully!")
    print(f"   Models saved to: {models_dir}")
    print("   - fan_model.pkl")
    print("   - humidifier_model.pkl")
    print("   - scaler.pkl")
    print("\n   To make predictions, run: python predict.py --interactive")


if __name__ == "__main__":
    main()

