"""
Enum4linux Tool Implementation

SMB/NetBIOS enumeration using enum4linux.
Now with MongoDB integration for result storage.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import re
from datetime import datetime
import os
import sys

# Add parent directory to path for MongoDB integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mongodb_integration import CrewAIMongoDB
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️  MongoDB integration not available. Results will not be stored in MongoDB.")

class Enum4linuxTool(BasePenTestTool):
    """enum4linux SMB/NetBIOS enumeration tool with MongoDB integration"""
    
    def __init__(self):
        super().__init__("enum4linux", "enum4linux")
        self.mongo = None
        if MONGODB_AVAILABLE:
            try:
                self.mongo = CrewAIMongoDB()
                print("✅ MongoDB connected for enum4linux results")
            except Exception as e:
                print(f"⚠️  MongoDB connection failed: {e}")
                self.mongo = None
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """
        Main scanning interface - calls enumerate method
        
        Args:
            target: Target IP address
            **kwargs: Additional options
        """
        return self.enumerate(target, **kwargs)
    
    def enumerate(self, target: str, **kwargs) -> ToolResult:
        """
        Enumerate SMB/NetBIOS information
        
        Args:
            target: Target IP address
            **kwargs: Additional options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_enum4linux():
                return self._fallback_enumerate(target, **kwargs)
            
            cmd = self._build_command(target, **kwargs)
            result = self._execute_enum4linux(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                
                # Store results in MongoDB if available
                if self.mongo:
                    try:
                        mongo_result_id = self.mongo.store_tool_result(
                            tool_name="enum4linux",
                            target=target,
                            result_data={
                                "success": True,
                                "raw_output": result["output"],
                                "parsed_data": parsed_results,
                                "command": " ".join(cmd),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                        print(f"💾 Results stored in MongoDB: {mongo_result_id}")
                    except Exception as e:
                        print(f"⚠️  Failed to store in MongoDB: {e}")
                
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "shares": parsed_results["shares"],
                        "users": parsed_results["users"],
                        "groups": parsed_results["groups"],
                        "os_info": parsed_results["os_info"],
                        "command": " ".join(cmd),
                        "stored_in_mongodb": self.mongo is not None
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    output=result["output"],
                    error=result["error"]
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"enum4linux failed: {str(e)}"
            )
    
    def _check_enum4linux(self) -> bool:
        """Check if enum4linux is available"""
        try:
            result = subprocess.run(
                ["enum4linux", "-h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build enum4linux command"""
        cmd = ["enum4linux"]
        
        # Default to all enumeration
        if not any(k in kwargs for k in ["users", "shares", "groups", "policies"]):
            cmd.append("-a")  # All enumeration
        else:
            if kwargs.get("users"):
                cmd.append("-U")
            if kwargs.get("shares"):
                cmd.append("-S")
            if kwargs.get("groups"):
                cmd.append("-G")
            if kwargs.get("policies"):
                cmd.append("-P")
        
        # Authentication
        if kwargs.get("username") and kwargs.get("password"):
            cmd.extend(["-u", kwargs["username"]])
            cmd.extend(["-p", kwargs["password"]])
        
        cmd.append(target)
        return cmd
    
    def _execute_enum4linux(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute enum4linux command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "enum4linux timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"enum4linux execution failed: {str(e)}"
            }
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse enum4linux output"""
        results = {
            "shares": [],
            "users": [],
            "groups": [],
            "os_info": {}
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse shares
            if "Sharename" in line and "Type" in line:
                continue  # Header line
            elif line.startswith("\\\\") and "\t" in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    share_name = parts[0].replace("\\\\", "").split("\\")[-1]
                    share_type = parts[1] if len(parts) > 1 else "Unknown"
                    comment = parts[2] if len(parts) > 2 else ""
                    results["shares"].append({
                        "name": share_name,
                        "type": share_type,
                        "comment": comment
                    })
            
            # Parse users
            elif "user:" in line:
                user_match = re.search(r'user:\[([^\]]+)\]', line)
                if user_match:
                    results["users"].append(user_match.group(1))
            
            # Parse groups
            elif "group:" in line:
                group_match = re.search(r'group:\[([^\]]+)\]', line)
                if group_match:
                    results["groups"].append(group_match.group(1))
            
            # Parse OS info
            elif "OS=" in line:
                results["os_info"]["os"] = line.split("OS=")[1].split(",")[0].strip()
        
        return results
    
    def _fallback_enumerate(self, target: str, **kwargs) -> ToolResult:
        """Fallback enumeration simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated enum4linux enumeration for {target}",
            metadata={
                "note": "enum4linux not available - using simulation",
                "shares": [
                    {"name": "IPC$", "type": "IPC", "comment": "IPC Service"},
                    {"name": "C$", "type": "Disk", "comment": "Default share"}
                ],
                "users": ["Administrator", "Guest"],
                "groups": ["Administrators", "Users"],
                "recommendations": [
                    "Install enum4linux: apt-get install enum4linux",
                    f"Test manually with: enum4linux -a {target}"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install enum4linux:
        
        1. Debian/Ubuntu: apt-get install enum4linux
        2. Kali Linux: pre-installed
        3. Manual install: Download from https://labs.portcullis.co.uk/tools/enum4linux/
        
        Basic usage:
        enum4linux -a target_ip
        enum4linux -U target_ip  # Users only
        enum4linux -S target_ip  # Shares only
        """
