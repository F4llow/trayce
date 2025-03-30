import cv2
import numpy as np
import os
import base64
from flask import Flask, Response, render_template, request, jsonify
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from gemini_spatial import GeminiSpatial
from dotenv import load_dotenv
from recyability import compute_tray_score


# Load environment variables
load_dotenv()

# Set environment variable to skip authorization
os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Load the YOLOv11 model
model = YOLO('yolo11n.pt')  # Using the nano model for faster inference

# Initialize Gemini Spatial
gemini = GeminiSpatial()

# COCO dataset class names
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Whitelist: Only these classes will be shown
# Modify this list to include only the classes you want to detect
WHITELIST_CLASSES = [
    'bottle', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'dining table', 'person'
]

# Confidence threshold for detections (0.0 to 1.0)
# Lower this value to show more detections with lower confidence
# Increase this value to only show high-confidence detections
CONFIDENCE_THRESHOLD = 0.30  # Default is 0.25 (25%)

def generate_frames():
    # Access webcam (0 is usually the default webcam, 2 is typically the external webcam)
    cap = cv2.VideoCapture(0)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Perform object detection with the confidence threshold
            results = model(frame, conf=CONFIDENCE_THRESHOLD)
            
            # Create a copy of the original frame for drawing filtered results
            annotated_frame = frame.copy()
            
            # Get the detection results
            boxes = results[0].boxes
            
            # Filter and draw only the classes we want
            for box in boxes:
                class_id = int(box.cls.item())
                class_name = COCO_CLASSES[class_id]
                
                # Only include classes in the whitelist
                if class_name in WHITELIST_CLASSES:
                    # Get coordinates and confidence
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = box.conf.item()
            
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            label = f"{class_name}: {confidence:.2f}" 
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Convert to jpeg format
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()
            
            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def process_image(image_path):
    # Read the image
    image = cv2.imread(image_path)
    
    # Perform object detection with the confidence threshold
    results = model(image, conf=CONFIDENCE_THRESHOLD)
    
    # Create a copy of the original image for drawing filtered results
    annotated_image = image.copy()
    
    # Get the detection results
    boxes = results[0].boxes
    
    # Filter and draw only the classes we want
    detections = []
    for box in boxes:
        class_id = int(box.cls.item())
        class_name = COCO_CLASSES[class_id]
        
        # Only include classes in the whitelist
        if class_name in WHITELIST_CLASSES:
            # Get coordinates and confidence
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = box.conf.item()
            
            # Draw bounding box
            cv2.rectangle(annotated_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Add label with class name and confidence
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(annotated_image, label, (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Add detection to the list
            detections.append({
                'class': class_name,
                'confidence': float(confidence),
                'box': [int(x1), int(y1), int(x2), int(y2)]
            })
    
    # Convert the annotated image to base64 for displaying in HTML
    _, buffer = cv2.imencode('.jpg', annotated_image)
    img_str = base64.b64encode(buffer).decode('utf-8')
    
    return img_str, detections

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the uploaded image
        img_base64, detections = process_image(file_path)
        
        return jsonify({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'detections': detections
        })

@app.route('/gemini_detect', methods=['POST'])
def gemini_detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the uploaded image with Gemini
        img_base64, detections = gemini.detect_objects(file_path)
        
        return jsonify({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'detections': detections
        })

@app.route('/analyze_tray', methods=['POST'])
def analyze_tray():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the uploaded image with Gemini for tray analysis
        img_base64, categorized_items = gemini.analyze_tray(file_path)

        tray_score = compute_tray_score(categorized_items)
        
        return jsonify({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'categorized_items': categorized_items,
            'tray_score': tray_score
        })

if __name__ == '__main__':
    app.run(debug=True)
