from django.test import TestCase

import requests

response = requests.patch('http://127.0.0.1:8000/api/payment/mark-invoice-as-successful/d7e7f482-bd9e-4812-a518-b64a6713b3be/')