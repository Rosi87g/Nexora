# test_local.py
import requests
import json

API_KEY = "ne-a-5a4e7ec8678f497bb753f44c1a82aee1-a432178396f40341a4b6aea5"

def test_models_list():
    print("🔍 Testing models list...")
    response = requests.get(
        "http://127.0.0.1:8000/v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Found {len(response.json()['data'])} models\n")

def test_chat():
    print("💬 Testing chat completion...")
    response = requests.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "nexora-1.0",
            "messages": [
                {"role": "user", "content": "What is Python Programming? Explain in detail."}
            ],
            "temperature": 0.7,
            "max_tokens": 90
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Model: {result['model']}")
        print(f"✅ Response: {result['choices'][0]['message']['content']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_models_list()
    test_chat()