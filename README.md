# 🚤 AI-Based Safety and Passenger Monitoring System

An AI-powered real-time safety and passenger monitoring system designed for boats and watercraft. The system combines **Computer Vision, YOLO object detection, OpenCV, Machine Learning, and FastAPI** to monitor passengers, detect safety violations, evaluate voyage safety, and provide real-time monitoring through a web dashboard.

## 📌 Project Overview

The **AI-Based Safety and Passenger Monitoring System** is designed to improve passenger safety during boat voyages by continuously analyzing live camera footage and environmental/operational conditions.

The system uses computer vision to detect and monitor passengers in real time. It can identify passenger count, overcrowding, passengers moving outside the defined boat boundary, and life-jacket compliance.

A safety prediction module evaluates the current safety conditions and classifies the voyage into three levels:

* 🟢 **Safe**
* 🟡 **Caution**
* 🔴 **Unsafe**

The system provides separate interfaces for **drivers and administrators**, allowing drivers to monitor their current voyage while administrators can review drivers, voyages, safety conditions, and voyage records.

---

## ✨ Key Features

### 👤 Passenger Monitoring

* Real-time passenger detection using YOLO.
* Passenger counting.
* Basic object tracking using a custom tracking algorithm.
* Configurable maximum passenger capacity.
* Detection of passengers outside the defined boat boundary.

### 🦺 Life-Jacket Monitoring

* Detects life jackets using the computer vision model.
* Checks whether detected passengers are wearing life jackets.
* Calculates the number of passengers with and without life jackets.

### 🚨 Safety Monitoring

The system identifies important safety conditions such as:

* Overcrowding
* Passenger outside boat boundary
* Missing life jacket
* Camera availability
* Overall safety status

### 🤖 Machine Learning Safety Prediction

The system includes a Random Forest-based voyage safety prediction module.

The model considers environmental and operational parameters such as:

* Wind Speed
* Wave Height
* Weather Condition
* Day of the Week
* Boat Technical Condition

The prediction is mapped into:

**Safe / Caution / Unsafe**

### 📹 Real-Time Video Streaming

* Live camera feed through the web application.
* MJPEG video streaming.
* Real-time computer vision analysis.
* Camera status monitoring.

### 👨‍✈️ Driver Dashboard

Drivers can:

* Log in securely.
* Register their details.
* Start a voyage.
* Enter voyage conditions.
* View safety predictions.
* Monitor passenger information.
* Monitor safety alerts.
* End the current voyage.

### 👨‍💼 Admin Dashboard

Administrators can:

* View registered drivers.
* Monitor voyage records.
* View active voyages.
* View unsafe voyages.
* View voyage details.
* Review safety logs.
* Activate/deactivate drivers.
* End voyages when required.

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │      Camera         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ OpenCV + YOLO       │
                    │ Object Detection    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Passenger Tracking  │
                    │ & Safety Analysis   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Safety Predictor     │
                    │ Safe/Caution/Unsafe  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ FastAPI Backend      │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       ┌─────────────────┐           ┌─────────────────┐
       │ Driver Dashboard│           │ Admin Dashboard │
       └─────────────────┘           └─────────────────┘
                │                             │
                └──────────────┬──────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ SQLAlchemy Database │
                    │ Users / Trips / Logs │
                    └─────────────────────┘
```

---

## 🛠️ Technologies Used

| Technology      | Purpose                              |
| --------------- | ------------------------------------ |
| Python          | Core programming language            |
| FastAPI         | Backend web framework                |
| YOLO            | Real-time object detection           |
| OpenCV          | Computer vision and video processing |
| CVZone          | Computer vision utilities            |
| Scikit-learn    | Machine learning                     |
| Random Forest   | Voyage safety prediction             |
| Pandas          | Data processing                      |
| NumPy           | Numerical processing                 |
| SQLAlchemy      | Database ORM                         |
| SQLite/Database | Data storage                         |
| Jinja2          | HTML template rendering              |
| Uvicorn         | FastAPI application server           |
| Joblib          | ML model loading                     |

---

## 📂 Project Structure

```text
vision-enabled-ai-safety-passenger-monitoring/
│
├── main.py
├── database.py
├── models.py
├── auth.py
├── dashboard.py
├── video.py
├── cv_service.py
├── ml_wrapper.py
├── safety_predictor.py
├── tracker.py
├── create_admin.py
│
├── requirements.txt
├── .gitignore
├── README.md
│
├── index.html
├── base.html
├── dashboard.html
├── admin_dashboard.html
├── pre_voyage.html
├── transition.html
├── voyage_detail.html
├── voyage_summary.html
├── risk_dashboard.html
│
└── screenshots/
    ├── home.png
    ├── login.png
    ├── admin-login.png
    ├── pre-voyage.png
    ├── voyage-detail.png
    └── voyage-summary.png
```

---

## 🔐 Authentication

The application provides role-based authentication for:

### Driver

Drivers can register and access the driver dashboard.

### Administrator

Administrators can access the administrative dashboard and monitor drivers and voyages.

Passwords are securely hashed before being stored in the database.

---

## 🗄️ Database

The application uses SQLAlchemy models for storing:

### User

Stores:

* Username
* Password hash
* Role
* Full name
* License number
* Boat number
* Active status

### Trip

Stores:

* Driver
* Voyage start time
* Voyage end time
* Safety status
* Passenger information
* Alert count

### SafetyLog

Stores:

* Voyage
* Timestamp
* Safety prediction
* Passenger count
* Safety violations

---

## 🤖 Computer Vision Module

The computer vision service continuously processes camera frames.

The pipeline is:

```text
Camera
   ↓
OpenCV Frame Capture
   ↓
YOLO Object Detection
   ↓
Person Detection
   ↓
Object Tracking
   ↓
Passenger Counting
   ↓
Boundary Detection
   ↓
Life-Jacket Detection
   ↓
Safety Status
```

The system also provides a real-time MJPEG video stream through the FastAPI application.

---

## 🧠 Safety Decision Logic

The real-time safety predictor uses the following priority:

```text
Overcrowding OR Passenger Outside Boundary
                    ↓
                  UNSAFE

No Life Jacket
                    ↓
                 CAUTION

No Safety Violation
                    ↓
                   SAFE
```

This allows the dashboard to immediately communicate the current safety condition.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Arshid920/vision-enabled-ai-safety-passenger-monitoring.git
```

### 2. Enter the project directory

```bash
cd vision-enabled-ai-safety-passenger-monitoring
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

If the project contains the `web_app` package:

```bash
python -m uvicorn web_app.main:app --reload
```

Otherwise, run the appropriate FastAPI entry point based on the project structure.

### 7. Open the application

```text
http://127.0.0.1:8000
```

---

## 📸 Screenshots

### Home Page

![Home Page](screenshots/home.png)

### Login

![Login](screenshots/login.png)

### Admin Login

![Admin Login](screenshots/admin-login.png)

### Pre-Voyage

![Pre Voyage](screenshots/pre-voyage.png)

### Voyage Details

![Voyage Detail](screenshots/voyage-detail.png)

### Voyage Summary

![Voyage Summary](screenshots/voyage-summary.png)

---

## 🔮 Future Enhancements

Possible future improvements include:

* Cloud-based deployment.
* Mobile application integration.
* GPS-based boat tracking.
* Automatic emergency notifications.
* SMS/email alerts.
* Improved passenger re-identification.
* More advanced life-jacket detection.
* Cloud database integration.
* Historical safety analytics.
* Multiple camera support.
* Edge-device deployment for onboard processing.

---

## 🎓 Academic Project

This project demonstrates the practical integration of:

**Artificial Intelligence + Computer Vision + Machine Learning + Web Development + Database Management**

It can be used as an academic project demonstrating how AI technologies can be applied to real-world maritime passenger safety and monitoring.

---

## 👨‍💻 Developer

**Arshid920**

GitHub:
https://github.com/Arshid920

Project Repository:
https://github.com/Arshid920/vision-enabled-ai-safety-passenger-monitoring

---

## 📄 License

This project is developed for educational and academic purposes.
