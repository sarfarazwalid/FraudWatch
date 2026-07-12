"""
Test registration via HTTP request.
"""
import requests
import json

url = "http://localhost:8000/api/v1/auth/register"

payload = {
    "email": "test@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
}

print("=" * 80)
print("TESTING REGISTRATION VIA HTTP")
print("=" * 80)
print(f"\nURL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 201:
        print("\n✓ SUCCESS: Registration completed successfully!")
    else:
        print(f"\n✗ FAILED: HTTP {response.status_code}")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
