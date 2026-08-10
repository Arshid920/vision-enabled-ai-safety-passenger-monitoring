import joblib
import pandas as pd
import os
from pathlib import Path

# Resolve paths
BASE_DIR = Path(__file__).resolve().parents[2] / "streambit"
MODEL_PATH = BASE_DIR / "boat_safety_random_forest.pkl"
ENCODER_PATH = BASE_DIR / "decision_label_encoder.pkl"

_model = None
_label_encoder = None

def load_model():
    global _model, _label_encoder
    if _model is None:
        try:
            if not MODEL_PATH.exists() or not ENCODER_PATH.exists():
                print(f"[ML Service] Models not found at {MODEL_PATH}")
                return False
            _model = joblib.load(MODEL_PATH)
            _label_encoder = joblib.load(ENCODER_PATH)
            print("[ML Service] Models loaded successfully")
            return True
        except Exception as e:
            print(f"[ML Service] Error loading models: {e}")
            return False
    return True

def predict_safety(wind_speed: str, wave_height: str, weather: str, day: str, boat_condition: str) -> str:
    """
    Predicts voyage safety based on environmental conditions.
    Returns: 'Safe', 'Caution', or 'Unsafe'
    """
    if not load_model():
        return "Unknown"

    # Create DataFrame with exact column names expected by the model
    input_df = pd.DataFrame([{
        "Wind Speed": wind_speed,
        "Wave Height": wave_height,
        "Weather": weather,
        "Day of the Week": day,
        "Boat Technical Condition": boat_condition
    }])

    try:
        pred = _model.predict(input_df)[0]
        decision = _label_encoder.inverse_transform([pred])[0]
        
        # Map 'Moderate' to 'Caution' for UI consistency
        if decision == "Moderate":
            return "Caution"
            
        return decision
    except Exception as e:
        print(f"[ML Service] Prediction error: {e}")
        return "Error"
