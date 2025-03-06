from flask import Flask, render_template, jsonify
from datetime import datetime
import requests
import time
import cv2
from ultralytics import YOLO
import pytesseract
import os  # Import os for file handling
import time
# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the YOLO model for vehicle detection
model = YOLO("best_5.pt")

# Load the YOLO model for license plate detection
model2 = YOLO("License.pt")

app = Flask(__name__)

# ThingSpeak details
write_api_key = "Q6I6HTVETTRCP7QO"
read_api_key = "OX2LVBJ9SB25SZA2"
channel_id = '2685441'

# Classes of interest for vehicles
classes_of_interest = ["Car", "Van", "Truck", "Bus", "Motorcycle", "Bicycle"]

def send_yolo_detection(vehicle_detected):
    url = f"https://api.thingspeak.com/update?api_key={write_api_key}&field1={int(vehicle_detected)}"
    response = requests.get(url)
    if response.status_code == 200:
        print("Data sent to ThingSpeak successfully")
    else:
        print(f"Error sending data to ThingSpeak: {response.content}")

def read_parking_slot():
    url = f"https://api.thingspeak.com/channels/{channel_id}/fields/2.json?api_key={read_api_key}&results=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        field_value = data['feeds'][0]['field2']
        return field_value
    else:
        print(f"Error reading data from ThingSpeak: {response.content}")
        return None

def load_image(image_index):
    # Attempt to load the image with .jpg extension
    jpg_path = f"{image_index}.jpg"
    if os.path.exists(jpg_path):
        return jpg_path
    
    # If .jpg not found, check for .jpeg
    jpeg_path = f"{image_index}.jpeg"
    if os.path.exists(jpeg_path):
        return jpeg_path
    png_path = f"{image_index}.png"
    if os.path.exists(png_path):
        return png_path


    return None  # Return None if neither image exists

def process_yolo(image_path, image_index):
    results = model.predict(image_path,device="cuda")
    result = results[0]
    vehicle_detected = False
    boxes = result.boxes.xyxy.cpu().numpy()
    class_indices = result.boxes.cls.cpu().numpy()
    labels = result.names

    for j in range(len(boxes)):
        label_index = int(class_indices[j])
        label = labels[label_index]

        if label in classes_of_interest:
            vehicle_detected = True
            print("For", image_index, "image vehicle detected:", vehicle_detected)
            print("For", image_index, "detecting license plate")
            
            # Use the license plate detection model
            results_l = model2.predict(image_path, device='cuda')  # Use 'cuda' for GPU
            detected_plates = []  # List to hold detected license plate numbers

            # Load the image using OpenCV
            image = cv2.imread(image_path)

            # Extract the bounding boxes and labels from the results
            for result in results_l:
                for box in result.boxes:
                    # Get the coordinates of the bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Crop the bounding box from the image for OCR
                    roi = image[y1:y2, x1:x2]

                    # Perform OCR on the cropped image
                    text = pytesseract.image_to_string(roi, config='--psm 6')
                    text = text.strip()  # Clean up the extracted text
                    if text:  # Only add non-empty results
                        detected_plates.append(text)
                        print(f"Detected text: {text}")

            # Return vehicle detection status and the first detected plate, if any
            return vehicle_detected, detected_plates[0] if detected_plates else None

    return vehicle_detected, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_images', methods=['GET'])
def process_images():
    license_plate_data = []
    
    for image_index in range(1, 6):  # Loop through 5 images
        image_path = load_image(image_index)  # Get the image path
        if image_path is None:
            print(f"Image {image_index} not found in either .jpg or .jpeg format.")
            continue  # Skip to the next iteration if no image is found

        vehicle_detected, license_plate = process_yolo(image_path, image_index)
        send_yolo_detection(vehicle_detected)
  
        # Wait for Wokwi to send the parking slot data to ThingSpeak
        time.sleep(10)

        parking_slot = read_parking_slot()
      
        print("For", image_index, "image slot detected:", parking_slot)


        if vehicle_detected:
            current_time=time.time()
            formatted_time = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
            license_plate_data.append({'license_plate': license_plate, 'slot': parking_slot,'time':formatted_time})

    print(license_plate_data)
    return jsonify(license_plate_data)

if __name__ == '__main__':
    app.run(debug=True)
