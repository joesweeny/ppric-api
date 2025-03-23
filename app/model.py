import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
import os
import pickle
import time


def load_and_preprocess_data(file_path="data/user_activity_dataset.csv"):
    """Load and preprocess the dataset."""
    print("Loading data...")
    df = pd.read_csv(file_path)

    feature_columns = [
        "headless", "cookiesEnabled", "pageLoadTime",
        "event_mousemove", "event_keydown", "event_scroll", "event_copy",
        "ip_is_datacenter", "screen_width", "screen_height",
        "screen_devicePixelRatio", "viewport_innerWidth", "viewport_innerHeight",
        "battery_level", "battery_charging", "battery_chargingTime",
        "hardware_cpuCores", "hardware_deviceMemory"
    ]
    target_column = "target"

    categorical_cols = ["headless", "cookiesEnabled", "event_mousemove", "event_keydown",
                        "event_scroll", "event_copy", "ip_is_datacenter", "battery_charging"]
    le_dict = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        le_dict[col] = le

    X = df[feature_columns]
    y = df[target_column].apply(lambda x: 0 if x == 1 else 100)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, X_test, y_train, y_test, feature_columns, le_dict


def train_random_forest_regressor(X_train, X_test, y_train, y_test, feature_columns):
    """Train a Random Forest Regressor and evaluate it."""
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )

    print("Training Random Forest Regressor model...")
    start_time = time.time()
    rf_model.fit(X_train, y_train)
    training_time = time.time() - start_time
    print(f"Training completed in {training_time:.1f} seconds")

    y_pred = rf_model.predict(X_test)

    y_pred = np.clip(y_pred, 0, 100)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Mean Squared Error on test set: {mse:.2f}")
    print(f"R² Score on test set: {r2:.4f}")

    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\nFeature Importance:")
    print(feature_importance)

    print("\nSample Predictions (0 = Sharp, 100 = Square):")
    for i in range(5):
        print(f"Sample {i + 1}: Predicted Score = {y_pred[i]:.2f}, Actual Score = {y_test.iloc[i]}")

    return rf_model


def save_model(model, file_path="rf_regressor_model.pkl"):
    """Save the trained model to a file."""
    with open(file_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {file_path}")


def build_and_train_model():
    """Main function to build and return the trained model."""
    if not os.path.exists("data"):
        raise FileNotFoundError("Data directory not found. Please ensure 'data/user_activity_dataset.csv' exists.")

    X_train, X_test, y_train, y_test, feature_columns, le_dict = load_and_preprocess_data()

    trained_model = train_random_forest_regressor(X_train, X_test, y_train, y_test, feature_columns)

    save_model(trained_model)

    return trained_model


if __name__ == "__main__":
    model = build_and_train_model()

    # Example of how to use the model
    print("\nModel is ready for use")
