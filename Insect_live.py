from ultralytics import YOLO
import cv2
import time
import numpy as np
import socket
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# CONFIG
MODEL_PATH = "best.pt"
CONFIDENCE_THRESHOLD = 0.20
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
ESP32_IP = "192.168.0.196"
STREAM_URL = f"http://{ESP32_IP}:81/stream"
UDP_PORT = 82
TARGET_CLASS = 2


class LEDController:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)

    def send_command(self, command):
        """Send UDP command to ESP32"""
        try:
            self.sock.sendto(command.encode(), (self.ip, self.port))
            print(f"--> Sent: {command}")
            return True
        except Exception as e:
            print(f"--> Failed to send {command}: {e}")
            return False

    def on(self):
        return self.send_command("LED_ON")

    def off(self):
        return self.send_command("LED_OFF")


def connect_to_stream():
    print(f"--> Connecting to: {STREAM_URL}")

    for attempt in range(5):
        print(f"   Attempt {attempt + 1}/5...")
        cap = cv2.VideoCapture(STREAM_URL)

        time.sleep(2)

        if cap.isOpened():
            for _ in range(3):
                ret, frame = cap.read()
                if ret:
                    print(f"--> Stream connected successfully")
                    return cap
                time.sleep(0.1)

            cap.release()

        if attempt < 4:
            print(f"   Retrying in 2 seconds...")
            time.sleep(2)

    print(f"-->  Failed to connect after 5 attempts")
    return None


def test_led_connection(led_controller):
    print("-->  Testing LED connection...")

    # Test ON
    if led_controller.on():
        time.sleep(1)
        # Test OFF
        if led_controller.off():
            print("-->  LED control working")
            return True

    print("-->  LED control test failed")
    return False


print("=" * 60)
print("UDP  Control")
print(f"-->  Detecting  Class {TARGET_CLASS} (Hat)")
print("=" * 60)

#   controller
led_controller = LEDController(ESP32_IP, UDP_PORT)
led_enabled = test_led_connection(led_controller)
if not led_enabled:
    print("-->  Continuing without LED control...")

# Load YOLO model
print("\n--> Loading YOLO model...")
try:
    model = YOLO(MODEL_PATH)
    print("-->  Model loaded successfully")
except Exception as e:
    print(f"-->  Failed to load model: {e}")
    exit()

# Connect to stream
print("\n-->  Connecting to camera stream...")
cap = connect_to_stream()
if cap is None:
    print("-->  Cannot connect to camera")
    print("   Please check:")
    print(f"   1. ESP32 is at IP: {ESP32_IP}")
    print("   2. Stream server is running on port 81")
    print("   3. Both devices are on same network")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print("\n-->  Starting detection...")
print("Controls:")
print("  Q - Quit program")
print("-" * 60)

# Detection variables
led_active = False
led_cooldown = 1.0
last_led_trigger = 0
detection_buffer = []

# FPS
frame_count = 0
start_time = time.time()
last_fps_update = start_time
fps = 0
debug_mode = False

try:
    while True:
        # Read frame
        ret, frame = cap.read()

        if not ret:
            print("-->  Lost connection to stream, reconnecting...")
            cap.release()
            time.sleep(1)
            cap = connect_to_stream()
            if cap is None:
                print("-->  Could not reconnect to stream")
                break
            continue

        frame_count += 1
        current_time = time.time()

        if frame.shape[:2] != (FRAME_HEIGHT, FRAME_WIDTH):
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        #  object detection
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
            print(f"--> Detection error: {e}")
            continue

        #  annotated frame with bounding boxes
        annotated_frame = results[0].plot()

        hat_detections = 0
        if results[0].boxes is not None:
            # Filter detections
            classes = results[0].boxes.cls.cpu().numpy() if results[0].boxes.cls is not None else []
            confidences = results[0].boxes.conf.cpu().numpy() if results[0].boxes.conf is not None else []

            for i, cls in enumerate(classes):
                if cls == TARGET_CLASS and confidences[i] >= CONFIDENCE_THRESHOLD:
                    hat_detections += 1

        # Update  buffer
        detection_buffer.append(hat_detections > 0)
        if len(detection_buffer) > 10:
            detection_buffer.pop(0)

        if detection_buffer:
            detection_ratio = sum(detection_buffer) / len(detection_buffer)
        else:
            detection_ratio = 0

        stable_detection = detection_ratio > 0.3

        if debug_mode and hat_detections > 0:
            print(f"-->  DEBUG: Hat detections: {hat_detections}, Stability: {detection_ratio:.2f}")

        # ==========  CONTROL LOGIC ==========
        if led_enabled:
            if (stable_detection and
                    not led_active and
                    current_time - last_led_trigger > led_cooldown):

                print(f"-->  {hat_detections} hat(s) detected - Turning LED ON")
                if led_controller.on():
                    led_active = True
                    last_led_trigger = current_time
                    print(f"-->  turned ON")
                else:
                    print(f"-->   ON command failed")


            elif (led_active and
                  not stable_detection and
                  current_time - last_led_trigger > 2.0):

                print(f"-->  No hats detected - Turning LED OFF")
                if led_controller.off():
                    led_active = False
                    print(f"-->  LED turned OFF")
                else:
                    print(f"-->  LED OFF command failed")

        # ========== FPS   ==========
        if current_time - last_fps_update >= 0.5:
            fps = frame_count / (current_time - last_fps_update)
            frame_count = 0
            last_fps_update = current_time

        # FPS
        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

        det_color = (0, 0, 255) if hat_detections > 0 else (255, 255, 255)

        #   status
        led_status = "ON" if led_active else "OFF"
        led_color = (0, 0, 255) if led_active else (0, 255, 0)
        cv2.putText(
            annotated_frame,
            f"SOUND: {led_status}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            led_color,
            1
        )

        if debug_mode:
            cv2.putText(
                annotated_frame,
                f"Stability: {detection_ratio:.2f}",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                1
            )

        cv2.putText(
            annotated_frame,
            "Q:Quit",
            (10, FRAME_HEIGHT - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (200, 200, 200),
            1
        )

        cv2.imshow("ESP32-CAM Hat Detection", annotated_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q'):
            print("\n-->  Quitting program...")
            break

        elif key == ord('s') or key == ord('S'):

            filename = f"hat_detection_{int(time.time())}.jpg"
            cv2.imwrite(filename, annotated_frame)
            print(f"-->  Saved: {filename}")

        elif key == ord('l') or key == ord('L'):
            # Manual   toggle
            if led_enabled:
                if led_active:
                    print("-->  Manual: Turning LED OFF")
                    if led_controller.off():
                        led_active = False
                else:
                    print("-->  Manual: Turning LED ON")
                    if led_controller.on():
                        led_active = True
                last_led_trigger = time.time()
            else:
                print("-->  LED control is disabled")

        elif key == ord('t') or key == ord('T'):

            print("-->  Testing LED connection...")
            if led_controller.on():
                time.sleep(0.5)
                if led_controller.off():
                    print("-->  LED test successful")
                else:
                    print("-->  LED OFF failed")
            else:
                print("-->  LED ON failed")

        elif key == ord('d') or key == ord('D'):

            debug_mode = not debug_mode
            print(f"-->  Debug mode: {'ON' if debug_mode else 'OFF'}")

        elif key == ord('+') or key == ord('='):

            CONFIDENCE_THRESHOLD = min(CONFIDENCE_THRESHOLD + 0.05, 0.95)
            print(f"-->  Confidence threshold: {CONFIDENCE_THRESHOLD:.2f}")

        elif key == ord('-') or key == ord('_'):

            CONFIDENCE_THRESHOLD = max(CONFIDENCE_THRESHOLD - 0.05, 0.05)
            print(f"-->  Confidence threshold: {CONFIDENCE_THRESHOLD:.2f}")

except KeyboardInterrupt:
    print("\n-->  Program interrupted by user")

except Exception as e:
    print(f"\n-->  Unexpected error: {e}")
    import traceback

    traceback.print_exc()

finally:

    print("\n-->  Cleaning up...")

    if led_enabled and led_active:
        print("-->  Turning LED off...")
        led_controller.off()

    if 'cap' in locals() and cap is not None:
        cap.release()
        print("-->  Camera released")

    # Close windows
    cv2.destroyAllWindows()

    print("-->  Program finished")
    print("=" * 60)