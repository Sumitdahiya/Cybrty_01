from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import logging
import os
from datetime import datetime
import uuid

# Import our CrewAI agents and tools
from agents.pentest_crew import PentestCrew
from tools import ToolManager
from models.ollama_manager import OllamaManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Guided Penetration Testing API",
    description="CrewAI-powered penetration testing with intelligent task sequencing",
    version="2.0.0"
)

# Global instances
pentest_crew = None
tool_manager = None
ollama_manager = None

# Pydantic models for API requests
class PentestRequest(BaseModel):
    target: str
    scope: str = "basic"
    test_type: str = "comprehensive"  # comprehensive, quick, specific
    specific_tools: Optional[List[str]] = None
    ai_guided: bool = True
    max_duration_minutes: int = 30

class ToolExecutionRequest(BaseModel):
    tool_name: str
    target: str
    parameters: Optional[Dict[str, Any]] = {}

class AgentTaskRequest(BaseModel):
    agent_role: str
    target: str
    task_description: str
    expected_outcome: str

# Store active pentest sessions
active_sessions = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global pentest_crew, tool_manager, ollama_manager
    
    try:
        logger.info("Initializing AI-Guided Penetration Testing API...")
        
        # Initialize tool manager
        tool_manager = ToolManager()
        logger.info(f"Tool Manager initialized with tools: {tool_manager.get_available_tools()}")
        
        # Initialize Ollama manager
        ollama_manager = OllamaManager()
        logger.info("Ollama Manager initialized")
        
        # Initialize CrewAI agents
        pentest_crew = PentestCrew()
        logger.info("CrewAI PentestCrew initialized with AI-guided task planning")
        
        logger.info("API startup complete - CrewAI agents ready for intelligent penetration testing")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Don't fail startup, allow basic functionality

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI-Guided Penetration Testing API",
        "version": "2.0.0",
        "features": [
            "CrewAI agent-based intelligent testing",
            "AI-guided task sequencing",
            "Dynamic tool selection",
            "MongoDB result storage",
            "Real-time progress tracking"
        ],
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global pentest_crew, tool_manager, ollama_manager
    
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check tool manager
    if tool_manager:
        available_tools = tool_manager.get_available_tools()
        health_status["services"]["tool_manager"] = {
            "status": "healthy",
            "available_tools": available_tools,
            "tool_count": len(available_tools)
        }
    else:
        health_status["services"]["tool_manager"] = {"status": "not_initialized"}
    
    # Check Ollama manager
    if ollama_manager:
        try:
            models = await ollama_manager.list_models()
            health_status["services"]["ollama"] = {
                "status": "healthy",
                "available_models": models,
                "current_model": ollama_manager.model_name
            }
        except Exception as e:
            health_status["services"]["ollama"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        health_status["services"]["ollama"] = {"status": "not_initialized"}
    
    # Check CrewAI agents
    if pentest_crew:
        try:
            stats = pentest_crew.get_database_stats()
            health_status["services"]["crewai_agents"] = {
                "status": "healthy",
                "mongodb_connected": pentest_crew.mongodb.is_connected(),
                "session_id": pentest_crew.session_id,
                "database_stats": stats
            }
        except Exception as e:
            health_status["services"]["crewai_agents"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        health_status["services"]["crewai_agents"] = {"status": "not_initialized"}
    
    # Check active sessions
    health_status["active_sessions"] = len(active_sessions)
    
    return health_status

@app.post("/invokePentest")
async def invoke_ai_guided_pentest(request: PentestRequest, background_tasks: BackgroundTasks):
    """
    Execute AI-guided penetration testing with CrewAI agents
    This endpoint uses intelligent agents to dynamically decide and sequence tasks
    """
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="CrewAI agents not initialized")
    
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting AI-guided pentest for target: {request.target}")
        
        # Store session info
        active_sessions[session_id] = {
            "target": request.target,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "test_type": request.test_type,
            "ai_guided": request.ai_guided
        }
        
        if request.ai_guided:
            # Execute full AI-guided penetration testing
            if request.test_type == "comprehensive":
                # Run comprehensive AI-guided pentest in background
                background_tasks.add_task(
                    execute_comprehensive_ai_pentest,
                    session_id,
                    request.target,
                    request.scope,
                    request.max_duration_minutes
                )
                
                return {
                    "message": "AI-guided comprehensive penetration test started",
                    "session_id": session_id,
                    "target": request.target,
                    "test_type": request.test_type,
                    "status": "running",
                    "ai_guidance": "Agents will dynamically select and sequence tasks based on AI analysis",
                    "progress_endpoint": f"/session/{session_id}/status",
                    "results_endpoint": f"/session/{session_id}/results"
                }
            
            elif request.test_type == "quick":
                # Execute quick AI-guided scan
                results = await execute_quick_ai_pentest(session_id, request.target, request.scope)
                active_sessions[session_id]["status"] = "completed"
                return results
                
        else:
            # Execute specific tools if provided
            if request.specific_tools:
                results = await execute_specific_tools(session_id, request.target, request.specific_tools)
                active_sessions[session_id]["status"] = "completed"
                return results
        
        # Default to quick AI-guided test
        results = await execute_quick_ai_pentest(session_id, request.target, request.scope)
        active_sessions[session_id]["status"] = "completed"
        return results
        
    except Exception as e:
        logger.error(f"Error in AI-guided pentest: {e}")
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "error"
            active_sessions[session_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Pentest execution failed: {str(e)}")

async def execute_comprehensive_ai_pentest(session_id: str, target: str, scope: str, max_duration: int):
    """Execute comprehensive AI-guided penetration testing"""
    global pentest_crew
    
    try:
        # Update session status
        active_sessions[session_id]["status"] = "running_comprehensive"
        
        # Execute full CrewAI-guided penetration test
        results = await pentest_crew.execute_pentest(
            target=target,
            scope=scope,
            additional_params={"max_duration_minutes": max_duration, "session_id": session_id}
        )
        
        # Store results
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["results"] = results
        active_sessions[session_id]["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Comprehensive AI-guided pentest completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error in comprehensive pentest {session_id}: {e}")
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["error"] = str(e)

async def execute_quick_ai_pentest(session_id: str, target: str, scope: str) -> Dict[str, Any]:
    """Execute quick AI-guided penetration testing (2-3 tools max)"""
    global pentest_crew
    
    try:
        results = {
            "session_id": session_id,
            "target": target,
            "test_type": "quick_ai_guided",
            "phases": {},
            "summary": {}
        }
        
        # Execute reconnaissance phase only with AI guidance
        logger.info(f"Starting quick AI-guided reconnaissance for {target}")
        recon_results = await pentest_crew.execute_ai_guided_phase(
            target, "Reconnaissance Specialist", "quick_reconnaissance", session_id
        )
        results["phases"]["reconnaissance"] = recon_results
        
        # Based on reconnaissance, let AI decide if vulnerability assessment is needed
        decision = pentest_crew.task_planner.decide_next_task(target, "Vulnerability Assessment Expert")
        
        if decision.get("priority") in ["high", "medium"]:
            logger.info(f"AI recommends vulnerability assessment: {decision.get('reasoning')}")
            vuln_results = await pentest_crew.execute_ai_guided_phase(
                target, "Vulnerability Assessment Expert", "quick_vulnerability", session_id
            )
            results["phases"]["vulnerability_assessment"] = vuln_results
        
        # Generate quick summary
        results["summary"] = pentest_crew.generate_pentest_summary(results, session_id)
        results["ai_guidance_used"] = True
        results["completed_at"] = datetime.utcnow().isoformat()
        
        return results
        
    except Exception as e:
        logger.error(f"Error in quick AI pentest: {e}")
        return {"error": str(e), "session_id": session_id}

async def execute_specific_tools(session_id: str, target: str, tools: List[str]) -> Dict[str, Any]:
    """Execute specific tools without AI guidance"""
    global pentest_crew
    
    results = {
        "session_id": session_id,
        "target": target,
        "test_type": "specific_tools",
        "tool_results": [],
        "summary": {}
    }
    
    for tool_name in tools:
        try:
            logger.info(f"Executing specific tool: {tool_name} on target: {target}")
            result = pentest_crew.execute_tool(tool_name, target)
            results["tool_results"].append({
                "tool": tool_name,
                "target": target,
                "output": result,
                "executed_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            results["tool_results"].append({
                "tool": tool_name,
                "target": target,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            })
    
    results["summary"] = {
        "tools_executed": len(tools),
        "successful_executions": len([r for r in results["tool_results"] if "error" not in r]),
        "completed_at": datetime.utcnow().isoformat()
    }
    
    return results

@app.post("/execute-tool")
async def execute_single_tool(request: ToolExecutionRequest):
    """Execute a single penetration testing tool"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="PentestCrew not initialized")
    
    try:
        logger.info(f"Executing tool: {request.tool_name} on target: {request.target}")
        result = pentest_crew.execute_tool(request.tool_name, request.target, **request.parameters)
        
        return {
            "tool": request.tool_name,
            "target": request.target,
            "parameters": request.parameters,
            "result": result,
            "executed_at": datetime.utcnow().isoformat(),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error executing tool {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.post("/ai-task-decision")
async def get_ai_task_decision(target: str, agent_role: str):
    """Get AI-guided task decision for a specific agent and target"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="PentestCrew not initialized")
    
    try:
        decision = pentest_crew.task_planner.decide_next_task(target, agent_role)
        
        return {
            "target": target,
            "agent_role": agent_role,
            "ai_decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI task decision: {e}")
        raise HTTPException(status_code=500, detail=f"AI decision failed: {str(e)}")

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get the status of a specific pentest session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_info = active_sessions[session_id].copy()
    
    # Add additional info from MongoDB if available
    if pentest_crew:
        try:
            session_summary = pentest_crew.get_session_summary(session_id)
            session_info["database_summary"] = session_summary
        except Exception as e:
            session_info["database_error"] = str(e)
    
    return session_info

@app.get("/session/{session_id}/results")
async def get_session_results(session_id: str):
    """Get the detailed results of a specific pentest session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_info = active_sessions[session_id]
    
    if session_info["status"] == "completed" and "results" in session_info:
        return session_info["results"]
    elif session_info["status"] == "error":
        return {"error": session_info.get("error", "Unknown error")}
    else:
        return {"message": "Session still running", "status": session_info["status"]}

@app.get("/tools/available")
async def list_available_tools():
    """List all available penetration testing tools"""
    global tool_manager
    
    if not tool_manager:
        raise HTTPException(status_code=503, detail="Tool manager not initialized")
    
    available_tools = tool_manager.get_available_tools()
    
    return {
        "available_tools": available_tools,
        "tool_count": len(available_tools),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/agents/status")
async def get_agents_status():
    """Get the status of all CrewAI agents"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="CrewAI agents not initialized")
    
    return {
        "session_id": pentest_crew.session_id,
        "agents": {
            "reconnaissance": "Reconnaissance Specialist",
            "vulnerability": "Vulnerability Assessment Expert", 
            "exploitation": "Exploitation Specialist",
            "reporting": "Security Report Analyst"
        },
        "ai_guidance_enabled": True,
        "mongodb_connected": pentest_crew.mongodb.is_connected(),
        "task_planner": "Active",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/database/stats")
async def get_database_statistics():
    """Get MongoDB database statistics"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="CrewAI agents not initialized")
    
    try:
        stats = pentest_crew.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/recent-results")
async def get_recent_results(limit: int = 10):
    """Get recent penetration testing results"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="CrewAI agents not initialized")
    
    try:
        results = pentest_crew.get_recent_pentest_results(limit=limit)
        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/agent-actions")
async def get_agent_actions(agent_role: Optional[str] = None, session_id: Optional[str] = None, limit: int = 50):
    """Get agent actions and decisions"""
    global pentest_crew
    
    if not pentest_crew:
        raise HTTPException(status_code=503, detail="CrewAI agents not initialized")
    
    try:
        actions = pentest_crew.get_agent_actions(agent_role=agent_role, session_id=session_id, limit=limit)
        return {
            "actions": actions,
            "count": len(actions),
            "filters": {
                "agent_role": agent_role,
                "session_id": session_id
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
