#!/usr/bin/env python3
"""
MongoDB Integration for CrewAI Penetration Testing

Provides MongoDB connectivity and data management for CrewAI pentest results
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import json
from bson import ObjectId

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    print("⚠️  PyMongo not installed. MongoDB features will be disabled.")
    print("   Install with: pip install pymongo")

class CrewAIMongoDB:
    """MongoDB integration for CrewAI penetration testing results"""
    
    def __init__(self, connection_string: str = None, database_name: str = "crewai_pentest"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string (defaults to localhost)
            database_name: Database name to use
        """
        self.database_name = database_name
        self.connection_string = connection_string or "mongodb://localhost:27017/"
        self.client = None
        self.db = None
        self.connected = False
        
        if PYMONGO_AVAILABLE:
            self._connect()
        else:
            print("⚠️  MongoDB integration disabled - PyMongo not available")
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.connected = True
            print(f"✅ Connected to MongoDB: {self.database_name}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print("   Make sure MongoDB is running on localhost:27017")
            self.connected = False
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if MongoDB connection is active"""
        return self.connected and PYMONGO_AVAILABLE
    
    def store_pentest_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        """
        Store penetration test results in MongoDB
        
        Args:
            result_data: Dictionary containing pentest results
            
        Returns:
            ObjectId string if successful, None if failed
        """
        if not self.is_connected():
            print("⚠️  MongoDB not connected - cannot store results")
            return None
        
        try:
            # Add metadata
            document = {
                **result_data,
                "stored_at": datetime.utcnow(),
                "collection_type": "pentest_results",
                "version": "1.0"
            }
            
            # Insert into pentest_results collection
            collection = self.db.pentest_results
            result = collection.insert_one(document)
            
            print(f"💾 Pentest results stored in MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error storing pentest results: {e}")
            return None
    
    def store_tool_result(self, tool_name: str, target: str, result_data: Dict[str, Any]) -> Optional[str]:
        """
        Store individual tool results in MongoDB
        
        Args:
            tool_name: Name of the penetration testing tool
            target: Target that was scanned
            result_data: Tool execution results
            
        Returns:
            ObjectId string if successful, None if failed
        """
        if not self.is_connected():
            print("⚠️  MongoDB not connected - cannot store tool results")
            return None
        
        try:
            # Add metadata
            document = {
                "tool_name": tool_name,
                "target": target,
                "result_data": result_data,
                "executed_at": datetime.utcnow(),
                "collection_type": "tool_results",
                "version": "1.0"
            }
            
            # Insert into tool_results collection
            collection = self.db.tool_results
            result = collection.insert_one(document)
            
            print(f"💾 Tool results ({tool_name}) stored in MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error storing tool results: {e}")
            return None
    
    def store_agent_action(self, agent_role: str, action_type: str, action_data: Dict[str, Any], pentest_session_id: Optional[str] = None) -> Optional[str]:
        """
        Store agent actions and commands in MongoDB
        
        Args:
            agent_role: Role of the agent (e.g., 'Reconnaissance Specialist')
            action_type: Type of action (e.g., 'task_start', 'tool_execution', 'thinking', 'task_complete')
            action_data: Detailed action data including commands, thoughts, outputs
            pentest_session_id: Associated pentest session ID for grouping
            
        Returns:
            ObjectId string if successful, None if failed
        """
        if not self.is_connected():
            print("⚠️  MongoDB not connected - cannot store agent actions")
            return None
        
        try:
            # Add metadata
            document = {
                "agent_role": agent_role,
                "action_type": action_type,
                "action_data": action_data,
                "pentest_session_id": pentest_session_id,
                "timestamp": datetime.utcnow(),
                "collection_type": "agent_actions",
                "version": "1.0"
            }
            
            # Insert into agent_actions collection
            collection = self.db.agent_actions
            result = collection.insert_one(document)
            
            print(f"📝 Agent action ({agent_role} - {action_type}) stored in MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error storing agent action: {e}")
            return None
    
    def store_command_execution(self, command: str, output: str, success: bool, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Store command executions and their outputs
        
        Args:
            command: The command that was executed
            output: Output from the command
            success: Whether the command executed successfully
            context: Additional context (agent, tool, session, etc.)
            
        Returns:
            ObjectId string if successful, None if failed
        """
        if not self.is_connected():
            print("⚠️  MongoDB not connected - cannot store command execution")
            return None
        
        try:
            # Add metadata
            document = {
                "command": command,
                "output": output,
                "success": success,
                "context": context or {},
                "executed_at": datetime.utcnow(),
                "collection_type": "command_executions",
                "version": "1.0"
            }
            
            # Insert into command_executions collection
            collection = self.db.command_executions
            result = collection.insert_one(document)
            
            print(f"⚡ Command execution stored in MongoDB: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error storing command execution: {e}")
            return None
    
    def get_pentest_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent penetration test results
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of pentest result documents
        """
        if not self.is_connected():
            return []
        
        try:
            collection = self.db.pentest_results
            results = list(collection.find().sort("stored_at", -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                if "stored_at" in result:
                    result["stored_at"] = result["stored_at"].isoformat()
            
            return results
            
        except Exception as e:
            print(f"❌ Error retrieving pentest results: {e}")
            return []
    
    def get_tool_results(self, tool_name: Optional[str] = None, target: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tool execution results
        
        Args:
            tool_name: Filter by specific tool name
            target: Filter by specific target
            limit: Maximum number of results to return
            
        Returns:
            List of tool result documents
        """
        if not self.is_connected():
            return []
        
        try:
            collection = self.db.tool_results
            query = {}
            
            if tool_name:
                query["tool_name"] = tool_name
            if target:
                query["target"] = target
            
            results = list(collection.find(query).sort("executed_at", -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                if "executed_at" in result:
                    result["executed_at"] = result["executed_at"].isoformat()
            
            return results
            
        except Exception as e:
            print(f"❌ Error retrieving tool results: {e}")
            return []
    
    def get_agent_actions(self, agent_role: Optional[str] = None, pentest_session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve agent actions and commands
        
        Args:
            agent_role: Filter by specific agent role
            pentest_session_id: Filter by specific pentest session
            limit: Maximum number of results to return
            
        Returns:
            List of agent action documents
        """
        if not self.is_connected():
            return []
        
        try:
            collection = self.db.agent_actions
            query = {}
            
            if agent_role:
                query["agent_role"] = agent_role
            if pentest_session_id:
                query["pentest_session_id"] = pentest_session_id
            
            results = list(collection.find(query).sort("timestamp", -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                if "timestamp" in result:
                    result["timestamp"] = result["timestamp"].isoformat()
            
            return results
            
        except Exception as e:
            print(f"❌ Error retrieving agent actions: {e}")
            return []
    
    def get_command_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve command executions
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of command execution documents
        """
        if not self.is_connected():
            return []
        
        try:
            collection = self.db.command_executions
            results = list(collection.find().sort("executed_at", -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                if "executed_at" in result:
                    result["executed_at"] = result["executed_at"].isoformat()
            
            return results
            
        except Exception as e:
            print(f"❌ Error retrieving command executions: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with collection counts and other stats
        """
        if not self.is_connected():
            return {"error": "Not connected to MongoDB"}
        
        try:
            stats = {
                "database": self.database_name,
                "connected": True,
                "collections": {},
                "total_documents": 0
            }
            
            # Get collection stats
            for collection_name in ["pentest_results", "tool_results"]:
                if collection_name in self.db.list_collection_names():
                    count = self.db[collection_name].count_documents({})
                    stats["collections"][collection_name] = count
                    stats["total_documents"] += count
                else:
                    stats["collections"][collection_name] = 0
            
            return stats
            
        except Exception as e:
            return {"error": f"Error getting stats: {e}"}
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            print("🔌 MongoDB connection closed")

# Utility function for easy pentest result storage
def store_pentest_result_to_mongodb(result_data: Dict[str, Any]) -> Optional[str]:
    """
    Convenience function to store pentest results to MongoDB
    
    Args:
        result_data: Penetration test results dictionary
        
    Returns:
        ObjectId string if successful, None if failed
    """
    mongo = CrewAIMongoDB()
    if mongo.is_connected():
        return mongo.store_pentest_result(result_data)
    return None