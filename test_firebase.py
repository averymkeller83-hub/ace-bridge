import urllib.request
import json

url = "https://ace-bridge-commands-default-rtdb.firebaseio.com/commands.json"

print("Connecting to Firebase...")
try:
    response = urllib.request.urlopen(url, timeout=5)
    data = json.loads(response.read().decode())
    print("Success!")
    print(data)
except Exception as e:
    print("Error:", e)
