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
| **Manual Override** | Supports off / manual / auto modes for each actuator |
| **Energy Efficiency** | Optimize device operation to reduce power consumption |
| **Data-Driven Decisions** | Use ML models to predict optimal device settings |

### What This System Controls

| Device | Control Type | Purpose |
|--------|--------------|---------|
| **12V DC Fan** | PWM Speed Control (0-100%) | Air circulation and temperature reduction |
| **Ultrasonic Mist Maker** | Mode Selection (Off/Low/Medium/High) | Humidity adjustment |

### Control Modes

Each actuator supports three operating modes:

| Mode | Fan Behavior | Humidifier Behavior |
|------|-------------|---------------------|
| **auto** | ML model controls fan speed | ML model controls humidifier level |
| **manual** | User-set speed applied when manual_on=true | User-set level (0-3) applied directly |
| **off** | Fan forced off (0%) | Humidifier forced off (level 0) |

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
│  Air Temp       │       │  Soil Temp      │       │   Parameters    │
│  Humidity       │       │  (Waterproof)   │       │  Target Temp    │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ESP32 MICROCONTROLLER                             │
│  Reads DHT22 + DS18B20, packages JSON, sends HTTP POST to Flask API     │
│  Receives ML predictions + effective control values                      │
│  Controls fan via L298N PWM and mist maker via GPIO 25                 │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ WiFi (HTTP POST/Response)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLASK API SERVER  v3.1.0                              │
│  POST /predict          - ML inference + effective control resolution   │
│  POST /fan/mode         - Set fan mode (off/manual/auto)                │
│  POST /fan/manual       - Set manual fan speed and on/off               │
│  GET  /fan/state        - Read fan control state                        │
│  POST /humidifier/mode  - Set humidifier mode                           │
│  POST /humidifier/manual- Set manual humidifier level                   │
│  GET  /humidifier/state - Read humidifier control state                 │
│  GET  /sensors          - Latest sensor readings                        │
│  GET  /health           - Health check                                  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Effective Predictions
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           ACTUATOR LAYER                                 │
│  L298N + 12V DC Fan (PWM 0-100%)    Ultrasonic Mist Maker (0-3 modes)  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### Step-by-Step Process Flow

**STEP 1: Sensor Data Collection (every 30 seconds)**
- DHT22 → air_temp (°C) and humidity (%)
- DS18B20 → soil_temp (°C)

**STEP 2: Data Transmission — HTTP POST to `/predict`**
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

**STEP 3: ML Model Inference**
1. StandardScaler normalizes the 7 input features
2. RandomForestRegressor predicts fan_speed (e.g., 75.5%)
3. RandomForestClassifier predicts humidifier_mode, clamped to [0,3] via `np.clip`

**STEP 4: Effective Value Resolution (mode-aware)**

| Mode | Fan | Humidifier |
|------|-----|------------|
| auto | AI prediction | AI prediction |
| manual | manual_speed (if manual_on=true) | manual_level |
| off | 0 | 0 |

**STEP 5: Full JSON Response — Arduino reads the `effective_*` fields**
```json
{
    "fan_speed": 75.5,
    "effective_fan_speed": 75.5,
    "fan_mode": "auto",
    "humidifier_mode": 2,
    "effective_humidifier_level": 2,
    "humidifier_control_mode": "auto",
    "air_temp": 28.5,
    "humidity": 65.0,
    "soil_temp": 22.0
}
```

**STEP 6: Actuator Control**
- Fan: `analogWrite(FAN_ENA, effective_fan_speed * 255 / 100)`
- Humidifier: GPIO 25 signal sets mist maker mode (0=off, 1=low, 2=medium, 3=high)

---

## 🔧 Hardware Components

### Complete Hardware List

| Component | Model/Specification | Qty | Purpose |
|-----------|---------------------|-----|---------|
| **ESP32** | ESP32 DevKit V1 | 1 | WiFi microcontroller, data collection, device control |
| **DHT22** | AM2302 | 1 | Air temperature (±0.5°C) and humidity (±2% RH) |
| **DS18B20** | Waterproof Digital Temp Sensor | 1 | Soil temperature measurement |
| **L298N** | Dual H-Bridge Motor Driver | 1 | PWM fan speed control |
| **Ultrasonic Mist Maker** | Ceramic Disc Module | 1 | Greenhouse humidity control |
| **12V DC Fan** | Brushless Cooling Fan | 1 | Air circulation, temperature control |
| **Power Supply** | 12V DC Adapter | 1 | Powers fan and motor driver |
| **Jumper Wires** | M-M, M-F | Multiple | Circuit connections |
| **4.7kΩ Resistor** | Pull-up Resistor | 1 | DS18B20 data line pull-up |

### Sensor and Driver Specifications

#### ESP32 DevKit V1
| Specification | Value |
|---------------|-------|
| Core | Xtensa dual-core 32-bit LX6 |
| Clock | 240 MHz |
| WiFi | 802.11 b/g/n |
| GPIO | 34 pins |
| Voltage | 3.3V operating, 5V via USB |

#### DHT22 (AM2302)
| Specification | Value |
|---------------|-------|
| Temperature range | -40°C to 80°C (±0.5°C) |
| Humidity range | 0-100% RH (±2% RH) |
| Sampling rate | 0.5 Hz |
| Operating voltage | 3.3V - 5V |

#### DS18B20 Waterproof
| Specification | Value |
|---------------|-------|
| Temperature range | -55°C to +125°C (±0.5°C) |
| Protocol | OneWire |
| Resolution | 9-12 bit configurable |
| Operating voltage | 3.0V - 5.5V |

#### L298N Motor Driver
| Specification | Value |
|---------------|-------|
| Type | Dual H-Bridge |
| Motor voltage | 5V - 35V |
| Max current | 2A per channel |
| PWM support | Yes (ENA, IN1, IN2) |

#### Ultrasonic Mist Maker
| Specification | Value |
|---------------|-------|
| Type | Ceramic Disc Humidifier |
| Modes | 4 (Off / Low / Medium / High) |
| Operating voltage | 12V DC |

#### 12V DC Fan
| Specification | Value |
|---------------|-------|
| Type | Brushless DC |
| Speed control | PWM 0-100% |
| Operating voltage | 12V DC |

---

## 🔌 Hardware Wiring Diagram

### ESP32 Pin Assignments

| ESP32 Pin | Connected To | Purpose |
|-----------|-------------|---------|
| GPIO 4 | DHT22 Data | Air temperature + humidity |
| GPIO 5 | DS18B20 Data + 4.7kΩ pull-up | Soil temperature (OneWire) |
| GPIO 12 | L298N IN1 | Fan direction control |
| GPIO 13 | L298N IN2 | Fan direction control |
| GPIO 14 | L298N ENA | Fan PWM speed |
| GPIO 25 | Mist Maker Control | Humidifier mode signal |
| 3.3V | DHT22 VCC, DS18B20 VCC | Sensor power |
| GND | Common ground | All GND rails |

### Wiring Notes

- DS18B20 requires a 4.7kΩ pull-up resistor between DATA and VCC.
- L298N powered directly from 12V supply; fan connected to L298N OUT1/OUT2.
- All grounds tied together (ESP32 GND, L298N GND, mist maker GND).

### Wiring Schematic

```
12V Supply ─────────── L298N (12V, GND)
              └──────── 12V DC Fan (via OUT1/OUT2)

ESP32 GPIO 14 ────────── L298N ENA (PWM)
ESP32 GPIO 12 ────────── L298N IN1
ESP32 GPIO 13 ────────── L298N IN2

ESP32 GPIO 4  ────────── DHT22 DATA
ESP32 3.3V    ────────── DHT22 VCC
ESP32 GND     ────────── DHT22 GND

ESP32 GPIO 5  ────────── DS18B20 DATA ──[4.7kΩ]── 3.3V
ESP32 3.3V    ────────── DS18B20 VCC
ESP32 GND     ────────── DS18B20 GND

ESP32 GPIO 25 ────────── Mist Maker Control
12V Supply GND ───────── Mist Maker GND
```

---

## 📟 Arduino Integration

### Required Libraries

| Library | Author | Installation |
|---------|--------|-------------|
| WiFi.h | Espressif | Included with ESP32 board package |
| HTTPClient.h | Espressif | Included with ESP32 board package |
| DHT.h | Adafruit | Library Manager: "DHT sensor library" |
| OneWire.h | Paul Stoffregen | Library Manager: "OneWire" |
| DallasTemperature.h | Miles Burton | Library Manager: "DallasTemperature" |

### Arduino Firmware Structure

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define DHT_PIN     4
#define DS18B20_PIN 5
#define FAN_ENA    14
#define FAN_IN1    12
#define FAN_IN2    13
#define MIST_PIN   25

DHT dht(DHT_PIN, DHT22);
OneWire oneWire(DS18B20_PIN);
DallasTemperature soilSensor(&oneWire);

const char* ssid      = "YOUR_WIFI_SSID";
const char* password  = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://YOUR_SERVER_IP:5000/predict";

float target_temp     = 25.0;
float target_humidity = 60.0;
float prev_fan_speed  = 0.0;
int   prev_hum_mode   = 0;

void setup() {
    Serial.begin(115200);
    dht.begin();
    soilSensor.begin();
    pinMode(FAN_ENA, OUTPUT);
    pinMode(FAN_IN1, OUTPUT);
    pinMode(FAN_IN2, OUTPUT);
    pinMode(MIST_PIN, OUTPUT);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(1000); }
}

void loop() {
    float air_temp  = dht.readTemperature();
    float humidity  = dht.readHumidity();
    soilSensor.requestTemperatures();
    float soil_temp = soilSensor.getTempCByIndex(0);
    // POST to /predict
    // Use effective_fan_speed: analogWrite(FAN_ENA, effective * 255 / 100)
    // Use effective_humidifier_level: set mist maker mode 0-3
    delay(30000);
}
```

### Arduino Response Field Usage

| Field | Usage |
|-------|-------|
| `effective_fan_speed` | `analogWrite(FAN_ENA, effective_fan_speed * 255 / 100)` |
| `effective_humidifier_level` | Sets mist maker mode via GPIO 25 (0=off, 1=low, 2=med, 3=high) |

---

## 🤖 Machine Learning Models

### Model 1: Fan Speed Control (Regression)

#### Specifications

| Parameter | Value |
|-----------|-------|
| Algorithm | RandomForestRegressor |
| Task | Regression |
| Output | 0-100% (continuous) |
| n_estimators | 100 |
| max_depth | None (unlimited) |
| min_samples_split | 2 |
| min_samples_leaf | 1 |
| n_jobs | -1 (all CPU cores) |
| random_state | 42 |

#### Input Features (7 total)

| # | Feature | Unit | Source |
|---|---------|------|--------|
| 1 | `air_temp` | °C | DHT22 |
| 2 | `humidity` | % | DHT22 |
| 3 | `soil_temp` | °C | DS18B20 |
| 4 | `target_temp` | °C | Config |
| 5 | `target_humidity` | % | Config |
| 6 | `prev_fan_speed` | % | State |
| 7 | `prev_humidifier_mode` | 0-3 | State |

#### Fan Speed Labels (Dataset Generation)

```
temp_excess = air_temp - 24.0 (target temperature)

Condition              Fan Speed
temp_excess > 4    ->  90%
temp_excess > 2    ->  70%
temp_excess > 0    ->  50%
else               ->  30%

Example: air_temp=28.5, target=24.0, excess=4.5  ->  90%
```

---

### Model 2: Humidifier Mode Control (Classification)

#### Specifications

| Parameter | Value |
|-----------|-------|
| Algorithm | RandomForestClassifier |
| Task | Multi-class (4 classes) |
| n_estimators | 200 |
| max_depth | 10 |
| min_samples_split | 2 |
| min_samples_leaf | 2 |
| class_weight | balanced |
| n_jobs | -1 (all CPU cores) |
| random_state | 42 |

#### Output Classes

| Mode | Value | Condition |
|------|-------|-----------|
| Off | 0 | humidity_deficit <= 2 |
| Low | 1 | 2 < deficit <= 7 |
| Medium | 2 | 7 < deficit <= 15 |
| High | 3 | deficit > 15 |

Where `humidity_deficit = target_humidity (65%) - current_humidity`

#### Humidifier Labels (Dataset Generation)

```
humidity_deficit = 65.0 - current_humidity

deficit > 15    ->  Mode 3 (High)     [humidity < 50%]
deficit > 7     ->  Mode 2 (Medium)   [50% <= humidity < 58%]
deficit > 2     ->  Mode 1 (Low)      [58% <= humidity < 63%]
else            ->  Mode 0 (Off)      [humidity >= 63%]

Example: humidity=45%, deficit=20  ->  Mode 3 (High)
```

#### Prediction Normalization

```python
effective_humidifier_level = int(np.clip(raw_prediction, 0, 3))
```

---

## 📊 Dataset Description

### Overview

| Property | Value |
|----------|-------|
| File | greenhouse_ai_climate_dataset_1500.csv |
| Total records | 1,500 |
| Start timestamp | 2024-09-27 12:58:10 |
| Sampling interval | 5 minutes |
| Random seed | 42 |
| target_temp | 24.0°C (constant) |
| target_humidity | 65.0% (constant) |

### Column Definitions

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `timestamp` | datetime | - | Recording time |
| `air_temp` | float | °C | Normal(26.4, 2.5), clipped [18, 35] |
| `humidity` | float | % | Stratified across [35, 100] |
| `soil_temp` | float | °C | air_temp − uniform(0.5, 3.0) |
| `target_temp` | float | °C | Constant 24.0 |
| `target_humidity` | float | % | Constant 65.0 |
| `prev_fan_speed` | float | % | Lag-1 fan speed; first value = 50.0 |
| `prev_humidifier_mode` | int | 0-3 | Lag-1 mode; first value = 0 |
| `fan_speed` | float | % | Regression target label |
| `humidifier_mode` | int | 0-3 | Classification target label |

### Humidity Stratification (for class balance)

| Humidity Range | Samples | Humidifier Mode |
|---------------|---------|-----------------|
| [35, 50) | 300 | 3 — High |
| [50, 58) | 250 | 2 — Medium |
| [58, 63) | 250 | 1 — Low |
| [63, 100) | 700 | 0 — Off |
| **Total** | **1500** | |

### Sample Data

```
timestamp,air_temp,humidity,soil_temp,target_temp,target_humidity,prev_fan_speed,prev_humidifier_mode,fan_speed,humidifier_mode
2024-09-27 12:58:10,26.96,89.67,24.08,24,65,30.0,1.0,70,0
2024-09-27 13:03:10,25.67,93.78,22.87,24,65,70.0,0.0,50,0
2024-09-27 13:08:10,26.28,93.94,24.40,24,65,50.0,0.0,70,0
2024-09-27 13:13:10,25.00,99.33,22.93,24,65,70.0,0.0,50,0
2024-09-27 13:18:10,25.76,98.27,23.57,24,65,50.0,0.0,50,0
```

---

## 🔄 Data Preprocessing

### Pipeline

1. **Load** — `pd.read_csv('greenhouse_ai_climate_dataset_1500.csv')`
2. **Drop** — Remove `timestamp` column
3. **Split** — X (7 features), y_fan (regression), y_humid (classification)
4. **Train-Test Split** — 80% train (1200 samples) / 20% test (300 samples); `test_size=0.2, random_state=42`
5. **Scale** — `StandardScaler` fitted on X_train only; transform applied to both X_train and X_test
6. **Save scaler** — `joblib.dump(scaler, 'models/scaler.pkl')`

### Method Summary

| Step | Method | Detail |
|------|--------|--------|
| Load | `pandas.read_csv()` | Read CSV |
| Drop | `df.drop(columns=['timestamp'])` | Remove timestamp |
| Split | `train_test_split(test_size=0.2, random_state=42)` | 80/20 |
| Scale | `StandardScaler` | z = (x − μ) / σ; fitted on training data only |
| Persist | `joblib.dump()` | Saved to models/scaler.pkl |

---

## 📈 Model Performance and Accuracy

### Fan Speed Model (RandomForestRegressor — 100 trees)

| Metric | Value |
|--------|-------|
| **R² Score** | ~81% |
| **MAE** | Low |
| **RMSE** | Low |

**R² = 1 − (SS_residual / SS_total)**: value of 0.81 means the model explains 81% of the variance in fan speed.

### Humidifier Model (RandomForestClassifier — 200 trees, balanced)

| Metric | Value |
|--------|-------|
| **Accuracy** | ~79% |
| **Precision** | Weighted (per-class) |
| **Recall** | Weighted (per-class) |
| **F1-Score** | Weighted harmonic mean |

### Performance Summary

```
FAN SPEED MODEL      (RandomForestRegressor,  100 trees,  depth=unlimited)
  R2 Score:  |||||||||||||||||||||....  81%

HUMIDIFIER MODEL     (RandomForestClassifier, 200 trees,  depth=10, balanced)
  Accuracy:  ||||||||||||||||||||.....  79%
```

---

## 🔌 API Documentation

### Server Configuration

| Property | Value |
|----------|-------|
| Version | 3.1.0 |
| Host | 0.0.0.0 (all interfaces) |
| Port | 5000 |
| Framework | Flask + Flask-CORS |
| Base URL | http://SERVER_IP:5000 |

---

### GET `/`

Returns service info and all available endpoints.

**Response (200):**
```json
{
  "service": "Greenhouse Climate Control API",
  "version": "3.1.0",
  "endpoints": {
    "POST /predict":            "Predict fan speed + humidifier level",
    "POST /fan/mode":           "Set fan mode: off | manual | auto",
    "POST /fan/manual":         "Set manual fan on/off + speed (1-100)",
    "GET  /fan/state":          "Get fan control state",
    "POST /humidifier/mode":    "Set humidifier mode: off | manual | auto",
    "POST /humidifier/manual":  "Set manual level: 0=off 1=low 2=med 3=high",
    "GET  /humidifier/state":   "Get humidifier control state",
    "GET  /sensors":            "Latest sensor readings",
    "GET  /health":             "Health check"
  }
}
```

---

### GET `/health`

**Response (200):**
```json
{ "status": "healthy", "models_loaded": true }
```

---

### GET `/sensors`

Returns the latest sensor readings cached from the most recent `/predict` call.

**Response (200):**
```json
{ "air_temp": 28.5, "humidity": 65.0, "soil_temp": 22.0, "timestamp": "2024-09-27T12:58:10+00:00" }
```

---

### POST `/predict`

Main endpoint called by the ESP32 every cycle. Runs ML inference and resolves effective control values based on current operating modes.

**Request body:**
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

All 7 fields are required. Missing fields return HTTP 400 with a `missing` array.

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `air_temp` | float | Yes | Current air temperature (°C) |
| `humidity` | float | Yes | Current relative humidity (%) |
| `soil_temp` | float | Yes | Current soil temperature (°C) |
| `target_temp` | float | Yes | Desired target temperature (°C) |
| `target_humidity` | float | Yes | Desired target humidity (%) |
| `prev_fan_speed` | float | Yes | Previous fan speed (%) |
| `prev_humidifier_mode` | int | Yes | Previous humidifier mode (0-3) |

**Success Response (200):**
```json
{
  "fan_speed": 75.5,
  "effective_fan_speed": 75.5,
  "fan_mode": "auto",
  "humidifier_mode": 2,
  "effective_humidifier_level": 2,
  "humidifier_control_mode": "auto",
  "air_temp": 28.5,
  "humidity": 65.0,
  "soil_temp": 22.0
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `fan_speed` | float | Raw AI-predicted fan speed (0-100%) |
| `effective_fan_speed` | float | **Actual speed Arduino applies** (mode-resolved) |
| `fan_mode` | string | Current fan mode: off / manual / auto |
| `humidifier_mode` | int | Raw AI-predicted humidifier level (0-3) |
| `effective_humidifier_level` | int | **Actual level Arduino applies** (mode-resolved) |
| `humidifier_control_mode` | string | Current humidifier mode: off / manual / auto |
| `air_temp` / `humidity` / `soil_temp` | float | Echoed sensor values |

**Error (400):**
```json
{ "error": "Missing required fields", "missing": ["soil_temp"] }
```

**Error (500):**
```json
{ "error": "Prediction failed: <details>" }
```

---

### POST `/fan/mode`

Set fan operating mode.

**Request:** `{ "mode": "auto" }` — valid: `"off"` / `"manual"` / `"auto"`

**Response (200):**
```json
{ "success": true, "fan_control": { "mode": "auto", "manual_speed": 0, "manual_on": false } }
```

---

### POST `/fan/manual`

Set manual fan parameters (effective when mode is `"manual"`).

**Request:** `{ "on": true, "speed": 60 }` — speed range: 1-100

**Response (200):**
```json
{ "success": true, "fan_control": { "mode": "manual", "manual_speed": 60, "manual_on": true } }
```

---

### GET `/fan/state`

**Response (200):**
```json
{ "mode": "auto", "manual_speed": 0, "manual_on": false }
```

---

### POST `/humidifier/mode`

Set humidifier operating mode.

**Request:** `{ "mode": "auto" }` — valid: `"off"` / `"manual"` / `"auto"`

**Response (200):**
```json
{ "success": true, "humidifier_control": { "mode": "auto", "manual_level": 0 } }
```

---

### POST `/humidifier/manual`

Set manual humidifier level (effective when mode is `"manual"`).

**Request:** `{ "level": 2 }` — valid: 0 (off), 1 (low), 2 (medium), 3 (high)

**Response (200):**
```json
{ "success": true, "humidifier_control": { "mode": "manual", "manual_level": 2 } }
```

---

### GET `/humidifier/state`

**Response (200):**
```json
{ "mode": "auto", "manual_level": 0 }
```

---

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful operation |
| 400 | Bad Request | Missing or invalid input fields |
| 500 | Internal Server Error | Model prediction or server failure |

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.x | Core language |
| scikit-learn | RandomForest models |
| pandas | CSV loading and data manipulation |
| NumPy | Numerical arrays, np.clip for normalization |
| Flask | REST API framework |
| Flask-CORS | Cross-Origin Resource Sharing |
| joblib | Model and scaler serialization (.pkl) |
| Arduino IDE | ESP32 firmware development |
| C++ | ESP32 firmware language |

### Python Dependencies (requirements.txt)

```
flask
flask-cors
scikit-learn
pandas
numpy
joblib
```

### Arduino Libraries

| Library | Author | Purpose |
|---------|--------|---------|
| WiFi.h | Espressif | ESP32 WiFi |
| HTTPClient.h | Espressif | HTTP POST requests |
| DHT.h | Adafruit | DHT22 sensor |
| OneWire.h | Paul Stoffregen | OneWire protocol |
| DallasTemperature.h | Miles Burton | DS18B20 sensor |

---

## 📁 Project Structure

```
IT22894588_ClimateControl/
├── Rubasinghe-K.P_Climate-Control-System.md   # This documentation
├── requirements.txt                            # Python dependencies
├── ApiDetail.tt                                # API detail notes
├── quick_test.py                               # Quick end-to-end test
├── regenerate_dataset.py                       # Stratified dataset regeneration (seed=42)
├── DataSet/
│   └── greenhouse_ai_climate_dataset_1500.csv  # 1500-sample training dataset
├── models/
│   ├── fan_model.pkl                           # Trained RandomForestRegressor
│   ├── humidifier_model.pkl                    # Trained RandomForestClassifier
│   └── scaler.pkl                              # Fitted StandardScaler
└── src/
    ├── app.py                                  # Flask API v3.1.0 (all 9 endpoints)
    ├── server.py                               # Server runner script
    ├── train.py                                # Full training pipeline (8 steps)
    ├── train_fan_model.py                      # RandomForestRegressor 100 trees
    ├── train_humidifier_model.py               # RandomForestClassifier 200 trees, balanced
    ├── predict.py                              # GreenhousePredictor class + CLI
    ├── evaluate.py                             # MAE, RMSE, R², Accuracy, F1, Confusion Matrix
    ├── check_model_accuracy.py                 # Validates saved model accuracy
    ├── data_loader.py                          # Dataset CSV loading and feature extraction
    ├── preprocess.py                           # preprocess_pipeline(), StandardScaler utils
    ├── test_api.py                             # Tests all API endpoints
    └── verify_models.py                        # Model file integrity verification
```

### File Descriptions

| File | Description |
|------|-------------|
| `app.py` | Flask API v3.1.0: /predict, /fan/*, /humidifier/*, /sensors, /health |
| `server.py` | Starts the Flask server |
| `train.py` | Pipeline: load → drop timestamp → split features → 80/20 split → scale → train fan → train humidifier → evaluate → save |
| `train_fan_model.py` | `create_fan_model()`, `train_fan_model()`, `save_fan_model()`, `get_feature_importance()` |
| `train_humidifier_model.py` | `create_humidifier_model()`, `train_humidifier_model()`, `save_humidifier_model()`, `get_feature_importance()` |
| `predict.py` | `GreenhousePredictor` class: loads models and runs inference with feature scaling |
| `evaluate.py` | Regression: MAE, RMSE, R² — Classification: Accuracy, Precision, Recall, F1, Confusion Matrix |
| `check_model_accuracy.py` | Loads saved models and validates against test data |
| `data_loader.py` | `load_dataset()`, `drop_timestamp()`, `get_features_and_labels()` |
| `preprocess.py` | `split_data()`, `create_scaler()`, `scale_features()`, `preprocess_pipeline()` |
| `test_api.py` | Tests all 9 API endpoints including error cases |
| `verify_models.py` | Checks that `fan_model.pkl`, `humidifier_model.pkl`, `scaler.pkl` exist and load |
| `regenerate_dataset.py` | Generates 1500-sample stratified dataset with humidity bands (seed=42) |
| `quick_test.py` | Quick end-to-end system validation |

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.x + pip
- Arduino IDE with ESP32 board package installed

### Installation Steps

```bash
# Step 1: Clone repository
git clone https://github.com/kulindupr/SmartFarming-Lavender-AI.git
cd IT22894588_ClimateControl

# Step 2: Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate    # Linux/Mac

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: (Optional) Retrain models — pre-trained models are included
python src/train.py

# Step 5: Check model accuracy
python src/check_model_accuracy.py

# Step 6: Start API server
python src/server.py
# Server starts at http://0.0.0.0:5000

# Step 7: Test all endpoints
python src/test_api.py

# Step 8: (Optional) Regenerate dataset
python regenerate_dataset.py
```

### Arduino Setup

1. Install [Arduino IDE](https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - File → Preferences → Boards Manager URL:
     `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools → Board → Boards Manager → search "esp32" → install
3. Install required libraries via Sketch → Include Library → Manage Libraries:
   - "DHT sensor library" by Adafruit
   - "OneWire" by Paul Stoffregen
   - "DallasTemperature" by Miles Burton
4. Update firmware:
   ```cpp
   const char* ssid      = "YOUR_WIFI_SSID";
   const char* password  = "YOUR_WIFI_PASSWORD";
   const char* serverURL = "http://YOUR_SERVER_IP:5000/predict";
   ```
5. Select Board: Tools → Board → ESP32 Dev Module
6. Select Port: Tools → Port → (your COM port)
7. Click Upload

---

## 🚀 Usage

### Start the System

```bash
python src/server.py
```

Power on ESP32 with all sensors connected. The system will automatically:
- Read DHT22 and DS18B20 every 30 seconds
- POST to `/predict` and receive `effective_fan_speed` + `effective_humidifier_level`
- Adjust fan speed via L298N PWM
- Control mist maker mode via GPIO 25

### Manual API Testing

```bash
# Predict
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"air_temp":28.5,"humidity":65.0,"soil_temp":22.0,"target_temp":25.0,"target_humidity":60.0,"prev_fan_speed":50.0,"prev_humidifier_mode":1}'

# Set fan to manual mode at 60%
curl -X POST http://localhost:5000/fan/mode   -H "Content-Type: application/json" -d '{"mode":"manual"}'
curl -X POST http://localhost:5000/fan/manual -H "Content-Type: application/json" -d '{"on":true,"speed":60}'

# Turn humidifier off
curl -X POST http://localhost:5000/humidifier/mode -H "Content-Type: application/json" -d '{"mode":"off"}'

# Set humidifier to high manually
curl -X POST http://localhost:5000/humidifier/mode   -H "Content-Type: application/json" -d '{"mode":"manual"}'
curl -X POST http://localhost:5000/humidifier/manual -H "Content-Type: application/json" -d '{"level":3}'

# Read current states
curl http://localhost:5000/fan/state
curl http://localhost:5000/humidifier/state
curl http://localhost:5000/sensors
curl http://localhost:5000/health
```

---

## 👥 Contributors

| Name | Student ID | Role | Component |
|------|------------|------|-----------|
| Rubasinghe K.P | IT22894588 | Developer | Intelligent Climate Control |

---

## 📄 License

This project is part of the SmartFarming-Lavender-AI final-year research project.

---

## 🌡️ Intelligent Climate Control — Optimizing Greenhouse Conditions with AI 🌿
