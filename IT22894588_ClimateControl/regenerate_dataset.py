"""
Dataset Regeneration Script for Greenhouse Climate Control System.

This script regenerates the training dataset with stratified humidity values
to ensure all 4 humidifier modes (Off, Low, Medium, High) are represented.
"""

import numpy as np
import pandas as pd

def regenerate_dataset():
    n = 1500
    np.random.seed(42)

    # Generate air_temp and soil_temp
    air_temp = np.random.normal(26.4, 2.5, n).clip(18, 35)
    soil_temp = air_temp - np.random.uniform(0.5, 3.0, n)

    # Target values (constant)
    target_temp = np.full(n, 24.0)
    target_humidity = np.full(n, 65.0)

    # Generate stratified humidity values
    # 300 values from uniform(35, 50) → maps to High (deficit > 15)
    # 250 values from uniform(50, 58) → maps to Medium (deficit > 7)
    # 250 values from uniform(58, 63) → maps to Low (deficit > 2)
    # 700 values from uniform(63, 100) → maps to Off (deficit <= 2)

    np.random.seed(42)  # Reset seed for humidity generation
    humidity_high = np.random.uniform(35, 50, 300)      # High mode
    humidity_medium = np.random.uniform(50, 58, 250)    # Medium mode
    humidity_low = np.random.uniform(58, 63, 250)       # Low mode
    humidity_off = np.random.uniform(63, 100, 700)      # Off mode

    humidity = np.concatenate([humidity_high, humidity_medium, humidity_low, humidity_off])

    # Shuffle the humidity array
    np.random.seed(42)
    np.random.shuffle(humidity)

    # Calculate humidifier_mode based on deficit = 65 - humidity
    def calc_humidifier_mode(h):
        deficit = 65 - h
        if deficit > 15:
            return 3  # High
        elif deficit > 7:
            return 2  # Medium
        elif deficit > 2:
            return 1  # Low
        else:
            return 0  # Off

    humidifier_mode = np.array([calc_humidifier_mode(h) for h in humidity])

    # Calculate fan_speed based on temp_excess = air_temp - 24
    def calc_fan_speed(t):
        temp_excess = t - 24
        if temp_excess > 4:
            return 90
        elif temp_excess > 2:
            return 70
        elif temp_excess > 0:
            return 50
        else:
            return 30

    fan_speed = np.array([calc_fan_speed(t) for t in air_temp])

    # Calculate prev_fan_speed (lag-1 of fan_speed, first value = 50.0)
    prev_fan_speed = np.roll(fan_speed, 1).astype(float)
    prev_fan_speed[0] = 50.0

    # Calculate prev_humidifier_mode (lag-1 of humidifier_mode, first value = 0.0)
    prev_humidifier_mode = np.roll(humidifier_mode, 1).astype(float)
    prev_humidifier_mode[0] = 0.0

    # Generate timestamps
    timestamp = pd.date_range("2024-09-27 12:58:10+05:30", periods=n, freq="5min")

    # Create DataFrame with exact column order
    df = pd.DataFrame({
        'timestamp': timestamp,
        'air_temp': air_temp,
        'humidity': humidity,
        'soil_temp': soil_temp,
        'target_temp': target_temp,
        'target_humidity': target_humidity,
        'prev_fan_speed': prev_fan_speed,
        'prev_humidifier_mode': prev_humidifier_mode,
        'fan_speed': fan_speed,
        'humidifier_mode': humidifier_mode
    })

    # Save to CSV
    output_path = "DataSet/greenhouse_ai_climate_dataset_1500.csv"
    df.to_csv(output_path, index=False)

    # Print class distribution
    print("=" * 50)
    print("Dataset Regeneration Complete!")
    print("=" * 50)
    print(f"\nSaved to: {output_path}")
    print(f"Total rows: {len(df)}")
    print("\nHumidifier Mode Distribution:")
    print(df['humidifier_mode'].value_counts().sort_index())
    print("\nExpected:")
    print("  0 (Off):    ~700 rows (46.7%)")
    print("  1 (Low):    ~250 rows (16.7%)")
    print("  2 (Medium): ~250 rows (16.7%)")
    print("  3 (High):   ~300 rows (20.0%)")
    print("\nFan Speed Distribution:")
    print(df['fan_speed'].value_counts().sort_index())
    print("\nHumidity Statistics:")
    print(f"  Min: {df['humidity'].min():.2f}%")
    print(f"  Max: {df['humidity'].max():.2f}%")
    print(f"  Mean: {df['humidity'].mean():.2f}%")

    return df

if __name__ == "__main__":
    regenerate_dataset()

