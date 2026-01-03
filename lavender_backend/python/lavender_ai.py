import sys
import json
import os
import traceback

# Try to import TensorFlow (handle errors gracefully)
try:
    import tensorflow as tf
    from PIL import Image
    import numpy as np
    
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    TENSORFLOW_AVAILABLE = False

# Class names based on your training
CLASS_NAMES = ['healthy', 'nutrient_deficient', 'diseased']

def preprocess_image(image_path):
    """Preprocess image for model"""
    try:
        img = Image.open(image_path)
        img = img.resize((224, 224))  # Adjust if your model uses different size
        img_array = np.array(img)
        
        # Handle different image formats (RGB vs RGBA)
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]  # Remove alpha channel
        
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0  # Normalize
        return img_array
    except Exception as e:
        print(f"Preprocessing error: {e}", file=sys.stderr)
        return None

def predict_image(image_path):
    """Make prediction on single image"""
    try:
        if not TENSORFLOW_AVAILABLE:
            return {
                "prediction": "error",
                "confidence": 0.0,
                "error": "TensorFlow not available. Check installation.",
                "possible_issues": []
            }
        
        # Try to find model file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, 'my_lavender_expert.h5'),
            os.path.join(script_dir, '../my_lavender_expert.h5'),
            os.path.join(os.getcwd(), 'my_lavender_expert.h5'),
            os.path.join(os.getcwd(), 'python/my_lavender_expert.h5'),
            'my_lavender_expert.h5'
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = os.path.abspath(path)
                print(f"✅ Found model at: {model_path}", file=sys.stderr)
                break
        
        if not model_path:
            return {
                "prediction": "error",
                "confidence": 0.0,
                "error": f"Model file not found. Checked paths: {possible_paths}",
                "possible_issues": []
            }
        
        # Load model
        print("🔄 Loading AI model...", file=sys.stderr)
        model = tf.keras.models.load_model(model_path)
        print("✅ Model loaded successfully", file=sys.stderr)
        
        # Preprocess
        print("🔄 Preprocessing image...", file=sys.stderr)
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            return {
                "prediction": "error",
                "confidence": 0.0,
                "error": "Failed to preprocess image",
                "possible_issues": []
            }
        
        # Predict
        print("🔄 Making prediction...", file=sys.stderr)
        predictions = model.predict(processed_img, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0]))
        
        # Get class name
        class_name = CLASS_NAMES[predicted_class]
        
        # Determine possible issues
        possible_issues = []
        if class_name == 'nutrient_deficient':
            possible_issues = ['nitrogen_deficiency', 'phosphorus_deficiency', 'potassium_deficiency']
        elif class_name == 'diseased':
            possible_issues = ['fungal_infection', 'bacterial_infection', 'pest_infestation']
        
        print(f"✅ Prediction complete: {class_name} ({confidence:.2%})", file=sys.stderr)
        
        return {
            "prediction": class_name,
            "confidence": round(confidence, 4),
            "possible_issues": possible_issues,
            "class_probabilities": [float(p) for p in predictions[0]],
            "model_used": os.path.basename(model_path)
        }
        
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}", file=sys.stderr)
        print(f"📋 Traceback: {traceback.format_exc()}", file=sys.stderr)
        return {
            "prediction": "error",
            "confidence": 0.0,
            "error": str(e),
            "possible_issues": [],
            "traceback": traceback.format_exc()
        }

def main():
    """Main function to handle command line execution"""
    # Get image path from command line argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        
        # Check if file exists
        if not os.path.exists(image_path):
            result = {
                "prediction": "error",
                "confidence": 0.0,
                "error": f"File not found: {image_path}",
                "possible_issues": []
            }
            print(json.dumps(result, indent=2))
            return
        
        # Make prediction
        result = predict_image(image_path)
        
    else:
        # Test mode - no image provided
        result = {
            "prediction": "healthy",
            "confidence": 0.92,
            "possible_issues": [],
            "test_mode": True,
            "message": "No image provided, using test data"
        }
    
    # Always print JSON result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()