# Trayce: The Tray Waste Sorter

A smart waste-sorting assistant that uses computer vision to identify and classify food tray contents into trash, recycle, compost, or dish return — making disposal effortless and eco-friendly.

## Features

- Real-time object detection using YOLOv11, the latest version of YOLO
- Webcam integration for live detection using Gemini 2.0
- Image upload functionality for analyzing static images
- Focused detection of food and dining-related items
- Configurable confidence threshold for detections

## Technologies Used

### Frontend
- React: A JavaScript library for building user interfaces.
- TypeScript: A strongly typed superset of JavaScript.
- React Router: For navigation and routing between pages.
- Tailwind CSS: For styling components with utility-first CSS classes.
- Axios: For making HTTP requests to the backend.

### Backend
- Flask: A Python web framework for building the backend API.
- YOLO (Ultralytics): For object detection and classification.
- OpenCV for image processing and webcam access

## Getting Started

### Prerequisites

- Node.js 16.0+: Required for running the frontend.
- Python 3.8+: Required for running the backend.
- Package Managers:
   - npm or yarn for the frontend.
   - pip for the backend.

### Installation

1. Clone the repository and open it locally:
   ```
   git clone https://github.com/F4llow/trayce.git
   cd trayce
   ```

2. Open the `backend` folder and install the required packages inside of a virtual environment:
   ```
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Add a environment file named `.env` and assign your Gemini API key to `GEMINI_API_KEY.`

4. Run the application's backend:
   ```
   python3 app.py
   ```
   
5. Open the `frontend` folder and install the required dependences:
   ```
   cd frontend
   npm install
   ```
   
6. Run app:
   ```
   npm run dev
   ```

## Usage

### Computer Vision Scanner
- Click on the "Start Scanning" button to start the webcam.

### Webcam Detection
- Make sure that the webcam is under good lighting and that all items are clearly visible.
- Click on the "Capture Image" button to take a picture of your tray.

### Results Analysis
- View your tray analysis as an image labeled by Gemini AI object identification.
- Click the "View All Items" button to view the full list of identified objects, sorted by category. 
- Click the "Scan Again" button to restart the process.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini's API for computer vision 
