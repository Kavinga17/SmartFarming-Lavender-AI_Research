# 🌱 SmartFarming-Lavender-AI 💜

<div align="center">

**An Intelligent Agricultural System for Optimized Lavender Cultivation**

![Status](https://img.shields.io/badge/Status-In_Development-yellow?style=flat-square)
![Research](https://img.shields.io/badge/Type-Final_Year_Project-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 📋 About The Project

**SmartFarming-Lavender-AI** is a comprehensive intelligent farming system designed to revolutionize lavender cultivation through the integration of **IoT sensors**, **AI-powered models**, and **automated smart devices**. This final-year research project demonstrates how cutting-edge technology can transform traditional agriculture into a smart, sustainable, and highly efficient farming ecosystem.

The system addresses critical challenges in lavender farming by providing real-time monitoring, automated control, and predictive analytics across four major domains: soil management, climate control, pest detection, and lighting optimization.

---

## 🎯 System Overview

Our integrated system combines four specialized components working in harmony to optimize every aspect of lavender cultivation:
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SmartFarming-Lavender-AI System                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   🌍 Soil &     │  │  🌡️ Climate     │  │  🐛 Pest &      │         │
│  │   Irrigation    │  │   Control       │  │   Disease       │         │
│  │   Monitoring    │  │   System        │  │   Detection     │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                     │                  │
│           └────────────────────┼─────────────────────┘                  │
│                                │                                        │
│                         ┌──────▼──────┐                                 │
│                         │  Central    │                                 │
│                         │  Control    │                                 │
│                         │  Hub        │                                 │
│                         └──────┬──────┘                                 │
│                                │                                        │
│                         ┌──────▼──────┐                                 │
│                         │   💡 Smart  │                                 │
│                         │   Lighting  │                                 │
│                         │   System    │                                 │
│                         └─────────────┘                                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🌍 Soil & Irrigation
- Real-time soil moisture monitoring
- Automated irrigation scheduling
- Nutrient level tracking
- Water conservation optimization

</td>
<td width="50%">

### 🌡️ Climate Control
- Temperature regulation
- Humidity optimization
- Greenhouse environment monitoring
- Weather-adaptive responses

</td>
</tr>
<tr>
<td width="50%">

### 🐛 Pest & Disease Detection
- AI-powered computer vision
- Real-time threat identification
- Automated alert system
- Eco-friendly pest control

</td>
<td width="50%">

### 💡 Smart Lighting
- Optimized light spectrum
- Growth phase adaptation
- Essential oil enhancement
- Energy-efficient automation

</td>
</tr>
</table>

---

## 👥 Research Team

<div align="center">

| Team Member | Student ID | Component | Focus Area |
|:------------|:-----------|:----------|:-----------|
| **Fernando J.L.S.T.** | IT22XXXXXX | 🌍 Soil & Irrigation System | Water & Nutrient Management |
| **Rubasinghe K.P** | IT22XXXXXX | 🌡️ Climate Control System | Temperature & Humidity Control |
| **WBWMRK Aluvihare** | IT22304506 | 🐛 Pest & Disease Monitoring | AI Detection & Real-time Alerts |
| **Ekanayake S.K** | IT22XXXXXX | 💡 Smart Lighting System | Growth & Oil Production Optimization |

</div>

---

## 📚 Individual Component Documentation

Each component has been developed as an independent module with detailed documentation. Please refer to the individual README files in each component directory for comprehensive technical specifications, implementation details, and usage instructions.

---

## 🏗️ System Architecture

### Overall System Diagram
```
                          ┌─────────────────────────┐
                          │   Farmer Dashboard      │
                          │   (Web/Mobile App)      │
                          └───────────┬─────────────┘
                                      │
                          ┌───────────▼─────────────┐
                          │   Central Cloud Server  │
                          │   - Data Processing     │
                          │   - ML Model Hosting    │
                          │   - Analytics Engine    │
                          └───────────┬─────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
        ┌───────▼────────┐   ┌────────▼───────┐   ┌───────▼────────┐
        │  Soil Sensors  │   │ Climate Sensors│   │  ESP32-CAM     │
        │  - Moisture    │   │ - Temperature  │   │  - Pest Detection
        │  - pH Level    │   │ - Humidity     │   │  - Disease ID  │
        │  - Nutrients   │   │ - CO2 Level    │   │                │
        └───────┬────────┘   └────────┬───────┘   └───────┬────────┘
                │                     │                     │
        ┌───────▼────────┐   ┌────────▼───────┐   ┌───────▼────────┐
        │  Water Pump    │   │  HVAC System   │   │  Alert System  │
        │  Irrigation    │   │  Ventilation   │   │  Buzzer + LED  │
        └────────────────┘   └────────────────┘   └────────────────┘
                                      │
                          ┌───────────▼─────────────┐
                          │   Smart LED System      │
                          │   - Spectrum Control    │
                          │   - Intensity Adjust    │
                          └─────────────────────────┘
```

### Data Flow Architecture
```
Sensor Layer (IoT Devices)
        ↓
Edge Processing (ESP32/Arduino)
        ↓
Network Layer (WiFi/MQTT)
        ↓
Cloud Processing (AWS/Firebase)
        ↓
AI/ML Models (YOLOv8, Decision Trees)
        ↓
Control Commands
        ↓
Actuators (Pumps, HVAC, Lights, Alerts)
        ↓
Farmer Interface (Dashboard/Notifications)
```

---

## 🛠️ Technology Stack

<div align="center">

### Hardware
![ESP32](https://img.shields.io/badge/ESP32-000000?style=for-the-badge&logo=espressif&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-00979D?style=for-the-badge&logo=Arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)

### Software & AI
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Node.js](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white)

### Cloud & Database
![Firebase](https://img.shields.io/badge/firebase-%23039BE5.svg?style=for-the-badge&logo=firebase)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-%2300000f.svg?style=for-the-badge&logo=mysql&logoColor=white)

</div>

---

## 📂 Repository Structure
```
SmartFarming-Lavender-AI/
├── 📁 soil-irrigation/           # Soil & Water Management Component
│   ├── sensors/                  # Sensor code and drivers
│   ├── irrigation-control/       # Automated irrigation system
│   └── README.md                 # Component documentation
│
├── 📁 climate-control/           # Climate Management Component
│   ├── temperature-control/      # Temperature regulation
│   ├── humidity-control/         # Humidity management
│   └── README.md                 # Component documentation
│
├── 📁 pest-detection/            # Pest & Disease Monitoring Component
│   ├── Detect_Lavender.py       # Static image detection
│   ├── Insect_live.py           # Real-time monitoring
│   ├── Model_Train.py           # Training script
│   ├── Iot_ChipCode.txt         # ESP32-CAM firmware
│   └── README.md                # Component documentation
│
├── 📁 smart-lighting/            # Intelligent Lighting Component
│   ├── spectrum-control/         # Light spectrum optimization
│   ├── intensity-control/        # Light intensity management
│   └── README.md                 # Component documentation
│
├── 📁 datasets/                  # Training datasets for all models
├── 📁 models/                    # Trained AI/ML models
├── 📁 docs/                      # Project documentation
├── 📁 dashboard/                 # Web/Mobile dashboard code
└── README.md                     # This file
```

---

## 🚀 Getting Started

### Prerequisites
```bash
# Python 3.8+
# Node.js 14+
# Arduino IDE
# Git
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/SmartFarming-Lavender-AI.git

# Navigate to specific component directory
cd SmartFarming-Lavender-AI/pest-detection

# Install dependencies
pip install -r requirements.txt

# Follow component-specific README for detailed setup
```

---

## 📊 Expected Outcomes

- 🌱 **30% increase** in lavender yield
- 💧 **40% reduction** in water consumption
- 🐛 **50% decrease** in pest-related crop loss
- 💰 **25% cost savings** in resource management
- ♻️ **60% reduction** in pesticide usage

---

## 🎓 Academic Context

**Institution:** [Your University Name]  
**Program:** Bachelor of Science in Information Technology  
**Project Type:** Final Year Research Project  
**Duration:** [Start Date] - [End Date]  
**Supervisor:** [Supervisor Name]

---

## 📄 Research Papers & Documentation

- [Project Proposal](./docs/proposal.pdf)
- [Literature Review](./docs/literature-review.pdf)
- [System Design Document](./docs/system-design.pdf)
- [Final Research Paper](./docs/final-paper.pdf) *(Coming Soon)*

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Special thanks to our project supervisor and university faculty
- Lavender farm owners who provided testing grounds
- Open-source community for amazing tools and libraries

---

<div align="center">

## 📞 Contact

For questions, collaboration, or feedback:

📧 Email: smartfarming.lavender@university.edu  
🌐 Website: [Coming Soon]  
📱 Follow us: [@SmartFarmingAI](https://twitter.com/smartfarmingai)

---

**Made with 💜 by the SmartFarming-Lavender-AI Team**

⭐ Star this repo if you find it useful!

<img width="100%" height="50" src="https://i.imgur.com/dBaSKWF.gif" />

*Transforming traditional agriculture through AI and IoT innovation* 🌱

</div>


