#!/usr/bin/env python3
"""
API Verification Script - Demonstrates the working PenTest AI API
"""

import requests
import json
import sys
from time import sleep

API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test basic API health"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API Health: PASS")
            return True
        else:
            print(f"❌ API Health: FAIL ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health: FAIL - {e}")
        return False

def test_model_status():
    """Test model status endpoint"""
    print("\n🔍 Testing Model Status...")
    try:
        response = requests.get(f"{API_BASE_URL}/models/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Model Status: PASS")
            print(f"   - Ollama Installed: {data.get('ollama_installed', 'Unknown')}")
            print(f"   - Service Running: {data.get('service_running', 'Unknown')}")
            print(f"   - Model Available: {data.get('model_available', 'Unknown')}")
            print(f"   - Model Name: {data.get('model_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Model Status: FAIL ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Model Status: FAIL - {e}")
        return False

def test_pentest_endpoint():
    """Test the main penetration testing endpoint"""
    print("\n🔍 Testing Penetration Testing Endpoint...")
    try:
        payload = {
            "target": "demo.testfire.net",
            "scope": "basic",
            "additional_params": {
                "test_mode": True
            }
        }
        
        print(f"   📤 Sending request to {API_BASE_URL}/invokePentest")
        print(f"   📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE_URL}/invokePentest",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Pentest Endpoint: PASS")
            print(f"   📊 Status: {data.get('status', 'Unknown')}")
            
            results = data.get('results', {})
            print(f"   🎯 Target: {results.get('target', 'Unknown')}")
            print(f"   📈 Scope: {results.get('scope', 'Unknown')}")
            print(f"   🔄 Execution Status: {results.get('status', 'Unknown')}")
            print(f"   🤖 LLM Status: {results.get('llm_status', 'Unknown')}")
            
            if 'note' in results:
                print(f"   📝 Note: {results['note']}")
            
            # Show findings summary
            findings = results.get('findings', {})
            if findings:
                print("   📋 Findings Summary:")
                for category, finding in findings.items():
                    print(f"      • {category.title()}: {finding}")
            
            return True
        else:
            print(f"❌ Pentest Endpoint: FAIL ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Pentest Endpoint: FAIL - {e}")
        return False

def test_api_documentation():
    """Test API documentation accessibility"""
    print("\n🔍 Testing API Documentation...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API Documentation: PASS")
            print(f"   🌐 Available at: {API_BASE_URL}/docs")
            return True
        else:
            print(f"❌ API Documentation: FAIL ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Documentation: FAIL - {e}")
        return False

def main():
    """Run all API verification tests"""
    print("🚀 PenTest AI API Verification")
    print("=" * 50)
    
    tests = [
        ("API Health", test_api_health),
        ("Model Status", test_model_status), 
        ("Pentest Endpoint", test_pentest_endpoint),
        ("API Documentation", test_api_documentation)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your PenTest AI API is working correctly!")
        print(f"\n🌐 API Documentation: {API_BASE_URL}/docs")
        print("🔧 To enable full AI features, install Ollama (see OLLAMA_INSTALLATION.md)")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("Check the API server status and try again.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
