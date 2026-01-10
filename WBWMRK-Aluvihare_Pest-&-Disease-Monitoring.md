

## 👨‍💻 Developer Information

<div align="center">

**Developer:** WBWMRK Aluvihare - IT22304506
**Component:** Pest & Disease Detection and Real-time Monitoring System  
**Project:** SmartFarming-Lavender-AI 🌱💜

</div>

---

## 📋 Overview

AI-powered detection system using **YOLOv8** and **ESP32-CAM** for real-time monitoring of lavender health, detecting diseases and pest infestations with automatic alerts.

---

## ✨ Key Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 📹 **Live Detection** | Continuous monitoring via ESP32-CAM (320x240 @ 10 FPS) |
| 🎯 **3 Detection Classes** | Disease, Healthy plants, and Insects |
| 🔔 **Automatic Alerts** | Buzzer sound + LED flash on pest detection |
| 💻 **Dual Modes** | Static image analysis & Real-time streaming |
| ✅ **Stability Buffer** | 10-frame buffer to reduce false alarms |
| ⚡ **Auto-Recovery** | Network failure auto-reconnection |

</div>

---

## 🛠️ Technology Stack

<div align="center">

### Hardware Components
![ESP32](https://img.shields.io/badge/ESP32--CAM-000000?style=for-the-badge&logo=espressif&logoColor=white)
![Hardware](https://img.shields.io/badge/Buzzer-FF6B6B?style=for-the-badge&logo=arduino&logoColor=white)
![LED](https://img.shields.io/badge/LED-FFD93D?style=for-the-badge&logo=electron&logoColor=black)

### Software & Frameworks
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![OpenCV](https://img.shields.io/badge/opencv-%23white.svg?style=for-the-badge&logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)

### AI & ML
![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)
![Ultralytics](https://img.shields.io/badge/Ultralytics-6366F1?style=for-the-badge)

### Communication
![WiFi](https://img.shields.io/badge/WiFi-0078D4?style=for-the-badge&logo=wifi&logoColor=white)
![UDP](https://img.shields.io/badge/UDP-FF4500?style=for-the-badge)

</div>

---

## 🔄 System Architecture
```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐      ┌──────────────┐
│  ESP32-CAM  │─────▶│ WiFi Stream  │─────▶│ YOLOv8 Model   │─────▶│ Alert System │
│  (Field)    │      │ (Port 81)    │      │ (Detection)    │      │ (Buzzer+LED) │
└─────────────┘      └──────────────┘      └────────────────┘      └──────────────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │   Farmer     │
                                            │ Notification │
                                            └──────────────┘
```

---

## 📊 Model Training Configuration

<div align="center">

| Parameter | Value |
|-----------|-------|
| **Model Architecture** | YOLOv8m (Medium) |
| **Training Epochs** | 50 |
| **Batch Size** | 8 |
| **Image Resolution** | 960x960 (training), 320x240 (inference) |
| **Confidence Threshold** | 0.20 (live), 0.25 (static) |
| **GPU Acceleration** | CUDA-enabled |

### Detection Classes

| Class ID | Category | Detection Color |
|:--------:|:---------|:---------------:|
| 0 | Lavender_Disease | 🔴 Red |
| 1 | Lavender_Healthy | 🟢 Green |
| 2 | Insect/Pest | 🟡 Yellow |

</div>

---

## 📦 Dataset & Preprocessing

- **Structure:** Images folder (train/val) + Labels folder (YOLO format)
- **Annotation Format:** `class_id center_x center_y width height` (normalized 0-1)
- **Data Collection:** Field images of lavender in various health states
- **Annotation Tools:** LabelImg / Roboflow
- **Augmentation:** Applied during training for robustness

---

## 🚀 Installation & Setup
```bash
# Install Python dependencies
pip install ultralytics opencv-python numpy

# Run detection systems
python Insect_live.py          # Live monitoring
python Detect_Lavender.py      # Static image analysis
python Model_Train.py          # Train custom model
```

### ESP32-CAM Setup
```cpp
1. Flash Iot_ChipCode.txt to ESP32-CAM via Arduino IDE
2. Update WiFi credentials in wifi_con.txt
3. Note the assigned IP address from Serial Monitor
4. Update ESP32_IP in Insect_live.py
```

---

## 🎮 Interactive Controls

<div align="center">

| Key | Function |
|:---:|:---------|
| `Q` | Quit program |
| `S` | Save screenshot |
| `L` | Manual LED toggle |
| `T` | Test LED connection |
| `D` | Toggle debug mode |
| `+` / `-` | Adjust confidence threshold |

</div>

---

## 🎯 System Benefits

<div align="center">

| Benefit | Impact |
|---------|--------|
| 🔍 **Early Detection** | Identifies threats before visible damage occurs |
| ⏰ **24/7 Monitoring** | Continuous surveillance without human intervention |
| ⚡ **Immediate Response** | Real-time alerts enable quick action |
| 💰 **Cost-effective** | Low-cost ESP32-CAM hardware (~$5) |
| 📈 **Scalable** | Deploy multiple cameras across large fields |
| 📊 **Data-driven** | Logs detection events for trend analysis |

</div>

---

## 📂 Project Files

<div align="center">

| File | Purpose |
|------|---------|
| `Detect_Lavender.py` | Static image detection script |
| `Insect_live.py` | Real-time monitoring system |
| `Model_Train.py` | Model training script |
| `config.yaml` | Dataset configuration |
| `Iot_ChipCode.txt` | ESP32-CAM firmware code |
| `wifi_con.txt` | WiFi credentials configuration |

</div>

---

## 🏆 Technical Achievements

<div align="center">

✅ False positive reduction using 10-frame stability buffer  
✅ Network reliability with automatic reconnection  
✅ Resource optimization for low-power ESP32 hardware  
✅ Real-time performance achieving 10 FPS  
✅ Environmental variation handling through diverse training data  

</div>

---

## 📈 Performance Metrics

<div align="center">
```
Detection Accuracy: Optimized for field conditions
Processing Speed: ~10 FPS real-time inference
Latency: <100ms per frame
False Positive Rate: Reduced via stability buffer
Power Efficiency: Optimized for ESP32 constraints
Network Resilience: Auto-reconnection on failure
```

</div>

---

## 🌟 Project Impact

This pest detection system enables **proactive lavender farm management** by providing real-time monitoring and immediate alerts, reducing crop loss and minimizing pesticide usage through targeted interventions. The integration of computer vision with IoT creates a robust, scalable solution for modern agricultural challenges.

---

<div align="center">

<img width="100%" height="50" src="https://i.imgur.com/dBaSKWF.gif" />

### 🌱 Part of SmartFarming-Lavender-AI Research Project 💜

**Final Year Research Project - Smart Agriculture & IoT Integration**

<br/>

<h6>💡 "Innovation in agriculture is not just about technology, it's about protecting nature's gifts" </h6>

<img width="100%" height="50" src="https://i.imgur.com/dBaSKWF.gif" />

![Footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer)

</div>
