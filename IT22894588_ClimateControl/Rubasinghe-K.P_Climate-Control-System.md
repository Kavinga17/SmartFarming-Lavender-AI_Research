# 🌡️ Intelligent Climate Control System

## SmartFarming-Lavender-AI - Climate Control Component

An **AI-Powered Intelligent Climate Control System** for greenhouse environment management, specifically designed to optimize lavender cultivation conditions through IoT sensors, machine learning models, and automated device control.

---

## 📋 Table of Contents

- [Component Overview](#component-overview)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Hardware Components](#hardware-components)
- [Hardware Wiring Diagram](#hardware-wiring-diagram)
- [Arduino Integration](#arduino-integration)
- [Machine Learning Models](#machine-learning-models)
- [Dataset Description](#dataset-description)
- [Data Preprocessing](#data-preprocessing)
- [Model Performance and Accuracy](#model-performance-and-accuracy)
- [API Documentation](#api-documentation)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Contributors](#contributors)

---

## 🎯 Component Overview

The **Intelligent Climate Control** component is responsible for dynamically adjusting greenhouse temperature and humidity levels using machine learning predictions. This system continuously monitors environmental conditions through IoT sensors and automatically controls climate devices to maintain optimal growing conditions for lavender plants.

### Key Objectives

| Objective | Description |
|-----------|-------------|
| **Temperature Regulation** | Maintain optimal air temperature (22-28°C) for lavender growth |
| **Humidity Control** | Keep relative humidity at ideal levels (55-75%) |
| **Automated Response** | Real-time adjustment of fan speed and humidifier mode |
| **Energy Efficiency** | Optimize device operation to reduce power consumption |
| **Data-Driven Decisions** | Use ML models to predict optimal device settings |

### What This System Controls

| Device | Control Type | Purpose |
|--------|--------------|---------|
| **12V DC Fan** | PWM Speed Control (0-100%) | Air circulation and temperature reduction |
| **Ultrasonic Mist Maker** | Mode Selection (Off/Low/Medium/High) | Humidity adjustment |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT CLIMATE CONTROL SYSTEM                    │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │  GREENHOUSE │
                              │ ENVIRONMENT │
                              └──────┬──────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     DHT22       │       │    DS18B20      │       │   Environment   │
│  ┌───────────┐  │       │  ┌───────────┐  │       │   Parameters    │
│  │ Air Temp  │  │       │  │ Soil Temp │  │       │  ┌───────────┐  │
│  │ Humidity  │  │       │  │ Waterproof│  │       │  │Target Temp│  │
│  └───────────┘  │       │  └───────────┘  │       │  │Target Hum │  │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ESP32 MICROCONTROLLER                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ • Reads DHT22 sensor (air temperature + humidity)               │    │
│  │ • Reads DS18B20 sensor (soil temperature)                       │    │
│  │ • Packages sensor data as JSON                                  │    │
│  │ • Sends HTTP POST request to Flask API                          │    │
│  │ • Receives ML predictions                                       │    │
│  │ • Controls actuators via PWM and digital signals                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     │ WiFi (HTTP POST/Response)
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FLASK API SERVER                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Endpoint: POST /predict                                         │    │
│  │                                                                  │    │
│  │ 1. Receive JSON: {air_temp, humidity, soil_temp,                │    │
│  │                   target_temp, target_humidity,                  │    │
│  │                   prev_fan_speed, prev_humidifier_mode}         │    │
│  │                                                                  │    │
│  │ 2. Load scaler.pkl → Normalize input features                   │    │
│  │                                                                  │    │
│  │ 3. Load fan_model.pkl → Predict fan speed (0-100%)              │    │
│  │                                                                  │    │
│  │ 4. Load humidifier_model.pkl → Predict mode (0-3)               │    │
│  │                                                                  │    │
│  │ 5. Return JSON: {fan_speed, humidifier_mode}                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     │ Predictions
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           ACTUATOR LAYER                                 │
│  ┌────────────────────────────┐    ┌────────────────────────────────┐   │
│  │   L298N MOTOR DRIVER       │    │   ULTRASONIC MIST MAKER        │   │
│  │   + 12V DC FAN             │    │   (Humidifier)                 │   │
│  │   ─────────────────────    │    │   ────────────────────────     │   │
│  │   • PWM Speed: 0-100%      │    │   • Mode 0: Off                │   │
│  │   • Controls air flow      │    │   • Mode 1: Low                │   │
│  │   • Reduces temperature    │    │   • Mode 2: Medium             │   │
│  │   • 12V power supply       │    │   • Mode 3: High               │   │
│  └────────────────────────────┘    └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### Step-by-Step Process Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 1: SENSOR DATA COLLECTION (Every 30 seconds)                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   DHT22 Sensor                    DS18B20 Sensor                         │
│   ┌──────────────────┐            ┌──────────────────┐                   │
│   │ air_temp: 28.5°C │            │ soil_temp: 22.0°C│                   │
│   │ humidity: 65.0%  │            │ (waterproof)     │                   │
│   └──────────────────┘            └──────────────────┘                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 2: DATA TRANSMISSION (HTTP POST to Flask API)                       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   JSON Payload sent to server:                                           │
│   {                                                                      │
│       "air_temp": 28.5,                                                  │
│       "humidity": 65.0,                                                  │
│       "soil_temp": 22.0,                                                 │
│       "target_temp": 25.0,                                               │
│       "target_humidity": 60.0,                                           │
│       "prev_fan_speed": 50.0,                                            │
│       "prev_humidifier_mode": 1                                          │
│   }                                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 3: ML MODEL INFERENCE                                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   1. StandardScaler normalizes input features                            │
│                                                                          │
│   2. RandomForestRegressor predicts fan_speed                            │
│      Input → [28.5, 65.0, 22.0, 25.0, 60.0, 50.0, 1]                     │
│      Output → 75.5 (fan speed percentage)                                │
│                                                                          │
│   3. RandomForestClassifier predicts humidifier_mode                     │
│      Input → [28.5, 65.0, 22.0, 25.0, 60.0, 50.0, 1]                     │
│      Output → 2 (Medium mode)                                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 4: PREDICTION RESPONSE                                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   JSON Response from server:                                             │
│   {                                                                      │
│       "fan_speed": 75.5,                                                 │
│       "humidifier_mode": 2                                               │
│   }                                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 5: ACTUATOR CONTROL                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Fan Control:                    Humidifier Control:                    │
│   ┌─────────────────────┐         ┌─────────────────────┐                │
│   │ PWM Signal: 75.5%   │         │ Mode: 2 (Medium)    │                │
│   │ L298N ENA Pin       │         │ GPIO 25 Signal      │                │
│   │ Fan runs at 75.5%   │         │ Moderate mist       │                │
│   │ speed               │         │ output              │                │
│   └─────────────────────┘         └─────────────────────┘                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Hardware Components

### Complete Hardware List

| Component | Model/Specification | Quantity | Purpose |
|-----------|---------------------|----------|---------|
| **ESP32** | ESP32 DevKit V1 | 1 | WiFi-enabled microcontroller for data collection and device control |
| **DHT22** | AM2302 | 1 | Air temperature and humidity sensor (Accuracy: ±0.5°C, ±2% RH) |
| **DS18B20** | Waterproof Digital Temperature Sensor | 1 | Soil temperature measurement (Range: -55°C to +125°C) |
| **L298N** | Dual H-Bridge Motor Driver | 1 | PWM control for 12V DC fan speed regulation |
| **Ultrasonic Mist Maker** | Ceramic Disc Module | 1 | Humidifier for greenhouse humidity control |
| **12V DC Fan** | Brushless Cooling Fan | 1 | Air circulation and temperature control |
| **Power Supply** | 12V DC Adapter | 1 | Powers fan and motor driver |
| **Jumper Wires** | Male-to-Male, Male-to-Female | Multiple | Circuit connections |
| **4.7kΩ Resistor** | Pull-up Resistor | 1 | Required for DS18B20 data line |

### Hardware Specifications

#### ESP32 DevKit V1
| Specification | Value |
|---------------|-------|
| Microcontroller | Xtensa dual-core 32-bit LX6 |
| Clock Speed | 240 MHz |
| WiFi | 802.11 b/g/n |
| GPIO Pins | 34 |
| Operating Voltage | 3.3V |
| Input Voltage | 5V (via USB) |

#### DHT22 (AM2302) Sensor
| Specification | Value |
|---------------|-------|
| Temperature Range | -40°C to 80°C |
| Temperature Accuracy | ±0.5°C |
| Humidity Range | 0-100% RH |
| Humidity Accuracy | ±2% RH |
| Sampling Rate | 0.5 Hz (once every 2 seconds) |
| Operating Voltage | 3.3V - 5V |

#### DS18B20 Waterproof Temperature Sensor
| Specification | Value |
|---------------|-------|
| Temperature Range | -55°C to +125°C |
| Accuracy | ±0.5°C (from -10°C to +85°C) |
| Resolution | 9-12 bit configurable |
| Protocol | OneWire |
| Operating Voltage | 3.0V - 5.5V |
| Waterproof | Yes (stainless steel probe) |

#### L298N Motor Driver
| Specification | Value |
|---------------|-------|
| Driver Type | Dual H-Bridge |
| Motor Voltage | 5V - 35V |
| Logic Voltage | 5V |
| Max Current | 2A per channel |
| PWM Support | Yes |
| Control Pins | ENA, IN1, IN2 (per channel) |

#### Ultrasonic Mist Maker
| Specification | Value |
|---------------|-------|
| Type | Ceramic Disc Humidifier |
| Operating Modes | 4 (Off, Low, Medium, High) |
| Mist Output | Variable based on mode |
| Operating Voltage | 12V DC |

#### 12V DC Fan
| Specification | Value |
|---------------|-------|
| Type | Brushless DC Fan |
| Voltage | 12V DC |
| Speed Control | PWM (0-100%) |
| Purpose | Air circulation, cooling |

---

## 🔌 Hardware Wiring Diagram

### ESP32 Pin Connections

```
                                    ┌─────────────────┐
                                    │     ESP32       │
                                    │   DevKit V1     │
                                    │                 │
                    ┌───────────────┤ GPIO 4          │◄──── DHT22 Data Pin
                    │               │                 │
                    │  ┌────────────┤ GPIO 5          │◄──── DS18B20 Data Pin (+ 4.7kΩ pull-up)
                    │  │            │                 │
                    │  │  ┌─────────┤ GPIO 12         │◄──── L298N IN1
                    │  │  │         │                 │
                    │  │  │  ┌──────┤ GPIO 13         │◄──── L298N IN2
                    │  │  │  │      │                 │
                    │  │  │  │  ┌───┤ GPIO 14         │◄──── L298N ENA (PWM)
                    │  │  │  │  │   │                 │
                    │  │  │  │  │┌──┤ GPIO 25         │◄──── Mist Maker Control
                    │  │  │  │  ││  │                 │
                    │  │  │  │  ││  │ 3.3V            │◄──── DHT22 VCC, DS18B20 VCC
                    │  │  │  │  ││  │                 │
                    │  │  │  │  ││  │ GND             │◄──── Common Ground
                    │  │  │  │  ││  │                 │
                    │  │  │  │  ││  │ VIN             │◄──── 5V Power Input
                    │  │  │  │  ││  └─────────────────┘
                    │  │  │  │  ││
                    ▼  ▼  ▼  ▼  ▼▼
```

### Complete Wiring Schematic

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE WIRING DIAGRAM                           │
└──────────────────────────────────────────────────────────────────────────┘

    12V Power Supply                          ESP32 DevKit V1
    ┌─────────────┐                          ┌─────────────────┐
    │    12V+     ├──────────────────────────┤                 │
    │             │                          │                 │
    │    GND      ├──────┬───────────────────┤ GND             │
    └─────────────┘      │                   │                 │
                         │                   │ 3.3V ───────┬───┼─────┐
                         │                   │             │   │     │
                         │                   │ GPIO 4 ─────┼───┼──┐  │
    L298N Motor Driver   │                   │             │   │  │  │
    ┌─────────────────┐  │                   │ GPIO 5 ─────┼───┼──┼──┼──┐
    │ 12V  ◄──────────┼──┼── 12V+            │             │   │  │  │  │
    │                 │  │                   │ GPIO 12 ────┼───┼──┼──┼──┼──┐
    │ GND  ◄──────────┼──┤                   │             │   │  │  │  │  │
    │                 │  │                   │ GPIO 13 ────┼───┼──┼──┼──┼──┼──┐
    │ 5V   ───────────┼──┼── (optional)      │             │   │  │  │  │  │  │
    │                 │  │                   │ GPIO 14 ────┼───┼──┼──┼──┼──┼──┼──┐
    │ ENA  ◄──────────┼──┼───────────────────┼─────────────┼───┼──┼──┼──┼──┼──┼──┤
    │                 │  │                   │             │   │  │  │  │  │  │  │
    │ IN1  ◄──────────┼──┼───────────────────┼─────────────┼───┼──┼──┼──┼──┼──┘  │
    │                 │  │                   │             │   │  │  │  │  │     │
    │ IN2  ◄──────────┼──┼───────────────────┼─────────────┼───┼──┼──┼──┼──┘     │
    │                 │  │                   │             │   │  │  │  │        │
    │ OUT1 ───────────┼──┼──┐                │ GPIO 25 ────┼───┼──┼──┼──┼────────┼──┐
    │                 │  │  │                │             │   │  │  │  │        │  │
    │ OUT2 ───────────┼──┼──┼──┐             └─────────────┘   │  │  │  │        │  │
    └─────────────────┘  │  │  │                               │  │  │  │        │  │
                         │  │  │                               │  │  │  │        │  │
    12V DC Fan           │  │  │    DHT22                      │  │  │  │        │  │
    ┌─────────────┐      │  │  │    ┌─────────────┐            │  │  │  │        │  │
    │    (+)  ◄───┼──────┼──┘  │    │ VCC ◄───────┼────────────┘  │  │  │        │  │
    │             │      │     │    │             │               │  │  │        │  │
    │    (-)  ◄───┼──────┼─────┘    │ DATA ◄──────┼───────────────┘  │  │        │  │
    └─────────────┘      │          │             │                  │  │        │  │
                         │          │ GND ◄───────┼──────────────────┼──┼────────┘  │
                         │          └─────────────┘                  │  │           │
                         │                                           │  │           │
                         │          DS18B20                          │  │           │
                         │          ┌─────────────┐                  │  │           │
                         │          │ VCC ◄───────┼──────────────────┘  │           │
                         │          │             │     ┌──[4.7kΩ]──────┤           │
                         │          │ DATA ◄──────┼─────┴───────────────┘           │
                         │          │             │                                 │
                         │          │ GND ◄───────┼─────────────────────────────────┤
                         │          └─────────────┘                                 │
                         │                                                          │
                         │          Ultrasonic Mist Maker                           │
                         │          ┌─────────────┐                                 │
                         │          │ Control ◄───┼─────────────────────────────────┘
                         │          │             │
                         └──────────┤ GND         │
                                    └─────────────┘
```

---

## 📟 Arduino Integration

### Required Arduino Libraries

| Library | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| **WiFi.h** | Built-in | ESP32 WiFi connectivity | Included with ESP32 board package |
| **HTTPClient.h** | Built-in | HTTP POST requests to Flask API | Included with ESP32 board package |
| **DHT.h** | Latest | DHT22 sensor communication | Library Manager: "DHT sensor library" by Adafruit |
| **OneWire.h** | Latest | OneWire protocol for DS18B20 | Library Manager: "OneWire" by Paul Stoffregen |
| **DallasTemperature.h** | Latest | DS18B20 temperature reading | Library Manager: "DallasTemperature" by Miles Burton |

### Arduino Code Structure

```cpp
// Required Libraries
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ============================================
// PIN DEFINITIONS
// ============================================
#define DHT_PIN 4              // DHT22 data pin
#define DS18B20_PIN 5          // DS18B20 data pin
#define FAN_ENA 14             // L298N ENA pin (PWM)
#define FAN_IN1 12             // L298N IN1 pin
#define FAN_IN2 13             // L298N IN2 pin
#define MIST_PIN 25            // Mist maker control pin

// ============================================
// SENSOR OBJECTS
// ============================================
DHT dht(DHT_PIN, DHT22);
OneWire oneWire(DS18B20_PIN);
DallasTemperature soilSensor(&oneWire);

// ============================================
// WIFI & API CONFIGURATION
// ============================================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://YOUR_SERVER_IP:5000/predict";

// ============================================
// TARGET VALUES (Optimal for Lavender)
// ============================================
float target_temp = 25.0;       // Target temperature in °C
float target_humidity = 60.0;   // Target humidity in %

// ============================================
// PREVIOUS STATE VARIABLES
// ============================================
float prev_fan_speed = 0.0;
int prev_humidifier_mode = 0;

// ============================================
// SETUP FUNCTION
// ============================================
void setup() {
    Serial.begin(115200);
    
    // Initialize sensors
    dht.begin();
    soilSensor.begin();
    
    // Initialize actuator pins
    pinMode(FAN_ENA, OUTPUT);
    pinMode(FAN_IN1, OUTPUT);
    pinMode(FAN_IN2, OUTPUT);
    pinMode(MIST_PIN, OUTPUT);
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
    // Read sensor data
    float air_temp = dht.readTemperature();
    float humidity = dht.readHumidity();
    soilSensor.requestTemperatures();
    float soil_temp = soilSensor.getTempCByIndex(0);
    
    // Send data to API and get predictions
    // ... (HTTP POST implementation)
    
    // Apply predictions to actuators
    // ... (PWM and digital signal control)
    
    delay(30000);  // Wait 30 seconds
}
```

### Data Flow Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ESP32 DATA FLOW PROCESS                             │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Read Sensors (Every 30 seconds)
────────────────────────────────────────
    DHT22 Sensor
    ├── dht.readTemperature() → air_temp (°C)
    └── dht.readHumidity() → humidity (%)
    
    DS18B20 Sensor
    └── soilSensor.getTempCByIndex(0) → soil_temp (°C)

Step 2: Prepare JSON Payload
────────────────────────────
    {
        "air_temp": 28.5,
        "humidity": 65.0,
        "soil_temp": 22.0,
        "target_temp": 25.0,
        "target_humidity": 60.0,
        "prev_fan_speed": 50.0,
        "prev_humidifier_mode": 1
    }

Step 3: Send HTTP POST Request
──────────────────────────────
    URL: http://SERVER_IP:5000/predict
    Method: POST
    Content-Type: application/json
    Body: JSON payload

Step 4: Receive Prediction Response
───────────────────────────────────
    {
        "fan_speed": 75.5,
        "humidifier_mode": 2
    }

Step 5: Apply Predictions to Actuators
──────────────────────────────────────
    Fan Control:
    ├── Convert fan_speed (0-100%) to PWM (0-255)
    ├── PWM value = fan_speed * 255 / 100
    └── analogWrite(FAN_ENA, PWM_value)
    
    Humidifier Control:
    └── Set mist maker mode based on humidifier_mode (0-3)
```

---

## 🤖 Machine Learning Models

### Overview

This system uses two machine learning models to predict optimal climate control settings:

| Model | Algorithm | Type | Purpose |
|-------|-----------|------|---------|
| **Fan Speed Model** | RandomForestRegressor | Regression | Predicts optimal fan speed (0-100%) |
| **Humidifier Model** | RandomForestClassifier | Classification | Predicts humidifier mode (0-3) |

---

### Model 1: Fan Speed Control (Regression)

#### Model Specifications

| Parameter | Value |
|-----------|-------|
| **Algorithm** | RandomForestRegressor |
| **Task Type** | Regression |
| **Output Range** | 0-100% (continuous value) |
| **Number of Trees** | 80 |
| **Max Depth** | 8 |
| **Min Samples Split** | 10 |
| **Min Samples Leaf** | 5 |
| **Random State** | 42 |

#### Input Features

| Feature | Data Type | Unit | Source | Description |
|---------|-----------|------|--------|-------------|
| `air_temp` | float | °C | DHT22 | Current air temperature |
| `humidity` | float | % | DHT22 | Current relative humidity |
| `soil_temp` | float | °C | DS18B20 | Current soil temperature |
| `target_temp` | float | °C | Config | Desired target temperature |
| `target_humidity` | float | % | Config | Desired target humidity |
| `prev_fan_speed` | float | % | State | Previous fan speed setting |
| `prev_humidifier_mode` | int | 0-3 | State | Previous humidifier mode |

#### Output

| Output | Data Type | Range | Description |
|--------|-----------|-------|-------------|
| `fan_speed` | float | 0-100% | Predicted optimal fan speed percentage |

#### How Fan Speed is Determined

```
Fan Speed Prediction Logic:
──────────────────────────

Base Speed = 40%

Temperature Influence:
├── temp_diff = air_temp - target_temp
└── adjustment = temp_diff × 6

Humidity Influence:
└── adjustment = (humidity - 60) × 0.2

Soil Temperature Influence:
└── adjustment = (soil_temp - 22) × 1.0

Final Fan Speed = Base Speed + All Adjustments
                = Clipped to range [0, 100]

Example:
├── air_temp = 28.5°C, target_temp = 25°C → temp_diff = 3.5
├── humidity = 65%
├── soil_temp = 24°C
│
├── Base: 40
├── Temp adjustment: 3.5 × 6 = 21
├── Humidity adjustment: (65-60) × 0.2 = 1
├── Soil adjustment: (24-22) × 1.0 = 2
│
└── Fan Speed = 40 + 21 + 1 + 2 = 64%
```

---

### Model 2: Humidifier Mode Control (Classification)

#### Model Specifications

| Parameter | Value |
|-----------|-------|
| **Algorithm** | RandomForestClassifier |
| **Task Type** | Multi-class Classification |
| **Number of Classes** | 4 |
| **Number of Trees** | 60 |
| **Max Depth** | 5 |
| **Min Samples Split** | 15 |
| **Min Samples Leaf** | 8 |
| **Random State** | 42 |

#### Input Features

Same as Fan Speed Model (7 features)

#### Output Classes

| Mode | Value | Mist Maker State | When Used |
|------|-------|------------------|-----------|
| **Off** | 0 | Disabled | Humidity is above target (humidity_diff < -10) |
| **Low** | 1 | Intermittent operation | Humidity slightly above target (-10 ≤ humidity_diff < 0) |
| **Medium** | 2 | Moderate mist output | Humidity slightly below target (0 ≤ humidity_diff < 10) |
| **High** | 3 | Continuous maximum output | Humidity significantly below target (humidity_diff ≥ 10) |

#### How Humidifier Mode is Determined

```
Humidifier Mode Classification Logic:
─────────────────────────────────────

humidity_diff = target_humidity - current_humidity

┌─────────────────────┬──────────────────┬─────────────────────────────┐
│   Condition         │  Mode            │  Description                │
├─────────────────────┼──────────────────┼─────────────────────────────┤
│ humidity_diff < -10 │  0 (Off)         │ Too humid, turn off mist    │
│ -10 ≤ diff < 0      │  1 (Low)         │ Slightly humid, low mist    │
│ 0 ≤ diff < 10       │  2 (Medium)      │ Slightly dry, medium mist   │
│ diff ≥ 10           │  3 (High)        │ Too dry, maximum mist       │
└─────────────────────┴──────────────────┴─────────────────────────────┘

Example:
├── target_humidity = 60%
├── current_humidity = 45%
├── humidity_diff = 60 - 45 = 15
│
└── Since diff (15) ≥ 10 → Mode = 3 (High)
```

---

## 📊 Dataset Description

### Dataset Overview

| Property | Value |
|----------|-------|
| **File Name** | greenhouse_ai_climate_dataset_1500.csv |
| **Total Records** | 1,500 samples |
| **Time Period** | Continuous greenhouse monitoring data |
| **Sampling Interval** | 5 minutes |

### Dataset Features

| Column | Data Type | Unit | Description |
|--------|-----------|------|-------------|
| `timestamp` | datetime | - | Date and time of recording |
| `air_temp` | float | °C | Air temperature reading |
| `humidity` | float | % | Relative humidity reading |
| `soil_temp` | float | °C | Soil temperature reading |
| `target_temp` | float | °C | Target temperature setting |
| `target_humidity` | float | % | Target humidity setting |
| `prev_fan_speed` | float | % | Previous fan speed |
| `prev_humidifier_mode` | int | 0-3 | Previous humidifier mode |
| `fan_speed` | float | % | Actual fan speed (target variable) |
| `humidifier_mode` | int | 0-3 | Actual humidifier mode (target variable) |

### Sample Data

```
timestamp,air_temp,humidity,soil_temp,target_temp,target_humidity,prev_fan_speed,prev_humidifier_mode,fan_speed,humidifier_mode
2024-09-27 12:58:10,26.96,89.67,24.08,24,65,30.0,1.0,70,0
2024-09-27 13:03:10,25.67,93.78,22.87,24,65,70.0,0.0,50,0
2024-09-27 13:08:10,26.28,93.94,24.40,24,65,50.0,0.0,70,0
2024-09-27 13:13:10,25.00,99.33,22.93,24,65,70.0,0.0,50,0
2024-09-27 13:18:10,25.76,98.27,23.57,24,65,50.0,0.0,50,0
```

### Data Statistics

| Feature | Min | Max | Mean | Std Dev |
|---------|-----|-----|------|---------|
| air_temp | 22.0 | 32.0 | 26.5 | 2.1 |
| humidity | 40.0 | 99.0 | 70.0 | 15.0 |
| soil_temp | 18.0 | 28.0 | 23.5 | 1.8 |
| fan_speed | 0.0 | 100.0 | 55.0 | 20.0 |
| humidifier_mode | 0 | 3 | 1.5 | 1.0 |

---

## 🔄 Data Preprocessing

### Preprocessing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA PREPROCESSING PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Load Raw Data
─────────────────────
    df = pd.read_csv('greenhouse_ai_climate_dataset_1500.csv')

Step 2: Remove Unnecessary Columns
──────────────────────────────────
    df = df.drop(columns=['timestamp'])

Step 3: Feature Selection
─────────────────────────
    Features (X):
    ├── air_temp
    ├── humidity
    ├── soil_temp
    ├── target_temp
    ├── target_humidity
    ├── prev_fan_speed
    └── prev_humidifier_mode

    Targets (y):
    ├── fan_speed (for regression)
    └── humidifier_mode (for classification)

Step 4: Train-Test Split
────────────────────────
    ┌────────────────────────────────────────────┐
    │  Training Data: 75%  │  Testing Data: 25%  │
    │     (1125 samples)   │    (375 samples)    │
    └────────────────────────────────────────────┘
    
    random_state = 101 (for reproducibility)
    shuffle = True

Step 5: Feature Scaling (StandardScaler)
────────────────────────────────────────
    Formula: z = (x - μ) / σ
    
    Where:
    ├── x = original value
    ├── μ = mean of feature
    ├── σ = standard deviation of feature
    └── z = scaled value

    Result: All features normalized to mean=0, std=1

Step 6: Save Scaler
───────────────────
    joblib.dump(scaler, 'models/scaler.pkl')
```

### Preprocessing Methods

| Step | Method | Purpose |
|------|--------|---------|
| **Data Loading** | pandas.read_csv() | Load CSV dataset |
| **Column Removal** | df.drop() | Remove timestamp column |
| **Train-Test Split** | train_test_split(test_size=0.25) | 75% train, 25% test |
| **Feature Scaling** | StandardScaler | Normalize features to zero mean, unit variance |
| **Cross-Validation** | 5-Fold CV | Validate model performance |

---

## 📈 Model Performance and Accuracy

### Fan Speed Model (Regression) Performance

| Metric | Value | Description |
|--------|-------|-------------|
| **R² Score** | **~81%** | Model explains 81% of variance in fan speed |
| **MAE** | Low | Mean Absolute Error - average prediction error |
| **RMSE** | Low | Root Mean Square Error - penalizes larger errors |
| **Cross-Val R² Mean** | ~80% | Average R² across 5 folds |

#### Regression Metrics Explanation

```
R² Score (Coefficient of Determination): ~81%
───────────────────────────────────────────────
    ┌────────────────────────────────────────────────────────────────┐
    │  R² = 1 - (SS_residual / SS_total)                             │
    │                                                                 │
    │  Interpretation:                                                │
    │  ├── R² = 1.0  → Perfect prediction                            │
    │  ├── R² = 0.81 → 81% of variance explained ← OUR MODEL         │
    │  └── R² = 0.0  → Model no better than mean                     │
    └────────────────────────────────────────────────────────────────┘

MAE (Mean Absolute Error):
──────────────────────────
    MAE = (1/n) × Σ|actual - predicted|
    
    Lower is better. Represents average absolute difference
    between predicted and actual fan speeds.

RMSE (Root Mean Square Error):
──────────────────────────────
    RMSE = √[(1/n) × Σ(actual - predicted)²]
    
    Lower is better. Penalizes larger errors more heavily.
```

---

### Humidifier Model (Classification) Performance

| Metric | Value | Description |
|--------|-------|-------------|
| **Accuracy** | **~79%** | Overall correct predictions |
| **Precision** | High | Low false positive rate per class |
| **Recall** | High | Low false negative rate per class |
| **F1-Score** | Balanced | Harmonic mean of precision and recall |
| **Cross-Val Accuracy Mean** | ~78% | Average accuracy across 5 folds |

#### Confusion Matrix

```
                    Predicted Class
                   ┌─────┬─────┬─────┬─────┐
                   │  0  │  1  │  2  │  3  │
         ┌─────────┼─────┼─────┼─────┼─────┤
         │    0    │ ██  │  ░  │  ░  │  ░  │
Actual   │    1    │  ░  │ ██  │  ░  │  ░  │
Class    │    2    │  ░  │  ░  │ ██  │  ░  │
         │    3    │  ░  │  ░  │  ░  │ ██  │
         └─────────┴─────┴─────┴─────┴─────┘
         
██ = High correct predictions (diagonal)
░  = Low misclassifications (off-diagonal)

Model correctly classifies humidifier modes with ~79% accuracy
Balanced performance across all 4 classes
```

#### Classification Metrics Explanation

```
Accuracy: ~79%
──────────────
    Accuracy = (TP + TN) / Total
    
    79% of all predictions are correct.

Precision (per class):
──────────────────────
    Precision = TP / (TP + FP)
    
    Of all predictions for a class, how many are correct?

Recall (per class):
───────────────────
    Recall = TP / (TP + FN)
    
    Of all actual instances of a class, how many were found?

F1-Score (per class):
─────────────────────
    F1 = 2 × (Precision × Recall) / (Precision + Recall)
    
    Harmonic mean of precision and recall.
```

---

### Model Comparison Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODEL PERFORMANCE SUMMARY                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FAN SPEED MODEL (Regression)                                            │
│  ═══════════════════════════                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  R² Score:        ████████████████████░░░░░  81%                │    │
│  │  Cross-Val R²:    ████████████████████░░░░░  80%                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  HUMIDIFIER MODEL (Classification)                                       │
│  ═════════════════════════════════                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Accuracy:        ███████████████████░░░░░░  79%                │    │
│  │  Cross-Val Acc:   ██████████████████░░░░░░░  78%                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Documentation

### Server Configuration

| Property | Value |
|----------|-------|
| **Host** | 0.0.0.0 (all interfaces) |
| **Port** | 5000 |
| **Framework** | Flask |
| **Base URL** | http://SERVER_IP:5000 |

### Endpoints

#### POST `/predict`

Predicts optimal fan speed and humidifier mode based on sensor data.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "air_temp": 28.5,
    "humidity": 65.0,
    "soil_temp": 22.0,
    "target_temp": 25.0,
    "target_humidity": 60.0,
    "prev_fan_speed": 50.0,
    "prev_humidifier_mode": 1
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `air_temp` | float | Yes | Current air temperature (°C) |
| `humidity` | float | Yes | Current relative humidity (%) |
| `soil_temp` | float | Yes | Current soil temperature (°C) |
| `target_temp` | float | Yes | Target temperature (°C) |
| `target_humidity` | float | Yes | Target humidity (%) |
| `prev_fan_speed` | float | Yes | Previous fan speed setting (%) |
| `prev_humidifier_mode` | int | Yes | Previous humidifier mode (0-3) |

**Success Response (200 OK):**
```json
{
    "fan_speed": 75.5,
    "humidifier_mode": 2
}
```

**Response Parameters:**

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `fan_speed` | float | 0-100 | Predicted fan speed percentage |
| `humidifier_mode` | int | 0-3 | Predicted humidifier mode |

**Error Response (400 Bad Request):**
```json
{
    "error": "Missing required fields",
    "missing": ["soil_temp", "target_humidity"]
}
```

**Error Response (500 Internal Server Error):**
```json
{
    "error": "Model prediction failed",
    "details": "Error message"
}
```

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful prediction |
| 400 | Bad Request | Invalid or missing input data |
| 500 | Internal Server Error | Model or server error |

---

## 🛠️ Technologies Used

### Software Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.x | Core programming language |
| **scikit-learn** | Latest | Machine learning library (RandomForest) |
| **pandas** | Latest | Data manipulation and analysis |
| **NumPy** | Latest | Numerical computing |
| **Flask** | Latest | REST API server framework |
| **joblib** | Latest | Model serialization (.pkl files) |
| **Arduino IDE** | Latest | ESP32 programming environment |
| **C++** | - | ESP32 firmware language |

### Python Dependencies

```
flask
scikit-learn
pandas
numpy
joblib
```

### Arduino Libraries

| Library | Author | Purpose |
|---------|--------|---------|
| WiFi.h | Espressif | ESP32 WiFi connectivity |
| HTTPClient.h | Espressif | HTTP requests |
| DHT.h | Adafruit | DHT22 sensor |
| OneWire.h | Paul Stoffregen | OneWire protocol |
| DallasTemperature.h | Miles Burton | DS18B20 sensor |

---

## 📁 Project Structure

```
IT22894588_ClimateControl/
│
├── README.md                           # This documentation file
├── requirements.txt                    # Python dependencies
│
├── DataSet/
│   └── greenhouse_ai_climate_dataset_1500.csv    # Training dataset (1500 samples)
│
├── models/
│   ├── fan_model.pkl                   # Trained RandomForestRegressor model
│   ├── humidifier_model.pkl            # Trained RandomForestClassifier model
│   └── scaler.pkl                      # StandardScaler for feature normalization
│
├── src/
│   ├── app.py                          # Flask API application (main server)
│   ├── server.py                       # Server runner script
│   ├── train.py                        # Combined model training script
│   ├── train_fan_model.py              # Fan model training (separate)
│   ├── train_humidifier_model.py       # Humidifier model training (separate)
│   ├── predict.py                      # Prediction utilities
│   ├── evaluate.py                     # Model evaluation metrics
│   ├── check_model_accuracy.py         # Accuracy verification script
│   ├── data_loader.py                  # Dataset loading utilities
│   ├── preprocess.py                   # Data preprocessing functions
│   └── test_api.py                     # API testing script
│
└── esp32/
    └── climate_control.ino             # ESP32 Arduino firmware
```

### File Descriptions

| File | Description |
|------|-------------|
| `app.py` | Main Flask API server with /predict endpoint |
| `server.py` | Script to start the Flask server |
| `train.py` | Trains both fan and humidifier models |
| `train_fan_model.py` | Trains only the fan speed model |
| `train_humidifier_model.py` | Trains only the humidifier model |
| `predict.py` | Utility functions for making predictions |
| `evaluate.py` | Model evaluation and metrics calculation |
| `check_model_accuracy.py` | Validates model accuracy with test data |
| `data_loader.py` | Functions to load and parse dataset |
| `preprocess.py` | Data preprocessing and scaling functions |
| `test_api.py` | Test script for API endpoints |

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.x installed
- pip package manager
- Arduino IDE with ESP32 board support
- Required Arduino libraries installed

### Step 1: Clone the Repository

```bash
git clone https://github.com/kulindupr/SmartFarming-Lavender-AI.git
cd IT22894588_ClimateControl
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Train Models (Optional)

Pre-trained models are included. To retrain:

```bash
python src/train.py
```

Or train individual models:

```bash
python src/train_fan_model.py
python src/train_humidifier_model.py
```

### Step 5: Check Model Accuracy

```bash
python src/check_model_accuracy.py
```

### Step 6: Run the API Server

```bash
python src/server.py
```

Server will start at `http://0.0.0.0:5000`

### Step 7: Test the API

```bash
python src/test_api.py
```

### Step 8: Arduino Setup

1. **Install Arduino IDE**
   - Download from: https://www.arduino.cc/en/software

2. **Add ESP32 Board Support**
   - Go to: File → Preferences
   - Add to "Additional Boards Manager URLs":
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Go to: Tools → Board → Boards Manager
   - Search "ESP32" and install

3. **Install Required Libraries**
   - Go to: Sketch → Include Library → Manage Libraries
   - Install:
     - "DHT sensor library" by Adafruit
     - "OneWire" by Paul Stoffregen
     - "DallasTemperature" by Miles Burton

4. **Upload Code to ESP32**
   - Open the ESP32 Arduino code
   - Update WiFi credentials:
     ```cpp
     const char* ssid = "YOUR_WIFI_SSID";
     const char* password = "YOUR_WIFI_PASSWORD";
     ```
   - Update server IP:
     ```cpp
     const char* serverURL = "http://YOUR_SERVER_IP:5000/predict";
     ```
   - Select Board: Tools → Board → ESP32 Dev Module
   - Select Port: Tools → Port → (your COM port)
   - Click Upload

---

## 🚀 Usage

### Starting the System

1. **Start the Flask API Server**
   ```bash
   cd IT22894588_ClimateControl
   python src/server.py
   ```

2. **Power on ESP32 and Sensors**
   - Connect 12V power supply
   - Ensure all sensors are connected properly

3. **Monitor System Operation**
   - ESP32 automatically:
     - Reads DHT22 (air temp, humidity) every 30 seconds
     - Reads DS18B20 (soil temp) every 30 seconds
     - Sends data to Flask API via HTTP POST
     - Receives ML predictions
     - Adjusts fan speed via L298N PWM
     - Controls mist maker mode

### Testing the API Manually

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "air_temp": 28.5,
    "humidity": 65.0,
    "soil_temp": 22.0,
    "target_temp": 25.0,
    "target_humidity": 60.0,
    "prev_fan_speed": 50.0,
    "prev_humidifier_mode": 1
  }'
```

Expected Response:
```json
{
    "fan_speed": 75.5,
    "humidifier_mode": 2
}
```

---

## 👥 Contributors

| Name | Student ID | Role | Component |
|------|------------|------|-----------|
| kulindupr | IT22894588 | Developer | Intelligent Climate Control |

---

## 📄 License

This project is part of the SmartFarming-Lavender-AI final-year research project.

---

## 🌡️ Intelligent Climate Control - Optimizing Greenhouse Conditions with AI 🌿

