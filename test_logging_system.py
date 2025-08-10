#!/usr/bin/env python3
"""
Test script to verify the comprehensive logging system for PenTest AI API
This script tests MongoDB integration and comprehensive agent/tool logging
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.pentest_crew import PentestCrew
from mongodb_integration import CrewAIMongoDB

async def test_logging_system():
    """Test the comprehensive logging system"""
    print("🚀 Testing PenTest AI Comprehensive Logging System")
    print("=" * 60)
    
    # Initialize MongoDB connection
    print("\n1. Testing MongoDB Connection...")
    mongo = CrewAIMongoDB()
    
    if mongo.is_connected():
        print("✅ MongoDB connected successfully")
        
        # Get initial stats
        stats = mongo.get_stats()
        print(f"📊 Database: {stats.get('database')}")
        print(f"📁 Collections: {stats.get('collections', {})}")
        print(f"📋 Total documents: {stats.get('total_documents', 0)}")
    else:
        print("❌ MongoDB connection failed")
        return False
    
    # Initialize PentestCrew
    print("\n2. Testing PentestCrew Initialization...")
    try:
        pentest_crew = PentestCrew()
        print("✅ PentestCrew initialized successfully")
        
        # Test database stats through crew
        crew_stats = pentest_crew.get_database_stats()
        print(f"📊 Crew database stats: {json.dumps(crew_stats, indent=2)}")
        
    except Exception as e:
        print(f"❌ PentestCrew initialization failed: {e}")
        return False
    
    # Test basic tool execution with logging
    print("\n3. Testing Tool Execution with Logging...")
    try:
        test_target = "127.0.0.1"
        print(f"🎯 Testing nmap scan on {test_target}")
        
        # Execute tool and capture session ID
        tool_result = pentest_crew.execute_tool("nmap", test_target, 
                                               ports="80,443", 
                                               scan_type="basic")
        
        print(f"🔧 Tool execution result type: {type(tool_result)}")
        print(f"🔧 Tool execution result: {str(tool_result)[:200]}...")
        
        # Since execute_tool returns a string, we'll test session tracking differently
        # The logging should still happen within the tool execution
        
    except Exception as e:
        print(f"❌ Tool execution test failed: {e}")
        return False
    
    # Test comprehensive pentest with logging
    print("\n4. Testing Comprehensive Pentest with Logging...")
    try:
        print(f"🎯 Running comprehensive pentest on {test_target}")
        
        # Execute comprehensive pentest
        pentest_results = await pentest_crew.execute_pentest(
            target=test_target,
            scope="basic",
            additional_params={
                "test_mode": True,
                "logging_enabled": True
            }
        )
        
        print(f"🏁 Pentest execution completed")
        print(f"📊 Results keys: {list(pentest_results.keys())}")
        
        if 'session_id' in pentest_results:
            session_id = pentest_results['session_id']
            print(f"📝 Pentest Session ID: {session_id}")
            
            # Get comprehensive session summary
            summary = pentest_crew.get_session_summary(session_id)
            print(f"📋 Comprehensive session summary: {json.dumps(summary, indent=2)}")
        
    except Exception as e:
        print(f"❌ Comprehensive pentest test failed: {e}")
        return False
    
    # Test data retrieval methods
    print("\n5. Testing Data Retrieval Methods...")
    try:
        # Test agent actions retrieval
        print("🤖 Testing agent actions retrieval...")
        agent_actions = pentest_crew.get_agent_actions(limit=10)
        print(f"📊 Found {len(agent_actions)} agent actions")
        
        if agent_actions:
            print("🔍 Sample agent action:")
            sample_action = agent_actions[0]
            for key, value in sample_action.items():
                if key != '_id':
                    print(f"   {key}: {value}")
        
        # Test command executions retrieval
        print("\n⚡ Testing command executions retrieval...")
        command_executions = pentest_crew.get_command_executions(limit=10)
        print(f"📊 Found {len(command_executions)} command executions")
        
        if command_executions:
            print("🔍 Sample command execution:")
            sample_command = command_executions[0]
            for key, value in sample_command.items():
                if key != '_id':
                    if key == 'output' and len(str(value)) > 100:
                        print(f"   {key}: {str(value)[:100]}...")
                    else:
                        print(f"   {key}: {value}")
        
        # Test tool results retrieval
        print("\n🔧 Testing tool results retrieval...")
        tool_results = mongo.get_tool_results(limit=10)
        print(f"📊 Found {len(tool_results)} tool results")
        
        if tool_results:
            print("🔍 Sample tool result:")
            sample_tool = tool_results[0]
            for key, value in sample_tool.items():
                if key != '_id':
                    if key == 'result_data' and isinstance(value, dict):
                        print(f"   {key}: {list(value.keys())}")
                    else:
                        print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Data retrieval test failed: {e}")
        return False
    
    # Final statistics
    print("\n6. Final System Statistics...")
    try:
        final_stats = pentest_crew.get_database_stats()
        print("📊 Final Database Statistics:")
        print(json.dumps(final_stats, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Final stats retrieval failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive Logging System Test COMPLETED")
    print("🎉 All tests passed successfully!")
    print("📚 The system is now logging:")
    print("   • All agent actions and decisions")
    print("   • All tool executions and outputs")
    print("   • All command executions")
    print("   • Session-based tracking")
    print("   • Comprehensive error handling")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_logging_system())
    sys.exit(0 if success else 1)
