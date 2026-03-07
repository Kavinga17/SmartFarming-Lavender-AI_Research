from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import base64

app = Flask(__name__)

# CONFIG
MODEL_PATH = "My_Model.pt"
CONFIDENCE = 0.25

# Class names
CLASS_NAMES = {
    0: "Lavender_Disease",
    1: "Lavender_Healthy"
}

# Color coding
BOX_COLORS = {
    0: (0, 0, 255),    # Red for disease
    1: (0, 255, 0)     # Green for healthy
}

# Load YOLO model
model = YOLO(MODEL_PATH)

def process_image_with_yolo(image_array):
    # Run prediction
    results = model.predict(
        source=image_array,
        conf=CONFIDENCE,
        save=False,
        verbose=False
    )
    
    detections = []
    
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        
        # Get coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        detection = {
            'class_id': cls_id,
            'class_name': CLASS_NAMES.get(cls_id, 'Unknown'),
            'confidence': conf,
            'bbox': {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            }
        }
        detections.append(detection)
    
    return detections, results[0].plot() if len(detections) > 0 else image_array

def draw_detections_on_image(img, detections):

    img_copy = img.copy()
    
    for detection in detections:
        cls_id = detection['class_id']
        conf = detection['confidence']
        bbox = detection['bbox']
        
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        label = f"{detection['class_name']} {conf:.2f}"
        color = BOX_COLORS.get(cls_id, (255, 255, 0))
        
        # Draw rectangle
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
        
        # Draw label background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        
        cv2.rectangle(
            img_copy,
            (x1, y1 - text_height - 10),
            (x1 + text_width + 4, y1),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            img_copy,
            label,
            (x1 + 2, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
    
    return img_copy

def image_to_base64(image):

    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input data
        input_data = request.get_json()
        
        if 'image_url' in input_data:
            # Download image from URL
            response = requests.get(input_data['image_url'])
            img = Image.open(BytesIO(response.content))
            # Convert PIL to OpenCV format
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
        elif 'image_base64' in input_data:
            # Decode base64 image
            img_data = base64.b64decode(input_data['image_base64'])
            img = Image.open(BytesIO(img_data))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
        else:
            return jsonify({'error': 'Please provide either image_url or image_base64'}), 400
        

        detections, annotated_img = process_image_with_yolo(img)
        

        if len(detections) > 0 and not isinstance(annotated_img, np.ndarray):
            annotated_img = draw_detections_on_image(img, detections)
        

        annotated_image_base64 = image_to_base64(annotated_img)
        
        # Prepare response
        response_data = {
            'detections': detections,
            'total_detections': len(detections),
            'annotated_image': annotated_image_base64,
            'message': 'No detections found' if len(detections) == 0 else f'Found {len(detections)} detection(s)'
        }
        
        # Add summary statistics
        if len(detections) > 0:
            disease_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Disease')
            healthy_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Healthy')
            response_data['summary'] = {
                'disease_count': disease_count,
                'healthy_count': healthy_count,
                'has_disease': disease_count > 0
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict_file', methods=['POST'])
def predict_file():

    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        

        img_bytes = file.read()
        img = Image.open(BytesIO(img_bytes))
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        

        detections, annotated_img = process_image_with_yolo(img)
        

        if len(detections) > 0:
            annotated_img = draw_detections_on_image(img, detections)
        

        annotated_image_base64 = image_to_base64(annotated_img)
        
        # Prepare response
        response_data = {
            'detections': detections,
            'total_detections': len(detections),
            'annotated_image': annotated_image_base64,
            'filename': file.filename
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():

    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'classes': CLASS_NAMES
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)