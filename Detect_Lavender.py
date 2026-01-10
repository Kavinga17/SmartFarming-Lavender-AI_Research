from ultralytics import YOLO
import cv2
import numpy as np

# CONFIG 
MODEL_PATH = "My_Model.pt"
IMAGE_PATH = r"Test2.jpg"
CONFIDENCE = 0.25

# Class  
CLASS_NAMES = {
    0: "Lavender_Disease",
    1: "Lavender_Healthy"
}

# Color coding
BOX_COLORS = {
    0: (0, 0, 255),   
    1: (0, 255, 0)    
}


def main():
    model = YOLO(MODEL_PATH)

    #  prediction
    results = model.predict(
        source=IMAGE_PATH,
        conf=CONFIDENCE,
        save=False,
        verbose=False
    )

    # Load original image
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print("Error: Could not load image")
        return
    img = img.astype(np.uint8)

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        #  coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = f"{CLASS_NAMES.get(cls_id, 'Unknown')} {conf:.2f}"
        color = BOX_COLORS.get(cls_id, (255, 255, 0))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )

        # Draw  bounding box*
        cv2.rectangle(
            img,
            (x1, y1),
            (x1 + text_width + 4, y1 + text_height + 4),
            color,
            -1
        )
        cv2.putText(
            img,
            label,
            (x1 + 2, y1 + text_height + 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        print(f"Detected: {CLASS_NAMES.get(cls_id, 'Unknown')} | Confidence: {conf:.2f}")


    cv2.imshow("YOLO Detection", img)
    print("Press 'q' to close window")
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
