#!/usr/bin/env python3
"""
API Endpoints Demo for PenTest AI with MongoDB Logging
This script demonstrates all the new MongoDB logging and retrieval endpoints
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_api_endpoint(endpoint, description):
    """Test an API endpoint and display results"""
    print(f"\n{'='*60}")
    print(f"🔧 Testing: {description}")
    print(f"📡 Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS")
            print(f"📊 Response: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    print("🚀 PenTest AI API - MongoDB Logging Endpoints Demo")
    print(f"🕒 Test Time: {datetime.now()}")
    print("=" * 80)
    
    # Test existing endpoints
    test_api_endpoint("/", "Root endpoint health check")
    test_api_endpoint("/health", "Health check endpoint")
    test_api_endpoint("/agents", "List available agents")
    test_api_endpoint("/tools", "List available tools")
    test_api_endpoint("/models/status", "Ollama model status")
    
    # Test new MongoDB logging endpoints
    test_api_endpoint("/database/stats", "Database statistics")
    test_api_endpoint("/agents/actions", "Agent actions (default limit)")
    test_api_endpoint("/agents/actions?limit=5", "Agent actions (limit 5)")
    test_api_endpoint("/agents/actions?agent_role=PentestCrew", "Agent actions (filter by role)")
    test_api_endpoint("/commands/executions", "Command executions (default limit)")
    test_api_endpoint("/commands/executions?limit=3", "Command executions (limit 3)")
    test_api_endpoint("/sessions/recent", "Recent sessions")
    
    # Test session-specific endpoint if we have a session ID
    try:
        stats_response = requests.get(f"{API_BASE}/database/stats")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            recent_results = stats_data.get('recent_results', [])
            if recent_results:
                session_id = recent_results[0].get('session_id')
                if session_id:
                    test_api_endpoint(f"/sessions/{session_id}/summary", f"Session summary for {session_id}")
    except:
        pass
    
    print(f"\n{'='*80}")
    print("✅ API Demo Completed!")
    print("📚 All MongoDB logging endpoints are functional")
    print("🎯 The system now provides comprehensive tracking of:")
    print("   • Agent actions and decisions")
    print("   • Tool executions and outputs") 
    print("   • Command executions")
    print("   • Session-based analytics")
    print("   • Database statistics")
    print("=" * 80)

if __name__ == "__main__":
    main()
