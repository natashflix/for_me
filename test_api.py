#!/usr/bin/env python3
"""
API endpoints testing for FOR ME bot
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8080"


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("TEST: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Status code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=True)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Server not running!")
        print("   Start server: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_root():
    """Test root endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Root Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Status code: {response.status_code}")
        data = response.json()
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Endpoints:")
        for name, desc in data.get('endpoints', {}).items():
            print(f"     - {name}: {desc}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_basic():
    """Test basic chat endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Chat Endpoint (basic)")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={
                "Content-Type": "application/json",
                "X-User-Id": "test_user_001"
            },
            json={
                "message": "Hello! This is a test message."
            },
            timeout=10
        )
        
        print(f"✅ Status code: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"   Status: {data.get('status')}")
            print(f"   Intent: {data.get('intent')}")
            reply = data.get('reply', '')
            print(f"   Reply: {reply[:200]}...")
            return True
        else:
            print(f"   Error: {data.get('detail', 'Unknown error')}")
            if "api_key" in str(data.get('detail', '')).lower():
                print("   ⚠️  GOOGLE_API_KEY required")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_with_ingredients():
    """Test chat endpoint with ingredients"""
    print("\n" + "=" * 60)
    print("TEST: Chat Endpoint (with ingredients)")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            headers={
                "Content-Type": "application/json",
                "X-User-Id": "test_user_002"
            },
            json={
                "message": "Analyze this shampoo",
                "ingredient_text": "AQUA, SODIUM LAURETH SULFATE, GLYCERIN, FRAGRANCE",
                "product_domain": "cosmetics"
            },
            timeout=10
        )
        
        print(f"✅ Status code: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"   Status: {data.get('status')}")
            print(f"   Intent: {data.get('intent')}")
            if data.get('for_me_score') is not None:
                print(f"   FOR ME Score: {data.get('for_me_score')}")
            if data.get('scores'):
                scores = data.get('scores', {})
                print(f"   Safety: {scores.get('safety')}")
                print(f"   Sensitivity: {scores.get('sensitivity')}")
                print(f"   Match: {scores.get('match')}")
            reply = data.get('reply', '')
            print(f"   Reply: {reply[:200]}...")
            return True
        else:
            print(f"   Error: {data.get('detail', 'Unknown error')}")
            if "api_key" in str(data.get('detail', '')).lower():
                print("   ⚠️  GOOGLE_API_KEY required")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analyze_endpoint():
    """Test analyze endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Analyze Endpoint")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            headers={"Content-Type": "application/json"},
            json={
                "user_id": "test_user_003",
                "ingredient_text": "Sugar, cocoa butter, cocoa paste, milk",
                "product_domain": "food"
            },
            timeout=10
        )
        
        print(f"✅ Status code: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"   Status: {data.get('status')}")
            if data.get('for_me_score') is not None:
                print(f"   FOR ME Score: {data.get('for_me_score')}")
            return True
        else:
            print(f"   Error: {data.get('detail', 'Unknown error')}")
            if "api_key" in str(data.get('detail', '')).lower():
                print("   ⚠️  GOOGLE_API_KEY required")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "🌐 FOR ME API ENDPOINTS TESTING" + "\n")
    
    print("Checking if server is running...")
    time.sleep(1)
    
    results = []
    
    # Test 1: Health
    results.append(test_health())
    
    if not results[0]:
        print("\n❌ Server not running. Start server:")
        print("   python main.py")
        return 1
    
    # Test 2: Root
    results.append(test_root())
    
    # Test 3: Chat basic
    results.append(test_chat_basic())
    
    # Test 4: Chat with ingredients
    results.append(test_chat_with_ingredients())
    
    # Test 5: Analyze
    results.append(test_analyze_endpoint())
    
    # Summary
    print("\n" + "=" * 60)
    print("API TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed < total:
        print("\n💡 For full testing, set GOOGLE_API_KEY:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("   Get key: https://aistudio.google.com/app/api-keys")
    
    if passed == total:
        print("\n🎉 All API tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
