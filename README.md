# Trayce - Lunch Tray Sorter

A smart waste-sorting assistant that uses computer vision (Google's Gemini API) to identify and classify food tray contents into trash, recycle, compost, or dish return — making disposal effortless and eco-friendly.

## Features

- Real-time object detection using YOLOv11, the latest version of YOLO
- Webcam integration for live detection
- Image upload functionality for analyzing static images
- Focused detection of food and dining-related items
- Configurable confidence threshold for detections

## Technologies Used

- YOLOv11 from Ultralytics for object detection
- Flask for the web application backend
- OpenCV for image processing and webcam access
- HTML, CSS, and JavaScript for the frontend

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Webcam (for live detection)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/F4llow/trayce.git
   cd trayce
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

### Webcam Detection
- Select the "Webcam" tab to use your webcam for real-time object detection.

### Image Upload
- Select the "Upload Image" tab.
- Click on the upload area to select an image or drag and drop an image.
- Click "Upload and Detect" to process the image.
- View the list of recyclable objects. 

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini's API for computer vision 
