from ultralytics import YOLO
import cv2
import pytesseract

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the YOLO model
model = YOLO("License.pt")

def predict_license_plate(path_test_car):
    # Perform prediction on the test image using the model on GPU
    results = model.predict(path_test_car, device='cuda')  # Use 'cuda' for GPU

    # List to hold detected license plate numbers
    detected_plates = []

    # Load the image using OpenCV
    image = cv2.imread(path_test_car)

    # Extract the bounding boxes and labels from the results
    for result in results:
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

    return detected_plates  # Return the list of detected license plate numbers

# Example usage
license_plates = predict_license_plate("1.jpg")
print("Detected License Plates:", license_plates)
