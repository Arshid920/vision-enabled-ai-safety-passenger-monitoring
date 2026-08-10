# AI Boat Safety & Monitoring System

This project is a comprehensive safety solution for watercraft, integrating Computer Vision and Machine Learning.

## 1. Computer Vision Module (YOLO + OpenCV)
Located in `people_counter/yolov8_live_counter.py`

This module performs real-time passenger detection and monitoring using live camera feeds. The system:
- Detects and counts passengers.
- Checks for overcrowding conditions (Max Capacity: 5).
- Monitors life-jacket compliance.
- Identifies person-overboard situations (Boundary Check).
- Generates a heatmap to analyze passenger movement distribution within the boat.

## 2. Machine Learning Safety Prediction Module (Random Forest)
Located in `streambit/`

This module predicts voyage safety levels (Safe / Caution / Unsafe) using environmental and operational parameters:
- **Inputs**: Wind Speed, Wave Height, Weather Condition, Day/Time, Boat Technical Condition.
- **Model**: Random Forest Classifier (`boat_safety_random_forest.pkl`).
- **Training**: Uses `retrain_model.py` and saved encoders.

## 3. Unified Monitoring Dashboard (Planned)
The system aims to integrate both modules through a backend (currently exploring Flask/Streamlit integration) to display results on a real-time monitoring dashboard for boat drivers.

### Dependencies
- Ultralytics YOLOv8
- OpenCV (cv2)
- CVZone
- Pandas, NumPy, Scikit-learn
- Streamlit / Flask
