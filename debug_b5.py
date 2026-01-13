import requests
import json

try:
    response = requests.get("http://localhost:8000/api/practice/B5_Fill%20blanks_Audio")
    data = response.json()
    if data['data']:
        print("Keys:", list(data['data'][0].keys()))
        print("First Item:", json.dumps(data['data'][0], indent=2))
    else:
        print("No data found")
except Exception as e:
    print(e)
