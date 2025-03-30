import cv2
import numpy as np
import os
import base64
import json
import sqlite3
import requests
from datetime import datetime
from functools import wraps
from flask import Flask, Response, render_template, request, jsonify, redirect, session, url_for
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from gemini_spatial import GeminiSpatial
from dotenv import load_dotenv
from recyability import compute_tray_score
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode

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
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
app.secret_key = os.getenv("APP_SECRET_KEY", "your-secret-key")

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

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'meal_history.db')

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create meals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        meal_date TIMESTAMP NOT NULL,
        meal_image TEXT NOT NULL,
        meal_items TEXT NOT NULL,
        tray_score REAL,
        total_calories INTEGER
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

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
            detected = False
            for box in boxes:
                class_id = int(box.cls.item())
                class_name = COCO_CLASSES[class_id]
                
                # Only include classes in the whitelist
                if class_name in WHITELIST_CLASSES:
                    # Get coordinates and confidence
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = box.conf.item()
                    
                    # Draw bounding box
                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    
                    # Add label with class name and confidence
                    label = f"{class_name}: {confidence:.2f}"
                    cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    detected = True
            
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

def get_calories_for_food(food_name):
    """
    Get calorie information for a food item using the USDA FoodData Central API.
    Returns calories per 100g serving or None if not found.
    """
    try:
        # Search for the food item
        search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "api_key": os.getenv("USDA_API_KEY", "DEMO_KEY"),
            "query": food_name,
            "dataType": "Foundation,SR Legacy",
            "pageSize": 1  # Just get the first result
        }
        
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            print(f"Error fetching nutrition data: {response.status_code}")
            return None
            
        data = response.json()
        
        # Check if we got any results
        if data.get('totalHits', 0) == 0 or not data.get('foods'):
            return None
            
        # Get the first food item
        food = data['foods'][0]
        
        # Look for calories (ENERC_KCAL) in the nutrients
        for nutrient in food.get('foodNutrients', []):
            if nutrient.get('nutrientName') == 'Energy' and nutrient.get('unitName') == 'KCAL':
                return {
                    'calories': nutrient.get('value', 0),
                    'serving_size': 100,  # Typically per 100g
                    'serving_unit': 'g',
                    'food_name': food.get('description', food_name)
                }
                
        return None
    except Exception as e:
        print(f"Error getting calories for {food_name}: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    data = request.json  # Expecting JSON payload
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    try:
        # Decode the base64 image
        image_data = base64.b64decode(data['image'].split(',')[1]) 
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'captured_image.jpg')
        with open(file_path, 'wb') as f:
            f.write(image_data)
        print(f"Image saved to {file_path}")  # Debugging

        # Process the uploaded image
        img_base64, detections = process_image(file_path)

        # Save the meal to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO meals (user_id, meal_date, meal_image, meal_items, tray_score)
        VALUES (?, ?, ?, ?, ?)
        ''', (session['user'], datetime.now(), img_base64, json.dumps(detections), compute_tray_score(detections)))
        conn.commit()
        conn.close()

        return jsonify({
            'image': f"data:image/jpeg;base64,{img_base64}",
            'detections': detections
        })
    except Exception as e:
        print(f"Error decoding image: {e}")  # Debugging
        return jsonify({'error': 'Failed to decode image'}), 400

@app.route('/gemini_detect', methods=['POST'])
@login_required
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
@login_required
def analyze_tray():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save the uploaded file
        file_path = os.path.join('static/uploads', file.filename)
        os.makedirs('static/uploads', exist_ok=True)
        file.save(file_path)
        
        try:
            # Process the image with Gemini
            img_base64, categorized_items = gemini.analyze_tray(file_path)
            
            # Identify food items using Gemini
            food_items = gemini.identify_food_items(categorized_items)
            
            # Get calorie information for each food item
            processed_food_items = []
            for item in food_items:
                calories_info = get_calories_for_food(item)
                if calories_info:
                    item_dict = {"name": item, "calories": calories_info}
                else:
                    item_dict = {"name": item, "calories": None}
                processed_food_items.append(item_dict)
            
            # Calculate total calories
            total_calories = sum(item["calories"]["calories"] if item["calories"] else 0 for item in processed_food_items)
            
            # Save the meal data to the database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create the meals table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                meal_date TEXT NOT NULL,
                meal_image TEXT NOT NULL,
                meal_items TEXT NOT NULL,
                tray_score REAL,
                total_calories INTEGER
            )
            ''')
            
            # Insert the meal data
            cursor.execute(
                "INSERT INTO meals (user_id, meal_date, meal_image, meal_items, tray_score, total_calories) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session['user'],
                    datetime.now().isoformat(),
                    img_base64,
                    json.dumps(processed_food_items),
                    None,  # Tray score (to be implemented later)
                    total_calories
                )
            )
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'image': f"data:image/jpeg;base64,{img_base64}",
                'categorized_items': categorized_items,
                'food_items': processed_food_items,
                'total_calories': total_calories
            })
            
        except Exception as e:
            print(f"Error in analyze_tray: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for('callback', _external=True)
    )

@app.route('/callback')
def callback():
    try:
        token = oauth.auth0.authorize_access_token()
        userinfo = token.get('userinfo')
        
        if not userinfo:
            # If userinfo is not in the token, try to get it from the userinfo endpoint
            userinfo_url = f"https://{os.getenv('AUTH0_DOMAIN')}/userinfo"
            resp = oauth.auth0.get(userinfo_url, token=token)
            userinfo = resp.json()
        
        # Store user info in session
        session['user'] = userinfo.get('email', userinfo.get('sub'))
        session['user_info'] = userinfo
        
        return redirect('/')
    except Exception as e:
        print(f"Error in callback: {e}")
        return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/meal_history')
@login_required
def meal_history():
    try:
        # Get meal history for the logged-in user
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM meals WHERE user_id = ? ORDER BY meal_date DESC",
            (session['user'],)
        )
        
        meals = []
        for row in cursor.fetchall():
            meal = dict(row)
            # Parse the JSON string of meal items
            meal['meal_items'] = json.loads(meal['meal_items'])
            meals.append(meal)
            
        conn.close()
        
        return render_template('meal_history.html', meals=meals, user=session.get('user'))
    except Exception as e:
        print(f"Error retrieving meal history: {e}")
        return render_template('meal_history.html', meals=[], user=session.get('user'), error="Could not retrieve meal history")

if __name__ == '__main__':
    app.run(debug=True)
