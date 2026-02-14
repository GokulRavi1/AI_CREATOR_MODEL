
import requests
import json
import traceback

url = "http://127.0.0.1:8000/api/studio/generate"
payload = {
    "prompt": "Test prompt",
    "negative_prompt": "Test negative",
    "width": 512,
    "height": 512,
    "steps": 25,
    "cfg_scale": 7.0,
    "checkpoint": "Realistic_Vision_V6.0_NV_B1_fp16.safetensors",
    "lora_name": "",
    "lora_strength": 0.8,
    "seed": -1,
    "use_hires_fix": False,
    "controlnet_enabled": False,
    "controlnet_name": "controlnet-canny-sdxl-1.0",
    "control_image_name": ""
}

try:
    print(f"Sending POST to {url} with payload: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print("Request failed:")
    traceback.print_exc()
