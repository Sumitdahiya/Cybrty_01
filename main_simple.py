from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import uvicorn
import os
from models.ollama_manager import OllamaManager
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Guided Penetration Testing Platform",
    description="An intelligent platform for automated penetration testing and security assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ScanRequest(BaseModel):
    target: str
    scan_type: str = "basic"
    options: Dict[str, Any] = {}

class TaskRequest(BaseModel):
    task_type: str
    target: str
    parameters: Dict[str, Any] = {}

class ScanResult(BaseModel):
    scan_id: str
    target: str
    status: str
    results: Dict[str, Any]
    timestamp: str

# Initialize managers
ollama_manager = OllamaManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if essential tools are available
        tools_status = {
            "nmap": check_tool_availability("nmap"),
            "nikto": check_tool_availability("nikto"),
            "sqlmap": check_tool_availability("sqlmap"),
            "hydra": check_tool_availability("hydra")
        }
        
        # Check Ollama connection
        ollama_status = await ollama_manager.health_check()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "version": "1.0.0",
                "services": {
                    "ollama": ollama_status,
                    "tools": tools_status
                },
                "message": "AI-Guided Penetration Testing Platform is running"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "message": "Service is not ready"
            }
        )

def check_tool_availability(tool_name: str) -> bool:
    """Check if a penetration testing tool is available"""
    try:
        result = subprocess.run([tool_name, "--version"], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        try:
            # Try alternative version check
            result = subprocess.run([tool_name, "-h"], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Welcome to AI-Guided Penetration Testing Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/api/tools")
async def list_tools():
    """List available penetration testing tools"""
    tools = [
        {"name": "nmap", "description": "Network mapper for network discovery and security auditing"},
        {"name": "nikto", "description": "Web server scanner"},
        {"name": "sqlmap", "description": "SQL injection testing tool"},
        {"name": "hydra", "description": "Network login cracker"},
        {"name": "john", "description": "Password cracker"},
        {"name": "smbclient", "description": "SMB/CIFS client"}
    ]
    
    # Check availability of each tool
    for tool in tools:
        tool["available"] = check_tool_availability(tool["name"])
    
    return {"tools": tools}

@app.post("/api/scan/nmap")
async def run_nmap_scan(request: ScanRequest):
    """Run an nmap scan"""
    try:
        target = request.target
        scan_type = request.options.get("scan_type", "basic")
        
        # Basic validation
        if not target:
            raise HTTPException(status_code=400, detail="Target is required")
        
        # Construct nmap command based on scan type
        if scan_type == "basic":
            cmd = ["nmap", "-sn", target]
        elif scan_type == "port":
            cmd = ["nmap", "-p", "1-1000", target]
        elif scan_type == "service":
            cmd = ["nmap", "-sV", target]
        else:
            cmd = ["nmap", target]
        
        # Run the scan
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            "scan_id": f"nmap_{hash(target)}",
            "target": target,
            "command": " ".join(cmd),
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Scan timeout")
    except Exception as e:
        logger.error(f"Nmap scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.post("/api/scan/nikto")
async def run_nikto_scan(request: ScanRequest):
    """Run a nikto web vulnerability scan"""
    try:
        target = request.target
        
        # Basic validation
        if not target:
            raise HTTPException(status_code=400, detail="Target is required")
        
        # Construct nikto command
        cmd = ["nikto", "-h", target]
        
        # Run the scan
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        return {
            "scan_id": f"nikto_{hash(target)}",
            "target": target,
            "command": " ".join(cmd),
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Scan timeout")
    except Exception as e:
        logger.error(f"Nikto scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/ollama/models")
async def list_ollama_models():
    """List available Ollama models"""
    try:
        return await ollama_manager.list_models()
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.post("/api/ollama/chat")
async def chat_with_ollama(request: dict):
    """Chat with Ollama AI"""
    try:
        model = request.get("model", "llama3.2:latest")
        message = request.get("message", "")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        response = await ollama_manager.generate_response(model, message)
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Ollama chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
