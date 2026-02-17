import requests
import sys

try:
    print("Testing backend connection...")
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"✓ Backend is responding!")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    sys.exit(0)
except requests.exceptions.Timeout:
    print("✗ Backend timeout - server is not responding")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ Connection refused - backend is not running on port 8000")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
