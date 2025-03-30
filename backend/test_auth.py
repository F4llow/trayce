import cv2
import numpy as np
import os
import base64
import json
from flask import Flask, Response, render_template, request, jsonify, redirect, session, url_for
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from gemini_spatial import GeminiSpatial
from dotenv import load_dotenv
from recyability import compute_tray_score
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from functools import wraps

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

# Auth0 setup
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Auth required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# Set environment variable to skip authorization (for OpenCV macOS fix)
os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'

# Create uploads directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# YOLO model
model = YOLO('yolo11n.pt')
gemini = GeminiSpatial()

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

WHITELIST_CLASSES = [
    'bottle', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'dining table', 'person'
]
CONFIDENCE_THRESHOLD = 0.30

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        results = model(frame, conf=CONFIDENCE_THRESHOLD)
        annotated_frame = frame.copy()
        boxes = results[0].boxes
        for box in boxes:
            class_id = int(box.cls.item())
            class_name = COCO_CLASSES[class_id]
            if class_name in WHITELIST_CLASSES:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = box.conf.item()
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                label = f"{class_name}: {confidence:.2f}"
                cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def process_image(image_path):
    image = cv2.imread(image_path)
    results = model(image, conf=CONFIDENCE_THRESHOLD)
    annotated_image = image.copy()
    boxes = results[0].boxes
    detections = []
    for box in boxes:
        class_id = int(box.cls.item())
        class_name = COCO_CLASSES[class_id]
        if class_name in WHITELIST_CLASSES:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = box.conf.item()
            cv2.rectangle(annotated_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(annotated_image, label, (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            detections.append({
                'class': class_name,
                'confidence': float(confidence),
                'box': [int(x1), int(y1), int(x2), int(y2)]
            })
    _, buffer = cv2.imencode('.jpg', annotated_image)
    img_str = base64.b64encode(buffer).decode('utf-8')
    return img_str, detections

# -------------------------
# Auth Routes
# -------------------------
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
          prompt="login"
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode({
            "returnTo": url_for("index", _external=True),
            "client_id": os.getenv("AUTH0_CLIENT_ID"),
        }, quote_via=quote_plus)
    )

# -------------------------
# App Routes (Protected)
# -------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session.get("user"))

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    img_base64, detections = process_image(file_path)
    return jsonify({
        'image': f"data:image/jpeg;base64,{img_base64}",
        'detections': detections
    })

@app.route('/gemini_detect', methods=['POST'])
@login_required
def gemini_detect():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file part'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)
    img_base64, detections = gemini.detect_objects(file_path)
    return jsonify({
        'image': f"data:image/jpeg;base64,{img_base64}",
        'detections': detections
    })

@app.route('/analyze_tray', methods=['POST'])
@login_required
def analyze_tray():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file part'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)
    img_base64, categorized_items = gemini.analyze_tray(file_path)
    tray_score = compute_tray_score(categorized_items)
    return jsonify({
        'image': f"data:image/jpeg;base64,{img_base64}",
        'categorized_items': categorized_items,
        'tray_score': tray_score
    })

if __name__ == '__main__':
    app.run(debug=True)
