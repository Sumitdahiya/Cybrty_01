#!/usr/bin/env python3
"""
MongoDB Data Viewer for CrewAI

View and manage data stored in MongoDB
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mongodb_integration import CrewAIMongoDB
import json
from datetime import datetime

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_json(data, title=""):
    if title:
        print(f"\n📄 {title}:")
    print(json.dumps(data, indent=2, default=str))

def main():
    print("🔍 CrewAI MongoDB Data Viewer")
    
    try:
        mongo = CrewAIMongoDB()
        
        # Show statistics
        print_header("SYSTEM STATISTICS")
        stats = mongo.get_agent_stats()
        print_json(stats, "Current Statistics")
        
        # Show agents
        print_header("AI AGENTS")
        agents = mongo.list_agents()
        for i, agent in enumerate(agents, 1):
            print(f"\n🤖 Agent #{i}")
            print(f"   ID: {agent['_id']}")
            print(f"   Role: {agent['role']}")
            print(f"   Goal: {agent['goal']}")
            print(f"   Tools: {agent.get('tools', 'None')}")
            print(f"   Created: {agent.get('created_at', 'Unknown')}")
        
        # Show missions
        print_header("MISSIONS")
        missions = mongo.list_missions()
        for i, mission in enumerate(missions, 1):
            print(f"\n🚀 Mission #{i}")
            print(f"   ID: {mission['_id']}")
            print(f"   Name: {mission['name']}")
            print(f"   Status: {mission.get('status', 'Unknown')}")
            print(f"   Target: {mission.get('target', 'Not specified')}")
            print(f"   Created: {mission.get('created_at', 'Unknown')}")
        
        # Show tool results
        print_header("TOOL RESULTS")
        tool_results = mongo.get_tool_results()
        for i, result in enumerate(tool_results, 1):
            print(f"\n🔧 Tool Result #{i}")
            print(f"   ID: {result['_id']}")
            print(f"   Tool: {result['tool']}")
            print(f"   Target: {result['target']}")
            print(f"   Timestamp: {result['timestamp']}")
            if 'result' in result and 'parsed_data' in result['result']:
                parsed = result['result']['parsed_data']
                if 'shares' in parsed:
                    print(f"   SMB Shares: {len(parsed['shares'])} found")
                if 'users' in parsed:
                    print(f"   Users: {len(parsed['users'])} found")
        
        # Show recent pentest results
        print_header("PENETRATION TEST RESULTS")
        pentest_results = mongo.get_pentest_results()
        if pentest_results:
            for i, result in enumerate(pentest_results[:5], 1):  # Show last 5
                print(f"\n🔒 Pentest Result #{i}")
                print(f"   ID: {result['_id']}")
                print(f"   Target: {result.get('target', 'Unknown')}")
                print(f"   Timestamp: {result['timestamp']}")
        else:
            print("\n📝 No penetration test results found")
        
        print_header("DATA EXPORT")
        print("You can export data using MongoDB Compass or mongosh:")
        print("mongosh mongodb://localhost:27017/crewai_pentest")
        print("db.agents.find().pretty()")
        print("db.tool_results.find().pretty()")
        
        mongo.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
