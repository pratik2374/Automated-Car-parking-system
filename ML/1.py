import torch
import numpy as np
from ultralytics import YOLO
import cv2
from PIL import Image
import os
import time 

# Load the YOLO model
model = YOLO("../best_5.pt")
print("YOLO Loaded")
channel_id = '2675528'  # Your Channel ID
write_api_key = '6E1YHXAOC34GZRZB'
classes_of_interest = ["Car", "Van", "Truck", "Bus", "Motorcycle", "Bicycle"]
vehicle_found = 0
image_index = 1
png_path = f"{image_index}.png"
jpeg_path = f"{image_index}.jpeg"
if os.path.exists(png_path):
    image_path = png_path
elif os.path.exists(jpeg_path):
    image_path = jpeg_path
else:
    print(f"No image found for index {image_index}")
    exit()
results = model.predict(image_path)
result = results[0]
boxes = result.boxes.xyxy.cpu().numpy()
class_indices = result.boxes.cls.cpu().numpy()
labels = result.names
for j in range(len(boxes)):
    label_index = int(class_indices[j])
    label = labels[label_index]

    # If a detected object is a vehicle, set vehicle_found to 1
    if label in classes_of_interest:
        vehicle_found = 1
        break  # Exit the loop since a vehicle is found

if vehicle_found == 1:
    print("Vehicle detected in the image.")
else:
    print("No vehicle detected in the image.")

import requests
import time



# URL for sending data to ThingSpeak
url = f'https://api.thingspeak.com/update?api_key={write_api_key}&field1={vehicle_found}'

# Sending data to ThingSpeak in a loop
while True:
    response = requests.get(url)

    if response.status_code == 200:
        print(f"Data sent successfully: {vehicle_found}")
    else:
        print(f"Error sending data: {response.status_code}")

    time.sleep(10)  # Wait for 10 seconds before sending the next value

