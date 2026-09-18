import random
import time
import network
import espnow


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
