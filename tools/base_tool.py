"""
Base Tool Class for Penetration Testing Tools

This module provides a common interface for all penetration testing tools
with safety checks, logging, and ethical guidelines enforcement.
"""

import subprocess
import logging
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Standard result format for all tools"""
    success: bool
    output: str
    error: str = ""
    command: str = ""
    exit_code: int = 0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BasePenTestTool(ABC):
    """Base class for all penetration testing tools"""
    
    def __init__(self, tool_name: str, binary_path: Optional[str] = None):
        self.tool_name = tool_name
        self.binary_path = binary_path or tool_name
        self.logger = logging.getLogger(f"tools.{tool_name}")
        
    def is_installed(self) -> bool:
        """Check if the tool is installed and available"""
        try:
            return shutil.which(self.binary_path) is not None
        except Exception as e:
            self.logger.error(f"Error checking {self.tool_name} installation: {e}")
            return False
    
    def check_target_safety(self, target: str) -> bool:
        """
        Perform safety checks on target before execution
        Override this method for tool-specific safety checks
        """
        # Basic safety checks
        forbidden_targets = [
            'localhost', '127.0.0.1', '::1',
            '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'
        ]
        
        # Check if target is in forbidden list
        for forbidden in forbidden_targets:
            if forbidden in target.lower():
                self.logger.warning(f"Target {target} may be internal/localhost - use with caution")
                break
                
        return True
    
    def execute_command(self, command: List[str], timeout: int = 300) -> ToolResult:
        """
        Safely execute a command with proper error handling
        """
        try:
            if not self.is_installed():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"{self.tool_name} is not installed",
                    command=" ".join(command)
                )
            
            self.logger.info(f"Executing: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                command=" ".join(command),
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                command=" ".join(command)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                command=" ".join(command)
            )
    
    @abstractmethod
    def scan(self, target: str, **kwargs) -> ToolResult:
        """
        Main scanning method - must be implemented by each tool
        """
        pass
    
    def get_installation_instructions(self) -> str:
        """
        Return installation instructions for the tool
        """
        return f"Please install {self.tool_name} to use this functionality."
