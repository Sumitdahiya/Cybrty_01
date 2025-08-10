from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import uvicorn
import os
from agents.pentest_crew import PentestCrew
from models.ollama_manager import OllamaManager
from tools import ToolManager
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from azure_config import azure_config, configure_azure_logging, get_azure_health_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Azure logging if available
configure_azure_logging()

app = FastAPI(
    title="PenTest AI API - Azure Deployment",
    description="FastAPI application with CrewAI agents for penetration testing using Ollama Deepseek model - Optimized for Azure App Service",
    version="2.0.0"
)

# Configure CORS for Azure
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.azurewebsites.net"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Configure trusted hosts for Azure
if azure_config.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.azurewebsites.net", "localhost"]
    )

class PentestRequest(BaseModel):
    target: str
    scope: str = "basic"
    agents: Optional[List[str]] = None  # Specify which agents to invoke
    tools: Optional[List[str]] = None   # Specify which tools to use
    additional_params: Dict[str, Any] = {}

class PentestResponse(BaseModel):
    status: str
    message: str
    results: Dict[str, Any] = {}

class AgentInfo(BaseModel):
    name: str
    role: str
    description: str

class ToolInfo(BaseModel):
    name: str
    description: str
    available: bool

@app.on_event("startup")
async def startup_event():
    """Initialize Ollama and download Deepseek model on startup"""
    logger.info("🚀 Starting up PenTest AI API on Azure...")
    
    # Log Azure configuration
    azure_health = get_azure_health_info()
    logger.info(f"Azure Configuration: {azure_health}")
    
    try:
        # Initialize Ollama with Azure configuration
        ollama_host = azure_config.get_ollama_host()
        logger.info(f"Connecting to Ollama at: {ollama_host}")
        
        ollama_manager = OllamaManager()
        model_available = await ollama_manager.ensure_model_available()
        
        if model_available:
            logger.info("✅ Startup completed successfully with Ollama integration")
        else:
            logger.warning("⚠️ Ollama model not available, proceeding with limited functionality")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        logger.info("The API will work with basic functionality. Install Ollama manually for full AI features.")

@app.get("/")
async def root():
    """Root endpoint with Azure deployment information"""
    return {
        "message": "PenTest AI API is running on Azure",
        "status": "healthy",
        "version": "2.0.0",
        "environment": azure_config.get_all_config()["environment"],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for Azure monitoring"""
    try:
        # Get Azure-specific health information
        azure_health = get_azure_health_info()
        
        # Check tool availability
        tool_manager = ToolManager()
        available_tools = tool_manager.get_available_tools()
        
        health_status = {
            "status": "healthy",
            "timestamp": "2025-01-06T12:00:00Z",
            "version": "2.0.0",
            "azure": azure_health,
            "tools": {
                "available": len(available_tools),
                "tools": available_tools
            },
            "database": {
                "mongodb_configured": azure_health["services"]["mongodb"]["configured"]
            },
            "ai_service": {
                "ollama_host": azure_health["services"]["ollama"]["host"]
            }
        }
        
        return health_status
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": "2025-01-06T12:00:00Z"
        }

@app.get("/agents", response_model=List[AgentInfo])
async def get_available_agents():
    """Get list of available penetration testing agents"""
    agents = [
        AgentInfo(
            name="recon",
            role="Reconnaissance Specialist", 
            description="Performs comprehensive reconnaissance using nmap, enum4linux, and nikto"
        ),
        AgentInfo(
            name="vulnerability",
            role="Vulnerability Assessment Expert",
            description="Identifies vulnerabilities using sqlmap, OWASP ZAP, Burp Suite, and nikto"
        ),
        AgentInfo(
            name="exploitation", 
            role="Exploitation Specialist",
            description="Performs controlled exploitation using Metasploit, Hydra, and John the Ripper"
        ),
        AgentInfo(
            name="reporting",
            role="Security Report Analyst", 
            description="Generates comprehensive security reports from tool outputs"
        )
    ]
    return agents

@app.get("/tools", response_model=List[ToolInfo])
async def get_available_tools():
    """Get list of available penetration testing tools"""
    try:
        tool_manager = ToolManager()
        available_tools = tool_manager.get_available_tools()
        
        tool_descriptions = {
            'nmap': 'Network discovery and security auditing',
            'burp': 'Web application security testing',
            'zap': 'OWASP ZAP web application security scanner',
            'sqlmap': 'Automatic SQL injection and database takeover tool',
            'nikto': 'Web server vulnerability scanner',
            'hydra': 'Password brute-forcing tool',
            'enum4linux': 'SMB/NetBIOS enumeration tool',
            'john': 'John the Ripper password cracking tool',
            'wireshark': 'Network packet analyzer',
            'metasploit': 'Penetration testing framework'
        }
        
        tools = []
        for tool_name in available_tools:
            tools.append(ToolInfo(
                name=tool_name,
                description=tool_descriptions.get(tool_name, f"{tool_name} penetration testing tool"),
                available=True  # All tools have fallback implementations
            ))
        
        return tools
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, target: str, options: Dict[str, Any] = {}):
    """Execute a specific penetration testing tool"""
    try:
        pentest_crew = PentestCrew()
        result = pentest_crew.execute_tool(tool_name, target, **options)
        
        return {
            "status": "success",
            "tool": tool_name,
            "target": target,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")

@app.post("/invokePentest", response_model=PentestResponse)
async def invoke_pentest(request: PentestRequest):
    """
    Invoke CrewAI agents for penetration testing with selective agent invocation
    
    Args:
        request: PentestRequest containing target, scope, and agent/tool selection
    
    Returns:
        PentestResponse with results from the selected penetration testing agents
    """
    try:
        logger.info(f"Starting pentest for target: {request.target}")
        logger.info(f"Selected agents: {request.agents}")
        logger.info(f"Selected tools: {request.tools}")
        
        # Initialize the pentest crew
        pentest_crew = PentestCrew()
        
        # If specific tools are requested, execute them directly
        if request.tools:
            tool_results = {}
            for tool_name in request.tools:
                logger.info(f"Executing tool: {tool_name}")
                tool_result = pentest_crew.execute_tool(tool_name, request.target, **request.additional_params)
                tool_results[tool_name] = tool_result
            
            return PentestResponse(
                status="success",
                message=f"Tool execution completed for {len(request.tools)} tools",
                results={
                    "target": request.target,
                    "scope": request.scope,
                    "selected_tools": request.tools,
                    "tool_results": tool_results,
                    "execution_type": "tools_only"
                }
            )
        
        # Execute the penetration testing workflow with selected agents
        results = await pentest_crew.execute_pentest(
            target=request.target,
            scope=request.scope,
            additional_params={
                **request.additional_params,
                "selected_agents": request.agents,
                "available_tools": pentest_crew.get_available_tools()
            }
        )
        
        logger.info("Pentest completed successfully")
        
        return PentestResponse(
            status="success",
            message="Penetration testing completed successfully",
            results={
                **results,
                "selected_agents": request.agents,
                "available_tools": pentest_crew.get_available_tools()
            }
        )
        
    except Exception as e:
        logger.error(f"Error during pentest execution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute penetration test: {str(e)}"
        )

@app.get("/models/status")
async def get_model_status():
    """Check the status of the Ollama Deepseek model"""
    try:
        ollama_manager = OllamaManager()
        status = await ollama_manager.get_model_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model status: {str(e)}"
        )

@app.get("/database/stats")
async def get_database_stats():
    """Get MongoDB database statistics"""
    try:
        pentest_crew = PentestCrew()
        stats = pentest_crew.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}"
        )

@app.get("/agents/actions")
async def get_agent_actions(
    agent_role: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50
):
    """Get agent actions and decisions from MongoDB"""
    try:
        pentest_crew = PentestCrew()
        actions = pentest_crew.get_agent_actions(
            agent_role=agent_role,
            session_id=session_id,
            limit=limit
        )
        return {
            "agent_actions": actions,
            "total_count": len(actions),
            "filters": {
                "agent_role": agent_role,
                "session_id": session_id,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent actions: {str(e)}"
        )

@app.get("/commands/executions")
async def get_command_executions(limit: int = 50):
    """Get command executions and their outputs"""
    try:
        pentest_crew = PentestCrew()
        executions = pentest_crew.get_command_executions(limit=limit)
        return {
            "command_executions": executions,
            "total_count": len(executions),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get command executions: {str(e)}"
        )

@app.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get a comprehensive summary of a specific pentest session"""
    try:
        pentest_crew = PentestCrew()
        summary = pentest_crew.get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session summary: {str(e)}"
        )

@app.post("/ai-guided-pentest")
async def ai_guided_pentest(request: PentestRequest):
    """Execute AI-guided penetration testing where agents decide their next tasks based on model guidance"""
    try:
        logger.info(f"Starting AI-guided penetration test for target: {request.target}")
        
        pentest_crew = PentestCrew()
        
        # Execute AI-guided penetration testing
        results = await pentest_crew.execute_pentest(
            target=request.target,
            scope=request.scope,
            additional_params=request.additional_params
        )
        
        return PentestResponse(
            status="completed",
            message=f"AI-guided penetration testing completed for {request.target}",
            results=results
        )
        
    except Exception as e:
        logger.error(f"AI-guided pentest failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"AI-guided penetration testing failed: {str(e)}"
        )

@app.get("/ai-guidance/next-task/{target}")
async def get_next_ai_task(target: str, agent_role: str = "Reconnaissance Specialist"):
    """Get AI-guided task recommendation for a specific agent and target"""
    try:
        pentest_crew = PentestCrew()
        
        # Get AI-powered task recommendation
        decision = pentest_crew.task_planner.decide_next_task(target, agent_role)
        
        return {
            "target": target,
            "agent_role": agent_role,
            "ai_decision": decision,
            "timestamp": decision.get("timestamp", ""),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI task guidance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI task guidance: {str(e)}"
        )

@app.get("/ai-guidance/analysis/{target}")
async def get_ai_analysis(target: str):
    """Get AI analysis of current penetration testing state"""
    try:
        pentest_crew = PentestCrew()
        
        # Get current state analysis
        current_state = pentest_crew.task_planner.analyze_current_state(target)
        
        return {
            "target": target,
            "current_state": current_state,
            "analysis": {
                "tools_completed": len(current_state.get("completed_tools", [])),
                "vulnerabilities_found": len(current_state.get("vulnerabilities", [])),
                "findings_count": len(current_state.get("findings", [])),
                "completion_percentage": min(len(current_state.get("completed_tools", [])) * 10, 100)
            },
            "recommendations": current_state.get("next_recommendations", []),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI analysis: {str(e)}"
        )

@app.post("/ai-guided-phase")
async def execute_ai_guided_phase(request: dict):
    """Execute a single AI-guided penetration testing phase"""
    try:
        target = request.get("target")
        agent_role = request.get("agent_role", "Reconnaissance Specialist")
        phase_name = request.get("phase_name", "reconnaissance")
        
        if not target:
            raise HTTPException(status_code=400, detail="Target is required")
        
        logger.info(f"Starting AI-guided {phase_name} phase for target: {target}")
        
        pentest_crew = PentestCrew()
        
        # Execute AI-guided phase
        phase_results = await pentest_crew.execute_ai_guided_phase(
            target=target,
            agent_role=agent_role,
            phase_name=phase_name,
            session_id=pentest_crew.session_id
        )
        
        return {
            "status": "completed",
            "target": target,
            "phase": phase_name,
            "agent": agent_role,
            "results": phase_results,
            "session_id": pentest_crew.session_id
        }
        
    except Exception as e:
        logger.error(f"AI-guided phase execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"AI-guided phase execution failed: {str(e)}"
        )

@app.get("/ai-agents/available")
async def get_available_ai_agents():
    """Get list of available AI agents and their capabilities"""
    try:
        return {
            "agents": [
                {
                    "role": "Reconnaissance Specialist",
                    "description": "Gathers comprehensive information about target systems using tools like nmap, enum4linux, and nikto",
                    "capabilities": ["network_scanning", "service_identification", "information_gathering"],
                    "primary_tools": ["nmap", "nikto", "enum4linux"]
                },
                {
                    "role": "Vulnerability Assessment Expert", 
                    "description": "Identifies and analyzes security vulnerabilities using specialized tools",
                    "capabilities": ["vulnerability_scanning", "web_app_testing", "risk_assessment"],
                    "primary_tools": ["sqlmap", "zap", "burp", "nikto"]
                },
                {
                    "role": "Exploitation Specialist",
                    "description": "Safely demonstrates and validates identified vulnerabilities",
                    "capabilities": ["exploitation", "privilege_escalation", "proof_of_concept"],
                    "primary_tools": ["metasploit", "hydra", "john"]
                },
                {
                    "role": "Security Report Analyst",
                    "description": "Generates comprehensive and actionable security reports",
                    "capabilities": ["report_generation", "risk_analysis", "recommendations"],
                    "primary_tools": ["analysis", "reporting", "documentation"]
                }
            ],
            "ai_guidance_enabled": True,
            "model_backend": "ollama_deepseek"
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI agents info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI agents info: {str(e)}"
        )

@app.get("/sessions/recent")
async def get_recent_sessions(limit: int = 10):
    """Get recent penetration testing sessions"""
    try:
        pentest_crew = PentestCrew()
        # Get recent pentest results to extract session IDs
        db_stats = pentest_crew.get_database_stats()
        recent_results = db_stats.get('recent_results', [])
        
        sessions = []
        for result in recent_results[:limit]:
            session_id = result.get('session_id')
            if session_id:
                summary = pentest_crew.get_session_summary(session_id)
                sessions.append(summary)
        
        return {
            "recent_sessions": sessions,
            "total_found": len(sessions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent sessions: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
