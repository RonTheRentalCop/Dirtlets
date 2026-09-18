from ast import While
import random
import time
import network
import espnow

# Data goes in through esp 32 or hosted offline network
# I need all the data to transmit to the other robots so an inital robot can be made leader to preform the caluclation

#Question: How much does it really matter the amount of computing that the boards do?


def recive_data():
    # Placeholder for receiving data from the ESP-NOW network
    # This function should be implemented to receive actual data
    return random.choice(["Disconnected", "Weak", "Good", "Excellent"])



# Very simple score to start

#Lets try to add the position movmenet and other things assossicated


# What would the leader do besides this? should I move them in squads?

def battery_status():
    if battery_level < 20:
        return "Low Battery"
    elif battery_level < 50:
        return "Medium Battery"
    elif battery_level < 80:
        return "Good Battery"
    else:
        return "High"

def network_score():
    score = 0
    if network_status == "Disconnected":
        score -= 30
    elif network_status == "Weak":
        score -= 10
    elif network_status == "Good":
        score += 10
    else:
        score += 20

def Esp_Now():
    score = 0
    if esp_now_status == "Disconnected":
        score -= 30
    elif esp_now_status == "Weak":
        score -= 10
    elif esp_now_status == "Good":
        score += 10
    else:
        score += 20

def health_score():
    score = 0
    score += battery_status()
    score += network_score()
    score += Esp_Now()
    return score

def selection():
    score = health_score()
    if score < 0:
        return "Critical"
    elif score < 20:
        return "Poor"
    elif score < 50:
        return "Fair"
    elif score < 80:
        return "Good"
    else:
        return "Excellent"

#Write the main block to put it together
if __name__ == "__main__":
    while True:
        battery_level = random.randint(0, 100)  # Simulate battery level
        network_status = recive_data()  # Simulate network status
        esp_now_status = recive_data()  # Simulate ESP-NOW status

        score = health_score()
        status = selection()

        print(f"Battery Level: {battery_level}%")
        print(f"Network Status: {network_status}")
        print(f"ESP-NOW Status: {esp_now_status}")
        print(f"Health Score: {score}")
        print(f"Overall Status: {status}")
        print("-" * 30)

        time.sleep(5)  # Wait for 5 seconds before the next check

# Now put the spoofed input stuff in

# Put all the other garbage down here
