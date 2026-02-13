import requests

url = "http://127.0.0.1:8000/api/discovery/body"
data = {
    "character_name": "test_char_verification",
    # No control_image_name
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
