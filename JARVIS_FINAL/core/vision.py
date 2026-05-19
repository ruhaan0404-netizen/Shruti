import ollama
import cv2
import pyautogui
import os
from datetime import datetime

# Setup a temporary directory for JARVIS's visual "short-term memory"
TEMP_DIR = "jarvis_memory_images"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def get_timestamped_path(prefix):
    return os.path.join(TEMP_DIR, f"{prefix}_{datetime.now().strftime('%H%M%S')}.png")

def capture_screen():
    """Captures the current desktop view."""
    path = get_timestamped_path("screenshot")
    screenshot = pyautogui.screenshot()
    screenshot.save(path)
    return path

def capture_webcam():
    """Captures a frame from the primary webcam."""
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if not ret:
        cam.release()
        return None
    
    path = get_timestamped_path("webcam")
    cv2.imwrite(path, frame)
    cam.release()
    return path

def analyze_image(image_path, user_query):
    """
    Sends the captured image to the local Llava model via Ollama.
    """
    if not image_path or not os.path.exists(image_path):
        return "Error: Image not found or capture failed."
        
    try:
        with open(image_path, 'rb') as img_file:
            response = ollama.generate(
                model='llava', 
                prompt=user_query,
                images=[img_file.read()]
            )
        return response['response']
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def vision_tool_controller(command):
    command_lower = command.lower()
    
    if "screenshot" in command_lower or "screen" in command_lower:
        img_path = capture_screen()
        description = analyze_image(img_path, "Describe this screen briefly.")
        return description
        
    elif "webcam" in command_lower or "look at me" in command_lower or "camera" in command_lower:
        img_path = capture_webcam()
        if not img_path:
            return "Failed to access webcam."
        description = analyze_image(img_path, "What do you see through the camera?")
        return description
    
    return "I'm sorry, I couldn't access the visual input."
