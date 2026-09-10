import time
import cv2 as cv


camera = cv.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    success, frame = camera.read()
    if not success:
        break

    detected_objects = detect_objects(frame)

    cv.imshow("Camera Feed", frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Relase the camerea and boom the window
camera.release()
cv.destroyAllWindows()

# Put this in a loop that continuously checks for detected objects and makes the car drive forward or stop and turn based on the detection results.
def detect_objects(frame):
    if detected_objects is None:
        #Call Function that does not exist yet to make car drive forward
        return []
    elif detected_objects is not None:
        detected_objects = []  # Placeholder for detected objects
        # Call Function that does not exist yet to make car stop and turn
        return detected_objects

# The Big steps of this program 

# Open CV needs to read the system
# Yolo needs to do his job and detect the objects
# Then Blah blag blah the program generates the next step for the robot to move
# Comnand needs to be sent 

#Possibly add a speaker to the drone so he can get MAD when things are in the way 
# Have him hit things in range if they don't move ONLY when I make rage mode

def loudspeakaer():
    # Don't know what the code will look like yet maybe use TTS
# This function will be called when the drone is in rage mode

# Rage mode
def rage_mode():
    if detected_objects is not None:
        print("RAGE. This Dirtlet is Mad ASF")
        # Have the drone hit the objects. Maybe increase speed but first make it run an enviornmental check
        # Cap the bvehicle speed to a certin metric for the safty of the solder and electronics inside
        

        # Call Function that does not exist yet to make car stop and turn
        return detected_objects
    # This function will be called when the drone is in rage mode
    # It will make the drone aggressive and hit objects in its path

    # Add logic to make the drone hit objects here