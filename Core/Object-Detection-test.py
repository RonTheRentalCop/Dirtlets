import time
import cv2 as cv
from ultralytics import YOLO


model = YOLO("yolov8n.pt")


def detect_objects(frame):
    """Placeholder for the future YOLO object detection call."""
    results = model(frame, verbose=False)
    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            label = model.names[class_id]
            detections.append({
                "label": label,
                "confidence": confidence,
                "box": (int(x1), int(y1), int(x2), int(y2))
            })
    return detections


camera = cv.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    success, frame = camera.read()
    if not success:
        break

    detected_objects = detect_objects(frame)

    for obj in detected_objects:
        x1, y1, x2, y2 = obj["box"]
        label = obj["label"]
        confidence = obj["confidence"]
        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (33, 172, 227, 0.169), 2)

    cv.imshow("Camera Feed", frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Relase the camerea and boom the window
camera.release()
cv.destroyAllWindows()

# The Big steps of this program 

# Open CV needs to read the system
# Yolo needs to do his job and detect the objects
# Then Blah blag blah the program generates the next step for the robot to move
# Comnand needs to be sent 

#Possibly add a speaker to the drone so he can get MAD when things are in the way 
# Have him hit things in range if they don't move ONLY when I make rage mode

def loudspeakaer():
    if detected_objects(person):
        # Play sound on speaker Alien! Alien! Alien!
        # If there are detected objects, make the drone angry
        print("Detected objects! Drone is angry!")
        # Add logic to make the drone angry here`
    # Don't know what the code will look like yet maybe use TTS
    pass
# This function will be called when the drone is in rage mode

# Rage mode
def Rage_Mode():
    # This function will be called when the drone is in rage mode
    # It will make the drone aggressive and hit objects in its path

    # Add logic to make the drone hit objects here
    pass