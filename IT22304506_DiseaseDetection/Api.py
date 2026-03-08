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
    0: (0, 0, 255),
    1: (0, 255, 0)
}

# Load YOLO model
model = YOLO(MODEL_PATH)


def process_image_with_yolo(image_array):

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

    return detections


def draw_detections_on_image(img, detections):

    img_copy = img.copy()

    for detection in detections:

        cls_id = detection['class_id']
        conf = detection['confidence']
        bbox = detection['bbox']

        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
        label = f"{detection['class_name']} {conf:.2f}"
        color = BOX_COLORS.get(cls_id, (255, 255, 0))

        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)

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


# MAIN ENDPOINT
@app.route('/diseasPredict', methods=['POST'])
def diseasPredict():

    try:

        input_data = request.get_json()

        if 'image_url' in input_data:

            response = requests.get(input_data['image_url'])
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

        # ✅ FIX: Build summary so Dart _summary field is populated correctly
        disease_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Disease')
        healthy_count = sum(1 for d in detections if d['class_name'] == 'Lavender_Healthy')

        response_data = {
            'detections': detections,
            'total_detections': len(detections),
            'annotated_image': annotated_image_base64,
            'summary': {                            # ✅ Added summary block
                'disease_count': disease_count,
                'healthy_count': healthy_count,
                'total_count': len(detections),
                'has_disease': disease_count > 0
            }
        }

        return jsonify(response_data)

    except Exception as e:

        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():

    return jsonify({
        'status': 'running',
        'model_loaded': model is not None,
        'classes': CLASS_NAMES
    })


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5001, debug=True)