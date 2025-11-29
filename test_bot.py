#!/usr/bin/env python3
"""
Simple test script for FOR ME bot functionality
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.system import ForMeSystem


async def test_health_check():
    """Test: system initialization check"""
    print("=" * 60)
    print("TEST 1: System Initialization")
    print("=" * 60)
    
    try:
        system = ForMeSystem(use_persistent_storage=False)
        print("✅ System initialized successfully")
        print(f"   - Model: {system.model_name}")
        print(f"   - Storage: {'In-Memory' if not system.use_persistent_storage else 'Database'}")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


async def test_chat_basic():
    """Test: basic chat request"""
    print("\n" + "=" * 60)
    print("TEST 2: Basic Chat Request")
    print("=" * 60)
    
    try:
        system = ForMeSystem(use_persistent_storage=False)
        
        result = await system.handle_chat_request(
            user_id="test_user_001",
            message="Hello! This is a test message.",
        )
        
        print("✅ Request processed")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Intent: {result.get('intent')}")
        print(f"   - Reply: {result.get('reply', '')[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Request processing error: {e}")
        if "api_key" in str(e).lower() or "api key" in str(e).lower():
            print("   ⚠️  GOOGLE_API_KEY required for full testing")
            print("   💡 Set: export GOOGLE_API_KEY='your-key-here'")
        return False


async def test_product_analysis():
    """Test: product analysis"""
    print("\n" + "=" * 60)
    print("TEST 3: Product Analysis (Cosmetics)")
    print("=" * 60)
    
    try:
        system = ForMeSystem(use_persistent_storage=False)
        
        result = await system.handle_chat_request(
            user_id="test_user_001",
            message="Analyze this shampoo",
            ingredient_text="AQUA, SODIUM LAURETH SULFATE, GLYCERIN, FRAGRANCE, PARFUM",
            product_domain="cosmetics",
        )
        
        print("✅ Analysis completed")
        print(f"   - Status: {result.get('status')}")
        print(f"   - FOR ME Score: {result.get('for_me_score', 'N/A')}")
        if result.get('scores'):
            scores = result.get('scores', {})
            print(f"   - Safety Score: {scores.get('safety', 'N/A')}")
            print(f"   - Sensitivity Score: {scores.get('sensitivity', 'N/A')}")
            print(f"   - Match Score: {scores.get('match', 'N/A')}")
        print(f"   - Reply: {result.get('reply', '')[:150]}...")
        return True
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        if "api_key" in str(e).lower() or "api key" in str(e).lower():
            print("   ⚠️  GOOGLE_API_KEY required for full testing")
        return False


async def test_food_analysis():
    """Test: food analysis"""
    print("\n" + "=" * 60)
    print("TEST 4: Product Analysis (Food)")
    print("=" * 60)
    
    try:
        system = ForMeSystem(use_persistent_storage=False)
        
        result = await system.handle_chat_request(
            user_id="test_user_002",
            message="Can I eat this?",
            ingredient_text="Sugar, cocoa butter, cocoa paste, dried milk, hazelnut",
            product_domain="food",
        )
        
        print("✅ Analysis completed")
        print(f"   - Status: {result.get('status')}")
        print(f"   - FOR ME Score: {result.get('for_me_score', 'N/A')}")
        print(f"   - Reply: {result.get('reply', '')[:150]}...")
        return True
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        if "api_key" in str(e).lower() or "api key" in str(e).lower():
            print("   ⚠️  GOOGLE_API_KEY required for full testing")
        return False


async def main():
    """Run all tests"""
    print("\n" + "🚀 FOR ME BOT TEST SUITE" + "\n")
    
    # Check API key
    has_api_key = bool(os.getenv("GOOGLE_API_KEY"))
    if not has_api_key:
        print("⚠️  WARNING: GOOGLE_API_KEY not set")
        print("   Some tests may not complete fully")
        print("   Set: export GOOGLE_API_KEY='your-key-here'\n")
    else:
        print("✅ GOOGLE_API_KEY found\n")
    
    results = []
    
    # Test 1: Initialization
    results.append(await test_health_check())
    
    # Test 2: Basic chat
    if has_api_key:
        results.append(await test_chat_basic())
    
    # Test 3: Cosmetics analysis
    if has_api_key:
        results.append(await test_product_analysis())
    
    # Test 4: Food analysis
    if has_api_key:
        results.append(await test_food_analysis())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if not has_api_key:
        print("\n💡 For full testing, set GOOGLE_API_KEY:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("   Get key: https://aistudio.google.com/app/api-keys")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
