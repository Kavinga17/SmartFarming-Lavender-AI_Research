"""
Unified Flask API Server for Smart Farming System
Combines:
- IT22894588: Climate Control System (Fan & Humidifier)
- IT22304506: Disease Detection (Lavender Disease + Insect Detection)
- ESP32-CAM: MJPEG stream (port 81) + UDP LED/buzzer control (port 82)

All services run on a single port (5000)
"""

import os
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime, UTC
import numpy as np
import cv2
import socket
import time
import threading
import base64
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import requests as http_requests  # renamed to avoid conflict with flask.request

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
CORS(app)

# ════════════════════════════════════════════════════════════════════════════════
#  CLIMATE CONTROL CONFIGURATION (IT22894588)
# ════════════════════════════════════════════════════════════════════════════════

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'IT22894588_ClimateControl', 'models')
FAN_MODEL_PATH = os.path.join(MODELS_DIR, 'fan_model.pkl')
HUMIDIFIER_MODEL_PATH = os.path.join(MODELS_DIR, 'humidifier_model.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

FEATURE_NAMES = [
    'air_temp', 'humidity', 'soil_temp',
    'target_temp', 'target_humidity',
    'prev_fan_speed', 'prev_humidifier_mode'
]

fan_model = None
humidifier_model = None
scaler = None

latest_sensor_data = {
    'air_temp': 0.0,
    'humidity': 0.0,
    'soil_temp': 0.0,
    'timestamp': None
}

fan_control = {
    'mode': 'auto',
    'manual_speed': 0,
    'manual_on': False
}

humidifier_control = {
    'mode': 'auto',
    'manual_level': 0
}

# ════════════════════════════════════════════════════════════════════════════════
#  DISEASE DETECTION CONFIGURATION (IT22304506 - Api.py)
# ════════════════════════════════════════════════════════════════════════════════

DISEASE_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'IT22304506_DiseaseDetection', 'My_Model.pt')
DISEASE_CONFIDENCE = 0.25

DISEASE_CLASS_NAMES = {
    0: "Lavender_Disease",
    1: "Lavender_Healthy"
}

DISEASE_BOX_COLORS = {
    0: (0, 0, 255),
    1: (0, 255, 0)
}

disease_model = None

# ════════════════════════════════════════════════════════════════════════════════
#  INSECT DETECTION + ESP32-CAM CONFIGURATION (IT22304506 - Api2.py)
#
#  Arduino sketch exposes:
#    - HTTP  port 81  → MJPEG stream  at  /stream
#    - UDP   port 82  → commands: "LED_ON" → triggers flash LED + police siren
#                                 "LED_OFF" → turns off LED + short beep
#                       responses: "LED_ON_OK" / "LED_OFF_OK"
# ════════════════════════════════════════════════════════════════════════════════

ESP32_IP = "192.168.0.198"          # Change to match your ESP32-CAM IP
UDP_PORT = 82                         # Must match Arduino udpPort (82)
STREAM_PORT = 81                      # Must match Arduino streamServer port (81)
STREAM_URL = f"http://{ESP32_IP}:{STREAM_PORT}/stream"

INSECT_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'IT22304506_DiseaseDetection', 'best.pt')
INSECT_CONFIDENCE_THRESHOLD = 0.20
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
TARGET_CLASS = 2

# UDP acknowledgement read timeout (seconds) — Arduino replies LED_ON_OK / LED_OFF_OK
UDP_ACK_TIMEOUT = 0.5

insect_model = None
led_controller = None
cap = None
detection_thread = None
is_streaming = False
latest_frame = None
latest_detections = {
    'hat_count': 0,
    'led_active': False,
    'fps': 0,
    'stability_ratio': 0.0,
    'total_detections': 0
}


# ════════════════════════════════════════════════════════════════════════════════
#  INITIALIZATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def load_climate_models():
    """Load climate control models"""
    global fan_model, humidifier_model, scaler
    print("🌡️  Loading Climate Control models...")

    if not os.path.exists(FAN_MODEL_PATH):
        print(f"⚠️  Fan model not found: {FAN_MODEL_PATH}")
        return False
    if not os.path.exists(HUMIDIFIER_MODEL_PATH):
        print(f"⚠️  Humidifier model not found: {HUMIDIFIER_MODEL_PATH}")
        return False
    if not os.path.exists(SCALER_PATH):
        print(f"⚠️  Scaler not found: {SCALER_PATH}")
        return False

    fan_model = joblib.load(FAN_MODEL_PATH)
    humidifier_model = joblib.load(HUMIDIFIER_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    if hasattr(humidifier_model, 'classes_'):
        print(f"   Humidifier model classes: {humidifier_model.classes_}")
    print("✅ Climate Control models loaded successfully!")
    return True


def load_disease_model():
    """Load disease detection model"""
    global disease_model
    print("🌿 Loading Disease Detection model...")

    if not os.path.exists(DISEASE_MODEL_PATH):
        print(f"⚠️  Disease model not found: {DISEASE_MODEL_PATH}")
        return False

    disease_model = YOLO(DISEASE_MODEL_PATH)
    print("✅ Disease Detection model loaded successfully!")
    return True


def load_insect_model():
    """Load insect detection model"""
    global insect_model
    print("🐛 Loading Insect Detection model...")

    if not os.path.exists(INSECT_MODEL_PATH):
        print(f"⚠️  Insect model not found: {INSECT_MODEL_PATH}")
        return False

    insect_model = YOLO(INSECT_MODEL_PATH)
    print("✅ Insect Detection model loaded successfully!")
    return True


def initialize_led_controller():
    """
    Initialize and verify the UDP LED controller that talks to the Arduino.
    The Arduino (port 82) expects plaintext UDP commands:
      "LED_ON"  → turns flash LED on + plays police siren, replies "LED_ON_OK"
      "LED_OFF" → turns flash LED off + plays short beep, replies "LED_OFF_OK"
    Returns True only when both ON and OFF round-trips succeed.
    """
    global led_controller
    print("💡 Initializing ESP32-CAM LED controller (UDP)...")

    controller = LEDController(ESP32_IP, UDP_PORT, ack_timeout=UDP_ACK_TIMEOUT)

    # Test LED_ON → expect "LED_ON_OK"
    ok_on, ack_on = controller.on()
    if not ok_on:
        print(f"⚠️  LED_ON send failed — continuing without LED control")
        return False

    print(f"   LED_ON sent, ack='{ack_on}'")
    time.sleep(0.5)

    # Test LED_OFF → expect "LED_OFF_OK"
    ok_off, ack_off = controller.off()
    if not ok_off:
        print(f"⚠️  LED_OFF send failed — continuing without LED control")
        return False

    print(f"   LED_OFF sent, ack='{ack_off}'")
    led_controller = controller
    print("✅ LED controller ready")
    return True


def normalize_humidifier_prediction(raw_pred: int) -> int:
    """Normalise humidifier prediction to 0-3"""
    return int(np.clip(raw_pred, 0, 3))


# ════════════════════════════════════════════════════════════════════════════════
#  LED CONTROLLER CLASS
#  Wraps UDP send → read-ack to match Arduino protocol exactly.
# ════════════════════════════════════════════════════════════════════════════════

class LEDController:
    """
    Sends UDP commands to the ESP32-CAM Arduino sketch and reads the
    acknowledgement that the Arduino writes back.

    Arduino behaviour:
      "LED_ON"  command → turns on GPIO-4 flash LED, plays police siren,
                          sends back "LED_ON_OK"
      "LED_OFF" command → turns off GPIO-4 flash LED, plays short beep,
                          sends back "LED_OFF_OK"
    """

    def __init__(self, ip: str, port: int, ack_timeout: float = 0.5):
        self.ip = ip
        self.port = port
        self.ack_timeout = ack_timeout
        # One socket reused for all sends; recvfrom reads the Arduino ack.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(self.ack_timeout)
        self._lock = threading.Lock()   # safe for multi-threaded Flask

    def send_command(self, command: str) -> tuple[bool, str]:
        """
        Send a UDP command and attempt to read the Arduino's ack reply.
        Returns (success: bool, ack_message: str).
        If the ack times out the command is still considered sent (best-effort).
        """
        with self._lock:
            try:
                self._sock.sendto(command.encode(), (self.ip, self.port))
                print(f"📤 UDP → {self.ip}:{self.port}  cmd='{command}'")
            except Exception as e:
                print(f"❌ UDP send failed for '{command}': {e}")
                return False, ""

            # Try to read ack (Arduino sends "LED_ON_OK" or "LED_OFF_OK")
            try:
                data, _ = self._sock.recvfrom(64)
                ack = data.decode().strip()
                print(f"📥 UDP ack='{ack}'")
                return True, ack
            except socket.timeout:
                # No ack within timeout — command was still sent
                print(f"⚠️  No UDP ack for '{command}' (timeout={self.ack_timeout}s) — assuming sent")
                return True, ""
            except Exception as e:
                print(f"⚠️  UDP ack read error: {e}")
                return True, ""

    def on(self) -> tuple[bool, str]:
        """
        Send LED_ON.
        Arduino response: turns on flash LED + plays police siren + replies LED_ON_OK.
        """
        return self.send_command("LED_ON")

    def off(self) -> tuple[bool, str]:
        """
        Send LED_OFF.
        Arduino response: turns off flash LED + plays short beep + replies LED_OFF_OK.
        """
        return self.send_command("LED_OFF")

    def close(self):
        try:
            self._sock.close()
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════════
#  INSECT DETECTION HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def connect_to_stream() -> bool:
    """
    Open the ESP32-CAM MJPEG stream (HTTP port 81, path /stream).
    Retries 5 times with 2-second delays.
    """
    global cap

    print(f"📷 Connecting to ESP32-CAM stream: {STREAM_URL}")

    for attempt in range(5):
        print(f"   Attempt {attempt + 1}/5 …")
        cap = cv2.VideoCapture(STREAM_URL)
        time.sleep(2)

        if cap.isOpened():
            for _ in range(3):
                ret, frame = cap.read()
                if ret and frame is not None:
                    print("✅ Stream connected successfully")
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return True
                time.sleep(0.1)
            cap.release()
            cap = None

        if attempt < 4:
            print("   Retrying in 2 seconds …")
            time.sleep(2)

    print("❌ Failed to connect to ESP32-CAM stream after 5 attempts")
    return False


def detection_loop():
    """
    Background thread: reads frames from the ESP32-CAM stream,
    runs YOLO insect detection, and drives the Arduino LED via UDP.

    LED logic (mirrors Arduino safety timeout of 30 s):
      • Stable insect detection  → send LED_ON  (Arduino lights LED + siren)
      • Detection clears         → send LED_OFF (Arduino extinguishes LED + beep)
      • 30-second safety timeout is on the Arduino side; Python still sends
        LED_OFF when detection clears so the Arduino timeout is rarely hit.
    """
    global is_streaming, latest_frame, latest_detections, cap
    global insect_model, led_controller
    global INSECT_CONFIDENCE_THRESHOLD, TARGET_CLASS

    led_active = False
    last_led_trigger = 0.0
    led_cooldown = 1.0          # seconds between consecutive LED_ON triggers
    led_off_delay = 2.0         # seconds of no detection before sending LED_OFF
    detection_buffer: list[bool] = []

    frame_count = 0
    fps = 0.0
    last_fps_update = time.time()

    while is_streaming:
        if cap is None or not cap.isOpened():
            time.sleep(1)
            continue

        ret, frame = cap.read()

        if not ret or frame is None:
            print("⚠️  Lost connection to ESP32-CAM stream, reconnecting …")
            cap.release()
            cap = None
            time.sleep(1)
            connect_to_stream()
            continue

        frame_count += 1
        current_time = time.time()

        # Resize if needed
        if frame.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # ── YOLO inference ────────────────────────────────────────────────────
        try:
            results = insect_model.predict(
                frame,
                conf=INSECT_CONFIDENCE_THRESHOLD,
                verbose=False,
                max_det=10,
                imgsz=320,
                classes=[TARGET_CLASS]
            )
        except Exception as e:
            print(f"❌ YOLO detection error: {e}")
            continue

        annotated_frame = results[0].plot()

        # Count target-class detections above threshold
        hat_detections = 0
        if results[0].boxes is not None:
            classes = results[0].boxes.cls.cpu().numpy() \
                if results[0].boxes.cls is not None else np.array([])
            confs = results[0].boxes.conf.cpu().numpy() \
                if results[0].boxes.conf is not None else np.array([])
            for i, cls in enumerate(classes):
                if int(cls) == TARGET_CLASS and confs[i] >= INSECT_CONFIDENCE_THRESHOLD:
                    hat_detections += 1

        # Rolling stability buffer (10 frames)
        detection_buffer.append(hat_detections > 0)
        if len(detection_buffer) > 10:
            detection_buffer.pop(0)
        detection_ratio = sum(detection_buffer) / len(detection_buffer) \
            if detection_buffer else 0.0
        stable_detection = detection_ratio > 0.3

        # ── LED / Arduino control ─────────────────────────────────────────────
        if led_controller:
            if stable_detection and not led_active \
                    and (current_time - last_led_trigger) > led_cooldown:
                print(f"🔴 {hat_detections} insect(s) detected → LED_ON + siren")
                ok, ack = led_controller.on()
                if ok:
                    led_active = True
                    last_led_trigger = current_time
                    print(f"   Arduino ack: '{ack}'")

            elif led_active and not stable_detection \
                    and (current_time - last_led_trigger) > led_off_delay:
                print("🟢 No insects detected → LED_OFF")
                ok, ack = led_controller.off()
                if ok:
                    led_active = False
                    print(f"   Arduino ack: '{ack}'")

        # ── FPS calculation ───────────────────────────────────────────────────
        if current_time - last_fps_update >= 0.5:
            fps = frame_count / (current_time - last_fps_update)
            frame_count = 0
            last_fps_update = current_time

        # ── OSD overlay ───────────────────────────────────────────────────────
        cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        led_status = "ON" if led_active else "OFF"
        led_color = (0, 0, 255) if led_active else (0, 255, 0)
        cv2.putText(annotated_frame, f"LED: {led_status}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, led_color, 1)
        cv2.putText(annotated_frame, f"Insects: {hat_detections}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 1)

        # ── Encode frame to base64 for API consumers ──────────────────────────
        ret_enc, buffer = cv2.imencode('.jpg', annotated_frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret_enc:
            latest_frame = base64.b64encode(buffer).decode('utf-8')

        latest_detections = {
            'hat_count': hat_detections,
            'led_active': led_active,
            'fps': round(fps, 1),
            'stability_ratio': round(detection_ratio, 2),
            'total_detections': latest_detections.get('total_detections', 0)
                                 + (1 if hat_detections > 0 else 0)
        }

    # Thread exiting — ensure LED is off
    if led_active and led_controller:
        print("🔒 Detection loop ending → sending LED_OFF")
        led_controller.off()


# ════════════════════════════════════════════════════════════════════════════════
#  DISEASE DETECTION HELPER FUNCTIONS (IT22304506 - Api.py)
# ════════════════════════════════════════════════════════════════════════════════

def process_image_with_yolo(image_array):
    """Run disease detection model on a BGR image array."""
    results = disease_model.predict(
        source=image_array,
        conf=DISEASE_CONFIDENCE,
        save=False,
        verbose=False
    )

    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        detections.append({
            'class_id': cls_id,
            'class_name': DISEASE_CLASS_NAMES.get(cls_id, 'Unknown'),
            'confidence': conf,
            'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        })
    return detections


def draw_detections_on_image(img, detections):
    """Draw YOLO bounding boxes on a copy of img."""
    img_copy = img.copy()
    for det in detections:
        cls_id = det['class_id']
        conf = det['confidence']
        b = det['bbox']
        x1, y1, x2, y2 = b['x1'], b['y1'], b['x2'], b['y2']
        label = f"{det['class_name']} {conf:.2f}"
        color = DISEASE_BOX_COLORS.get(cls_id, (255, 255, 0))

        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img_copy, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img_copy, label, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    return img_copy


def image_to_base64(image) -> str:
    """Encode a BGR image array as a JPEG base64 string."""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Smart Farming Unified API',
        'version': '1.1.0',
        'modules': {
            'climate_control': 'IT22894588 - Fan & Humidifier Control',
            'disease_detection': 'IT22304506 - Lavender Disease Detection',
            'insect_detection': 'IT22304506 - Insect Detection with ESP32-CAM'
        },
        'esp32_cam': {
            'ip': ESP32_IP,
            'stream_url': STREAM_URL,
            'udp_port': UDP_PORT,
            'arduino_commands': {
                'LED_ON': 'Flash LED on + police siren → ack: LED_ON_OK',
                'LED_OFF': 'Flash LED off + short beep → ack: LED_OFF_OK'
            }
        },
        'endpoints': {
            'POST /predict': 'Predict fan speed + humidifier level',
            'POST /fan/mode': 'Set fan mode: off | manual | auto',
            'POST /fan/manual': 'Set manual fan on/off + speed (1-100)',
            'GET  /fan/state': 'Get fan control state',
            'POST /humidifier/mode': 'Set humidifier mode: off | manual | auto',
            'POST /humidifier/manual': 'Set manual level: 0=off 1=low 2=med 3=high',
            'GET  /humidifier/state': 'Get humidifier control state',
            'GET  /sensors': 'Latest sensor readings',
            'POST /diseasPredict': 'Detect lavender disease from image',
            'POST /insect/connect': 'Connect to ESP32-CAM stream',
            'POST /insect/disconnect': 'Disconnect from stream',
            'GET  /insect/stream': 'Get latest annotated frame (base64)',
            'POST /insect/led/on': 'Send LED_ON to Arduino (LED + siren)',
            'POST /insect/led/off': 'Send LED_OFF to Arduino (LED off + beep)',
            'POST /insect/led/test': 'Test LED round-trip with Arduino ack',
            'POST /insect/config': 'Update confidence / target_class / esp32_ip',
            'POST /insect/snapshot': 'Return current frame as base64 snapshot',
            'GET  /health': 'Combined health check'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'climate_control': {
            'models_loaded': all([fan_model, humidifier_model, scaler])
        },
        'disease_detection': {
            'model_loaded': disease_model is not None,
            'classes': DISEASE_CLASS_NAMES
        },
        'insect_detection': {
            'model_loaded': insect_model is not None,
            'stream_active': is_streaming,
            'led_controller_ready': led_controller is not None,
            'esp32_ip': ESP32_IP,
            'stream_url': STREAM_URL,
            'udp_port': UDP_PORT,
            'target_class': TARGET_CLASS
        }
    })


# ════════════════════════════════════════════════════════════════════════════════
#  CLIMATE CONTROL ENDPOINTS (IT22894588)
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/fan/mode', methods=['POST'])
def set_fan_mode():
    data = request.get_json()
    if not data or 'mode' not in data:
        return jsonify({'error': 'Missing "mode" field'}), 400
    mode = data['mode']
    if mode not in ('off', 'manual', 'auto'):
        return jsonify({'error': 'mode must be "off", "manual", or "auto"'}), 400
    fan_control['mode'] = mode
    return jsonify({'success': True, 'fan_control': fan_control})


@app.route('/fan/manual', methods=['POST'])
def set_fan_manual():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400
    if 'on' in data:
        fan_control['manual_on'] = bool(data['on'])
    if 'speed' in data:
        speed = int(data['speed'])
        if not (1 <= speed <= 100):
            return jsonify({'error': 'speed must be between 1 and 100'}), 400
        fan_control['manual_speed'] = speed
    return jsonify({'success': True, 'fan_control': fan_control})


@app.route('/fan/state', methods=['GET'])
def get_fan_state():
    return jsonify(fan_control)


@app.route('/humidifier/mode', methods=['POST'])
def set_humidifier_mode():
    data = request.get_json()
    if not data or 'mode' not in data:
        return jsonify({'error': 'Missing "mode" field'}), 400
    mode = data['mode']
    if mode not in ('off', 'manual', 'auto'):
        return jsonify({'error': 'mode must be "off", "manual", or "auto"'}), 400
    humidifier_control['mode'] = mode
    return jsonify({'success': True, 'humidifier_control': humidifier_control})


@app.route('/humidifier/manual', methods=['POST'])
def set_humidifier_manual():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400
    if 'level' in data:
        level = int(data['level'])
        if level not in (0, 1, 2, 3):
            return jsonify({'error': 'level must be 0 (off), 1 (low), 2 (medium), or 3 (high)'}), 400
        humidifier_control['manual_level'] = level
    return jsonify({'success': True, 'humidifier_control': humidifier_control})


@app.route('/humidifier/state', methods=['GET'])
def get_humidifier_state():
    return jsonify(humidifier_control)


@app.route('/predict', methods=['POST'])
def predict():
    """Climate prediction endpoint"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No JSON data provided'}), 400

        missing_fields = [f for f in FEATURE_NAMES if f not in data]
        if missing_fields:
            return jsonify({'error': 'Missing required fields', 'missing': missing_fields}), 400

        try:
            features = pd.DataFrame([[
                float(data['air_temp']),
                float(data['humidity']),
                float(data['soil_temp']),
                float(data['target_temp']),
                float(data['target_humidity']),
                float(data['prev_fan_speed']),
                float(data['prev_humidifier_mode'])
            ]], columns=FEATURE_NAMES)
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid field value: {str(e)}'}), 400

        latest_sensor_data.update({
            'air_temp': float(data['air_temp']),
            'humidity': float(data['humidity']),
            'soil_temp': float(data['soil_temp']),
            'timestamp': datetime.now(UTC).isoformat()
        })

        features_scaled = scaler.transform(features.values)
        ai_fan_speed = float(fan_model.predict(features_scaled)[0])
        raw_hum_prediction = humidifier_model.predict(features_scaled)[0]
        ai_humidifier_level = normalize_humidifier_prediction(int(raw_hum_prediction))

        print(f"[PREDICT] raw_hum={raw_hum_prediction}  normalised={ai_humidifier_level}  "
              f"hum_mode={humidifier_control['mode']}")

        fan_mode = fan_control['mode']
        if fan_mode == 'off':
            effective_fan_speed = 0.0
        elif fan_mode == 'manual':
            effective_fan_speed = float(fan_control['manual_speed']) if fan_control['manual_on'] else 0.0
        else:
            effective_fan_speed = round(ai_fan_speed, 2)

        hum_mode = humidifier_control['mode']
        if hum_mode == 'off':
            effective_humidifier_level = 0
        elif hum_mode == 'manual':
            effective_humidifier_level = int(humidifier_control['manual_level'])
        else:
            effective_humidifier_level = ai_humidifier_level

        print(f"[PREDICT] effective_hum_level={effective_humidifier_level}")

        return jsonify({
            'fan_speed': round(ai_fan_speed, 2),
            'effective_fan_speed': effective_fan_speed,
            'fan_mode': fan_mode,
            'humidifier_mode': ai_humidifier_level,
            'effective_humidifier_level': effective_humidifier_level,
            'humidifier_control_mode': hum_mode,
            'air_temp': float(data['air_temp']),
            'humidity': float(data['humidity']),
            'soil_temp': float(data['soil_temp'])
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/sensors', methods=['GET'])
def sensors():
    return jsonify(latest_sensor_data)


# ════════════════════════════════════════════════════════════════════════════════
#  DISEASE DETECTION ENDPOINTS (IT22304506 - Api.py)
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/diseasPredict', methods=['POST'])
def diseas_predict():
    """Disease detection endpoint"""
    try:
        input_data = request.get_json()

        if 'image_url' in input_data:
            response = http_requests.get(input_data['image_url'], timeout=10)
            img = Image.open(BytesIO(response.content))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        elif 'image_base64' in input_data:
            img_data = base64.b64decode(input_data['image_base64'])
            img = Image.open(BytesIO(img_data))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        else:
            return jsonify({'error': 'Please provide image_url or image_base64'}), 400

        detections = process_image_with_yolo(img)
        annotated_img = draw_detections_on_image(img, detections)
        annotated_image_base64 = image_to_base64(annotated_img)

        disease_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Disease')
        healthy_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Healthy')

        return jsonify({
            'detections': detections,
            'total_detections': len(detections),
            'annotated_image': annotated_image_base64,
            'summary': {
                'disease_count': disease_count,
                'healthy_count': healthy_count,
                'total_count': len(detections),
                'has_disease': disease_count > 0
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════════
#  INSECT DETECTION ENDPOINTS (IT22304506 - Api2.py)
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/insect/connect', methods=['POST'])
def insect_connect():
    """Connect to ESP32-CAM MJPEG stream and start detection thread."""
    global is_streaming, detection_thread

    if is_streaming:
        return jsonify({'status': 'already_connected',
                        'stream_url': STREAM_URL})

    if connect_to_stream():
        is_streaming = True
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()
        return jsonify({
            'status': 'connected',
            'message': 'ESP32-CAM stream connected, detection started',
            'stream_url': STREAM_URL,
            'esp32_ip': ESP32_IP
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to ESP32-CAM at {STREAM_URL}'
        }), 500


@app.route('/insect/disconnect', methods=['POST'])
def insect_disconnect():
    """Stop detection thread and release the stream."""
    global is_streaming, cap

    is_streaming = False
    time.sleep(1.2)   # let the loop exit cleanly

    if cap is not None:
        cap.release()
        cap = None

    # Turn LED off on disconnect (safety)
    if led_controller:
        ok, ack = led_controller.off()
        print(f"   Disconnect LED_OFF ack: '{ack}'")

    return jsonify({'status': 'disconnected',
                    'message': 'Stream stopped and LED turned off'})


@app.route('/insect/stream', methods=['GET'])
def insect_get_stream():
    """Return the latest annotated frame and detection stats."""
    if latest_frame:
        return jsonify({
            'frame': latest_frame,
            'detections': latest_detections
        })
    return jsonify({'error': 'No frame available — call /insect/connect first'}), 404


@app.route('/insect/led/on', methods=['POST'])
def insect_led_on():
    """
    Manually send LED_ON to Arduino.
    Arduino will light the flash LED and play the police siren.
    Returns the Arduino acknowledgement string.
    """
    if not led_controller:
        return jsonify({'status': 'error',
                        'message': 'LED controller not initialised'}), 503
    ok, ack = led_controller.on()
    if ok:
        return jsonify({'status': 'success', 'led': 'on', 'arduino_ack': ack})
    return jsonify({'status': 'error', 'message': 'Failed to send LED_ON'}), 500


@app.route('/insect/led/off', methods=['POST'])
def insect_led_off():
    """
    Manually send LED_OFF to Arduino.
    Arduino will turn off the flash LED and play a short beep.
    Returns the Arduino acknowledgement string.
    """
    if not led_controller:
        return jsonify({'status': 'error',
                        'message': 'LED controller not initialised'}), 503
    ok, ack = led_controller.off()
    if ok:
        return jsonify({'status': 'success', 'led': 'off', 'arduino_ack': ack})
    return jsonify({'status': 'error', 'message': 'Failed to send LED_OFF'}), 500


@app.route('/insect/led/test', methods=['POST'])
def insect_led_test():
    """
    Full LED round-trip test:
      1. Send LED_ON  → read ack (expect "LED_ON_OK")
      2. Wait 0.5 s
      3. Send LED_OFF → read ack (expect "LED_OFF_OK")
    """
    if not led_controller:
        return jsonify({'status': 'error',
                        'message': 'LED controller not initialised'}), 503

    ok_on, ack_on = led_controller.on()
    time.sleep(0.5)
    ok_off, ack_off = led_controller.off()

    if ok_on and ok_off:
        return jsonify({
            'status': 'success',
            'message': 'LED test successful',
            'led_on_ack': ack_on,
            'led_off_ack': ack_off
        })

    return jsonify({
        'status': 'error',
        'message': 'LED test failed',
        'led_on_ok': ok_on,
        'led_off_ok': ok_off
    }), 500


@app.route('/insect/config', methods=['POST'])
def insect_update_config():
    """
    Update runtime insect-detection parameters.
    Accepts JSON with any of:
      confidence   (float 0.05-0.95)
      target_class (int)
      esp32_ip     (str)  — updates stream URL and LED controller IP
    """
    global INSECT_CONFIDENCE_THRESHOLD, TARGET_CLASS
    global ESP32_IP, STREAM_URL, led_controller

    data = request.get_json() or {}

    if 'confidence' in data:
        INSECT_CONFIDENCE_THRESHOLD = max(0.05, min(0.95, float(data['confidence'])))

    if 'target_class' in data:
        TARGET_CLASS = int(data['target_class'])

    if 'esp32_ip' in data:
        new_ip = str(data['esp32_ip']).strip()
        ESP32_IP = new_ip
        STREAM_URL = f"http://{ESP32_IP}:{STREAM_PORT}/stream"
        # Re-create LED controller with new IP
        if led_controller:
            led_controller.close()
        led_controller = LEDController(ESP32_IP, UDP_PORT, ack_timeout=UDP_ACK_TIMEOUT)
        print(f"🔧 ESP32_IP updated to {ESP32_IP}, new STREAM_URL={STREAM_URL}")

    return jsonify({
        'confidence': INSECT_CONFIDENCE_THRESHOLD,
        'target_class': TARGET_CLASS,
        'esp32_ip': ESP32_IP,
        'stream_url': STREAM_URL,
        'udp_port': UDP_PORT
    })


@app.route('/insect/snapshot', methods=['POST'])
def insect_save_snapshot():
    """Return the current annotated frame as a base64 snapshot."""
    if latest_frame:
        return jsonify({
            'status': 'success',
            'snapshot': latest_frame,
            'timestamp': int(time.time()),
            'detections': latest_detections
        })
    return jsonify({'error': 'No frame available'}), 404


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("🌱 Smart Farming Unified API Server")
    print("=" * 70)

    print("\n📦 Loading all models …")
    print("-" * 70)
    climate_loaded = load_climate_models()
    disease_loaded = load_disease_model()
    insect_loaded = load_insect_model()
    print("-" * 70)

    # Only attempt LED init when insect model loaded successfully
    led_ready = False
    if insect_loaded:
        led_ready = initialize_led_controller()
    else:
        print("⏭️  Skipping LED controller init (insect model not loaded)")

    print("-" * 70)
    print("\n📊 Status Summary:")
    print(f"   Climate Control  : {'✅ Ready' if climate_loaded else '❌ Not Available'}")
    print(f"   Disease Detection: {'✅ Ready' if disease_loaded else '❌ Not Available'}")
    print(f"   Insect Detection : {'✅ Ready' if insect_loaded else '❌ Not Available'}")
    print(f"   ESP32-CAM LED    : {'✅ Ready' if led_ready else '⚠️  Not Connected (stream still works)'}")
    print(f"   ESP32 IP         : {ESP32_IP}")
    print(f"   Stream URL       : {STREAM_URL}")
    print(f"   UDP LED port     : {UDP_PORT}")

    print("\n" + "=" * 70)
    print("🚀 Starting server on http://0.0.0.0:5000")
    print("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)