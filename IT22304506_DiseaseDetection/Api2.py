from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np
import socket
import time
import threading
import base64
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
CORS(app)


MODEL_PATH = "best.pt"
CONFIDENCE_THRESHOLD = 0.20
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
ESP32_IP = "10.145.120.187"  #
STREAM_URL = f"http://{ESP32_IP}:81/stream"
UDP_PORT = 82
TARGET_CLASS = 2

# Global variables
model = None
led_controller = None
cap = None
detection_thread = None
is_streaming = False
latest_frame = None
latest_detections = {
    'hat_count': 0,
    'led_active': False,
    'fps': 0,
    'stability_ratio': 0.0
}


class LEDController:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)
        
    def send_command(self, command):

        try:
            self.sock.sendto(command.encode(), (self.ip, self.port))
            print(f" Sent: {command}")
            return True
        except Exception as e:
            print(f" Failed to send {command}: {e}")
            return False
    
    def on(self):
        return self.send_command("LED_ON")
    
    def off(self):
        return self.send_command("LED_OFF")


def connect_to_stream():

    global cap
    
    print(f"📷 Connecting to: {STREAM_URL}")
    
    for attempt in range(5):
        print(f"   Attempt {attempt+1}/5...")
        cap = cv2.VideoCapture(STREAM_URL)
        time.sleep(2)
        
        if cap.isOpened():
            for _ in range(3):
                ret, frame = cap.read()
                if ret:
                    print(f" Stream connected successfully")
                    # Set properties
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return True
                time.sleep(0.1)
            
            cap.release()
        
        if attempt < 4:
            print(f"   Retrying in 2 seconds...")
            time.sleep(2)
    
    print(f" Failed to connect after 5 attempts")
    return False


def detection_loop():

    global is_streaming, latest_frame, latest_detections, cap, model, led_controller
    
    # Detection variables
    led_active = False
    last_led_trigger = 0
    led_cooldown = 1.0
    detection_buffer = []
    
    # FPS calculation
    frame_count = 0
    start_time = time.time()
    last_fps_update = start_time
    fps = 0
    
    while is_streaming:
        if cap is None or not cap.isOpened():
            time.sleep(1)
            continue
        
        # Read frame
        ret, frame = cap.read()
        
        if not ret:
            print(" Lost connection to stream, reconnecting...")
            cap.release()
            time.sleep(1)
            connect_to_stream()
            continue
        
        frame_count += 1
        current_time = time.time()
        
        # Resize frame if needed
        if frame.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Run object detection
        try:
            results = model.predict(
                frame,
                conf=CONFIDENCE_THRESHOLD,
                verbose=False,
                max_det=10,
                imgsz=320,
                classes=[TARGET_CLASS]
            )
        except Exception as e:
            print(f" Detection error: {e}")
            continue
        

        annotated_frame = results[0].plot()
        

        hat_detections = 0
        if results[0].boxes is not None:
            classes = results[0].boxes.cls.cpu().numpy() if results[0].boxes.cls is not None else []
            confidences = results[0].boxes.conf.cpu().numpy() if results[0].boxes.conf is not None else []
            
            for i, cls in enumerate(classes):
                if cls == TARGET_CLASS and confidences[i] >= CONFIDENCE_THRESHOLD:
                    hat_detections += 1
        

        detection_buffer.append(hat_detections > 0)
        if len(detection_buffer) > 10:
            detection_buffer.pop(0)
        
        if detection_buffer:
            detection_ratio = sum(detection_buffer) / len(detection_buffer)
        else:
            detection_ratio = 0
        
        stable_detection = detection_ratio > 0.3

        if led_controller:
            if stable_detection and not led_active and current_time - last_led_trigger > led_cooldown:
                print(f" {hat_detections} hat(s) detected - Turning LED ON")
                if led_controller.on():
                    led_active = True
                    last_led_trigger = current_time
            
            elif led_active and not stable_detection and current_time - last_led_trigger > 2.0:
                print(f" No hats detected - Turning LED OFF")
                if led_controller.off():
                    led_active = False
        
        # Update FPS
        if current_time - last_fps_update >= 0.5:
            fps = frame_count / (current_time - last_fps_update)
            frame_count = 0
            last_fps_update = current_time
        
        # Add text to frame
        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )
        
        led_status = "ON" if led_active else "OFF"
        led_color = (0, 0, 255) if led_active else (0, 255, 0)
        cv2.putText(
            annotated_frame,
            f"LED: {led_status}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            led_color,
            1
        )
        
        # Store latest data
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        latest_frame = base64.b64encode(buffer).decode('utf-8')
        
        latest_detections = {
            'hat_count': hat_detections,
            'led_active': led_active,
            'fps': round(fps, 1),
            'stability_ratio': round(detection_ratio, 2),
            'total_detections': latest_detections.get('total_detections', 0) + (1 if hat_detections > 0 else 0)
        }



@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'stream_connected': is_streaming,
        'esp32_ip': ESP32_IP,
        'target_class': TARGET_CLASS
    })

@app.route('/connect', methods=['POST'])
def connect():

    global is_streaming, detection_thread
    
    if is_streaming:
        return jsonify({'status': 'already_connected'})
    
    # Connect to stream
    if connect_to_stream():
        is_streaming = True
        # Start detection thread
        detection_thread = threading.Thread(target=detection_loop, daemon=True)
        detection_thread.start()
        return jsonify({'status': 'connected', 'message': 'Stream connected successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to connect to stream'}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():

    global is_streaming, cap
    
    is_streaming = False
    time.sleep(1)
    
    if cap is not None:
        cap.release()
        cap = None
    
    # Turn off LED
    if led_controller:
        led_controller.off()
    
    return jsonify({'status': 'disconnected'})

@app.route('/stream', methods=['GET'])
def get_stream():
    """Get latest frame as base64"""
    global latest_frame
    
    if latest_frame:
        return jsonify({
            'frame': latest_frame,
            'detections': latest_detections
        })
    else:
        return jsonify({'error': 'No frame available'}), 404

@app.route('/led/on', methods=['POST'])
def led_on():

    if led_controller and led_controller.on():
        return jsonify({'status': 'success', 'led': 'on'})
    return jsonify({'status': 'error', 'message': 'Failed to turn LED on'}), 500

@app.route('/led/off', methods=['POST'])
def led_off():

    if led_controller and led_controller.off():
        return jsonify({'status': 'success', 'led': 'off'})
    return jsonify({'status': 'error', 'message': 'Failed to turn LED off'}), 500

@app.route('/led/test', methods=['POST'])
def led_test():

    if not led_controller:
        return jsonify({'status': 'error', 'message': 'LED controller not initialized'}), 500
    
    if led_controller.on():
        time.sleep(0.5)
        if led_controller.off():
            return jsonify({'status': 'success', 'message': 'LED test successful'})
    
    return jsonify({'status': 'error', 'message': 'LED test failed'}), 500

@app.route('/config', methods=['POST'])
def update_config():

    global CONFIDENCE_THRESHOLD, TARGET_CLASS
    
    data = request.json
    
    if 'confidence' in data:
        CONFIDENCE_THRESHOLD = max(0.05, min(0.95, float(data['confidence'])))
    
    if 'target_class' in data:
        TARGET_CLASS = int(data['target_class'])
    
    return jsonify({
        'confidence': CONFIDENCE_THRESHOLD,
        'target_class': TARGET_CLASS
    })

@app.route('/snapshot', methods=['POST'])
def save_snapshot():

    global latest_frame
    
    if latest_frame:
        timestamp = int(time.time())
        # In a real app, you might save this to disk or return for download
        return jsonify({
            'status': 'success',
            'snapshot': latest_frame,
            'timestamp': timestamp
        })
    
    return jsonify({'error': 'No frame available'}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("ESP32-CAM Hat Detection API Server")
    print("=" * 60)
    
    # Initialize LED controller
    print("\n🔌 Initializing LED controller...")
    led_controller = LEDController(ESP32_IP, UDP_PORT)
    
    # Test LED connection
    if led_controller.on():
        time.sleep(0.5)
        if led_controller.off():
            print(" LED control working")
        else:
            print(" LED OFF failed, continuing anyway")
    else:
        print(" LED ON failed, continuing without LED control")
        led_controller = None
    
    # Load YOLO model
    print("\n Loading YOLO model...")
    try:
        model = YOLO(MODEL_PATH)
        print(" Model loaded successfully")
    except Exception as e:
        print(f" Failed to load model: {e}")
        exit()
    
    print("\n Starting Flask server...")
    print(f" ESP32 IP: {ESP32_IP}")
    print(f" Target Class: {TARGET_CLASS} (Hat)")
    print("\n API Endpoints:")
    print("   GET  /health     - Health check")
    print("   POST /connect    - Connect to stream")
    print("   POST /disconnect - Disconnect from stream")
    print("   GET  /stream     - Get latest frame")
    print("   POST /led/on     - Turn LED on")
    print("   POST /led/off    - Turn LED off")
    print("   POST /led/test   - Test LED")
    print("   POST /config     - Update config")
    print("   POST /snapshot   - Save snapshot")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)