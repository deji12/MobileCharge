from django.test import TestCase

import requests

response = requests.post('http://127.0.0.1:8000/api/payment/cancel-subscription/')
print(response.status_code)  # Check the status code

if response.status_code == 200:
    print(response.json())  # Try to parse the JSON if status code is 200 (OK)
else:
    print("Error:", response.text)  # Print the raw response for debugging
