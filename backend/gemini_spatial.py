import os
import json
from PIL import Image, ImageDraw, ImageFont
import base64
import io
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types

# Load environment variables
load_dotenv()

# Configure the Gemini API client
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# System instructions for bounding box detection
BOUNDING_BOX_SYSTEM_INSTRUCTIONS = """
Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 25 objects.
If an object is present multiple times, name them according to their unique characteristic (colors, size, position, unique characteristics, etc..).
"""

# Safety settings
SAFETY_SETTINGS = [
    types.SafetySettingDict(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]

class GeminiSpatial:
    def __init__(self):
        self.model_name = "gemini-2.0-flash"
    
    def detect_objects(self, image_path, prompt="Identify all objects in this image"):
        """
        Detect objects in an image using Gemini API
        
        Args:
            image_path: Path to the image file
            prompt: The prompt to send to Gemini
            
        Returns:
            Tuple of (annotated_image_base64, detection_results)
        """
        try:
            # Load the image
            img = Image.open(image_path)
            
            # Convert the image to RGB if it's not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create a copy for annotation
            annotated_img = img.copy()
            
            # Resize image if needed
            img.thumbnail([1024, 1024], Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            
            # Convert PIL Image to bytes for Gemini API
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # Add system instructions to the prompt
            full_prompt = BOUNDING_BOX_SYSTEM_INSTRUCTIONS + "\n\n" + prompt
            
            # Create Gemini model
            model = genai.GenerativeModel(model_name=self.model_name)
            
            # Generate content
            response = model.generate_content(
                contents=[
                    full_prompt,
                    {"mime_type": "image/jpeg", "data": img_bytes}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.5,
                ),
                safety_settings=SAFETY_SETTINGS
            )
            
            # Parse the response
            bounding_boxes = self._parse_json(response.text)
            
            # Draw bounding boxes on the image
            annotated_img = self._draw_bounding_boxes(annotated_img, bounding_boxes)
            
            # Convert the annotated image to base64
            buffered = io.BytesIO()
            annotated_img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return img_str, json.loads(bounding_boxes)
            
        except Exception as e:
            print(f"Error in detect_objects: {e}")
            return None, {"error": str(e)}
    
    def analyze_tray(self, image_path):
        """
        Analyze a lunch tray image and categorize items for disposal
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (annotated_image_base64, categorized_items)
        """
        prompt = """
        Analyze this lunch tray image. Identify all food items, containers, and utensils.
        For each item, determine which disposal category it belongs to:
        - Trash (non-recyclable items)
        - Recycling (plastic, metal, glass containers, apple sauce, Plastic utensils)
        - Compost (food waste, napkins, paper products)
        - Dish Return (reusable trays, plates, silverware, glass products)

        
        Return the results as a JSON array with these fields:
        - label: name of the item
        - category: disposal category (trash, recycling, compost, dish_return)
        - box_2d: bounding box coordinates [y1, x1, y2, x2] in normalized 0-1000 range
        """
        
        try:
            # Load the image
            img = Image.open(image_path)
            
            # Convert the image to RGB if it's not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create a copy for annotation
            annotated_img = img.copy()
            
            # Resize image if needed
            img.thumbnail([1024, 1024], Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            
            # Convert PIL Image to bytes for Gemini API
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            # Add system instructions to the prompt
            full_prompt = BOUNDING_BOX_SYSTEM_INSTRUCTIONS + "\n\n" + prompt
            
            # Create Gemini model
            model = genai.GenerativeModel(model_name=self.model_name)
            
            # Generate content
            response = model.generate_content(
                contents=[
                    full_prompt,
                    {"mime_type": "image/jpeg", "data": img_bytes}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.5,
                ),
                safety_settings=SAFETY_SETTINGS
            )
            
            # Parse the response
            bounding_boxes = self._parse_json(response.text)
            
            # Draw categorized bounding boxes on the image
            annotated_img = self._draw_categorized_boxes(annotated_img, bounding_boxes)
            
            # Convert the annotated image to base64
            buffered = io.BytesIO()
            annotated_img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return img_str, json.loads(bounding_boxes)
            
        except Exception as e:
            print(f"Error in analyze_tray: {e}")
            return None, {"error": str(e)}
    
    def _parse_json(self, json_output):
        """
        Parse JSON from the model response, handling potential formatting issues
        """
        # Parsing out the markdown fencing
        lines = json_output.splitlines()
        for i, line in enumerate(lines):
            if line == "```json":
                json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
                json_output = json_output.split("```")[0]  # Remove everything after the closing "```"
                break  # Exit the loop once "```json" is found
        
        # Ensure we have valid JSON
        try:
            json.loads(json_output)
            return json_output
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON using simple heuristics
            start_idx = json_output.find('[')
            end_idx = json_output.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = json_output[start_idx:end_idx]
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    pass
            
            # Return empty array as fallback
            return "[]"
    
    def _draw_bounding_boxes(self, img, bounding_boxes_json):
        """
        Draw bounding boxes on an image
        """
        # Define colors for bounding boxes
        colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple',
            'brown', 'gray', 'cyan', 'magenta', 'lime', 'navy', 'teal',
            'olive', 'coral', 'lavender', 'violet', 'gold', 'silver'
        ]
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Try to load a font, with fallback options
        try:
            font = ImageFont.truetype("Arial.ttf", 14)
        except IOError:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
            except IOError:
                font = ImageFont.load_default()
        
        # Parse the JSON
        try:
            bounding_boxes = json.loads(bounding_boxes_json)
            
            # Draw each bounding box
            for i, box in enumerate(bounding_boxes):
                color = colors[i % len(colors)]
                
                # Extract coordinates and normalize if needed
                if "box_2d" in box:
                    coords = box["box_2d"]
                    # Convert normalized coordinates (0-1000) to pixel values
                    y1 = int(coords[0] / 1000 * height)
                    x1 = int(coords[1] / 1000 * width)
                    y2 = int(coords[2] / 1000 * height)
                    x2 = int(coords[3] / 1000 * width)
                    
                    # Ensure coordinates are in the right order
                    if x1 > x2:
                        x1, x2 = x2, x1
                    if y1 > y2:
                        y1, y2 = y2, y1
                    
                    # Draw rectangle
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                    
                    # Draw label
                    if "label" in box:
                        label = box["label"]
                        # Get text size
                        if hasattr(font, 'getsize'):
                            text_width, text_height = font.getsize(label)
                        else:
                            # For newer Pillow versions
                            left, top, right, bottom = font.getbbox(label)
                            text_width, text_height = right - left, bottom - top
                        
                        # Draw text background
                        draw.rectangle([x1, y1 - text_height - 4, x1 + text_width + 4, y1], fill=color)
                        # Draw text
                        draw.text((x1 + 2, y1 - text_height - 2), label, fill="white", font=font)
            
            return img
        except Exception as e:
            print(f"Error drawing bounding boxes: {e}")
            return img
    
    def _draw_categorized_boxes(self, img, bounding_boxes_json):
        """
        Draw categorized bounding boxes on an image
        """
        # Define colors for different categories
        category_colors = {
            "trash": "red",
            "recycling": "blue",
            "compost": "green",
            "dish_return": "yellow"
        }
        
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Try to load a font, with fallback options
        try:
            font = ImageFont.truetype("Arial.ttf", 14)
        except IOError:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
            except IOError:
                font = ImageFont.load_default()
        
        # Parse the JSON
        try:
            bounding_boxes = json.loads(bounding_boxes_json)
            
            # Draw each bounding box
            for box in bounding_boxes:
                category = box.get("category", "unknown").lower()
                color = category_colors.get(category, "purple")
                
                # Extract coordinates and normalize if needed
                if "box_2d" in box:
                    coords = box["box_2d"]
                    # Convert normalized coordinates (0-1000) to pixel values
                    y1 = int(coords[0] / 1000 * height)
                    x1 = int(coords[1] / 1000 * width)
                    y2 = int(coords[2] / 1000 * height)
                    x2 = int(coords[3] / 1000 * width)
                    
                    # Ensure coordinates are in the right order
                    if x1 > x2:
                        x1, x2 = x2, x1
                    if y1 > y2:
                        y1, y2 = y2, y1
                    
                    # Draw rectangle
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                    
                    # Draw label with category
                    label = f"{box.get('label', 'Unknown')} ({category})"
                    # Get text size
                    if hasattr(font, 'getsize'):
                        text_width, text_height = font.getsize(label)
                    else:
                        # For newer Pillow versions
                        left, top, right, bottom = font.getbbox(label)
                        text_width, text_height = right - left, bottom - top
                    
                    # Draw text background
                    draw.rectangle([x1, y1 - text_height - 4, x1 + text_width + 4, y1], fill=color)
                    # Draw text
                    draw.text((x1 + 2, y1 - text_height - 2), label, fill="white", font=font)
            
            return img
        except Exception as e:
            print(f"Error drawing categorized boxes: {e}")
            return img
