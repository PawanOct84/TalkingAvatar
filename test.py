import requests
import time
from threading import Timer

API_URL = "http://localhost:8000/service_request/"

def test_service_request():
    # Replace the following with appropriate data for your API
    data = {
        "modelid": 1,
        "text": "Sample text",
        "language": "en",
        "email": "test@example.com"
    }

    response = requests.post(API_URL, json=data)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

def timer_handler():
    test_service_request()
    Timer(30, timer_handler).start()

# Call the timer_handler function to start the timer
timer_handler()
