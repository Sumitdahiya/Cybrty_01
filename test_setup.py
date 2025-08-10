#!/usr/bin/env python3
"""
Test script for the PenTest AI API
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

async def test_ollama_manager():
    """Test the Ollama manager functionality"""
    print("Testing Ollama Manager...")
    
    try:
        from models.ollama_manager import OllamaManager
        
        manager = OllamaManager()
        status = await manager.get_model_status()
        
        print(f"Model Status: {json.dumps(status, indent=2)}")
        
        if status.get('model_available'):
            print("✅ Deepseek model is available")
        else:
            print("⚠️  Deepseek model not available")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Ollama Manager: {e}")
        return False

async def test_pentest_crew():
    """Test the PenTest crew creation"""
    print("\nTesting PenTest Crew...")
    
    try:
        from agents.pentest_crew import PentestCrew
        
        crew = PentestCrew()
        print("✅ PenTest crew created successfully")
        print(f"Available agents: {list(crew.agents.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PenTest Crew: {e}")
        return False

async def test_api_imports():
    """Test API imports"""
    print("\nTesting API imports...")
    
    try:
        from main import app
        print("✅ FastAPI app imported successfully")
        
        # Test basic endpoint creation
        if hasattr(app, 'routes'):
            routes = [route.path for route in app.routes if hasattr(route, 'path')]
            print(f"Available routes: {routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API imports: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting PenTest AI API Tests\n")
    
    tests = [
        test_api_imports,
        test_ollama_manager,
        test_pentest_crew,
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print(f"\n📊 Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All tests passed! The API is ready to use.")
        print("\n🌟 Next steps:")
        print("1. Run: python start.py (to start with auto-setup)")
        print("2. Or run: uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("3. Open: http://localhost:8000/docs for API documentation")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
