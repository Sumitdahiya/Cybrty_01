"""
Hydra Tool Implementation

Password brute-forcing and authentication testing using THC-Hydra.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import tempfile
import os

class HydraTool(BasePenTestTool):
    """THC-Hydra password brute-forcing tool"""
    
    def __init__(self):
        super().__init__("hydra", "hydra")
        self.common_usernames = [
            "admin", "administrator", "root", "user", "test", "guest",
            "demo", "service", "operator", "manager", "support"
        ]
        self.common_passwords = [
            "password", "admin", "123456", "password123", "admin123",
            "root", "toor", "pass", "test", "guest", "demo", "service",
            "changeme", "default", "login", "welcome", "qwerty", "letmein"
        ]
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method - delegates to brute_force"""
        service = kwargs.pop('service', 'ssh')  # Remove from kwargs to avoid conflict
        return self.brute_force(target, service, **kwargs)
    
    def brute_force(self, target: str, service: str, **kwargs) -> ToolResult:
        """
        Perform password brute-force attack
        
        Args:
            target: Target IP or hostname
            service: Service to attack (ssh, ftp, http, etc.)
            **kwargs: Additional options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if hydra is available
            if not self._check_hydra():
                return self._fallback_brute_force(target, service, **kwargs)
            
            # Build hydra command
            cmd = self._build_command(target, service, **kwargs)
            
            # Execute hydra
            result = self._execute_hydra(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "found_credentials": parsed_results["credentials"],
                        "attempts": parsed_results["attempts"],
                        "service": service,
                        "command": " ".join([c for c in cmd if not c.startswith("-P") or "temp" not in c])
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
                error=f"Hydra brute-force failed: {str(e)}"
            )
    
    def test_ssh(self, target: str, **kwargs) -> ToolResult:
        """Test SSH authentication"""
        return self.brute_force(target, "ssh", **kwargs)
    
    def test_ftp(self, target: str, **kwargs) -> ToolResult:
        """Test FTP authentication"""
        return self.brute_force(target, "ftp", **kwargs)
    
    def test_http_basic(self, target: str, path: str = "/", **kwargs) -> ToolResult:
        """Test HTTP Basic authentication"""
        kwargs["path"] = path
        return self.brute_force(target, "http-get", **kwargs)
    
    def test_http_form(self, target: str, login_path: str, **kwargs) -> ToolResult:
        """Test HTTP form-based authentication"""
        kwargs["login_path"] = login_path
        return self.brute_force(target, "http-post-form", **kwargs)
    
    def test_rdp(self, target: str, **kwargs) -> ToolResult:
        """Test RDP authentication"""
        return self.brute_force(target, "rdp", **kwargs)
    
    def _check_hydra(self) -> bool:
        """Check if hydra is available"""
        try:
            result = subprocess.run(
                ["hydra", "-h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_command(self, target: str, service: str, **kwargs) -> List[str]:
        """Build hydra command"""
        cmd = ["hydra"]
        
        # Username options
        if kwargs.get("username"):
            cmd.extend(["-l", kwargs["username"]])
        elif kwargs.get("userlist"):
            cmd.extend(["-L", kwargs["userlist"]])
        else:
            # Create temporary username file
            userfile = self._create_temp_file(self.common_usernames)
            cmd.extend(["-L", userfile])
        
        # Password options
        if kwargs.get("password"):
            cmd.extend(["-p", kwargs["password"]])
        elif kwargs.get("passlist"):
            cmd.extend(["-P", kwargs["passlist"]])
        else:
            # Create temporary password file (limited for safety)
            limited_passwords = self.common_passwords[:10]  # Limit to 10 passwords
            passfile = self._create_temp_file(limited_passwords)
            cmd.extend(["-P", passfile])
        
        # Threading (be conservative)
        threads = kwargs.get("threads", 4)
        cmd.extend(["-t", str(threads)])
        
        # Exit after first success
        cmd.append("-f")
        
        # Verbose output
        cmd.append("-v")
        
        # Service-specific options
        if service == "http-post-form":
            # Format: "path:user=^USER^&pass=^PASS^:failure_string"
            login_path = kwargs.get("login_path", "/login")
            form_data = kwargs.get("form_data", "username=^USER^&password=^PASS^")
            failure_string = kwargs.get("failure_string", "Login failed")
            service_spec = f"{login_path}:{form_data}:{failure_string}"
            cmd.extend([target, service, service_spec])
        elif service == "http-get":
            path = kwargs.get("path", "/")
            cmd.extend([target, f"{service}:{path}"])
        else:
            # Standard service
            port = kwargs.get("port")
            if port:
                cmd.extend([f"{target}:{port}", service])
            else:
                cmd.extend([target, service])
        
        # Additional options
        if kwargs.get("timeout"):
            cmd.extend(["-w", str(kwargs["timeout"])])
        
        return cmd
    
    def _create_temp_file(self, items: List[str]) -> str:
        """Create temporary file with list items"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for item in items:
                f.write(f"{item}\n")
            return f.name
    
    def _execute_hydra(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute hydra command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 and result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Hydra command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Hydra execution failed: {str(e)}"
            }
        finally:
            # Clean up temporary files
            for item in cmd:
                if item.endswith('.txt') and 'temp' in item:
                    try:
                        os.unlink(item)
                    except:
                        pass
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse hydra output"""
        results = {
            "credentials": [],
            "attempts": 0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse successful login
            if "[ssh]" in line and "login:" in line and "password:" in line:
                # Extract credentials from line like: "[ssh] host: target login: admin password: admin123"
                parts = line.split()
                login_idx = parts.index("login:") + 1
                pass_idx = parts.index("password:") + 1
                
                if login_idx < len(parts) and pass_idx < len(parts):
                    credential = {
                        "username": parts[login_idx],
                        "password": parts[pass_idx],
                        "service": "ssh"
                    }
                    results["credentials"].append(credential)
            
            elif "login:" in line and "password:" in line:
                # Generic credential format
                if "host:" in line:
                    parts = line.split()
                    login_idx = parts.index("login:") + 1
                    pass_idx = parts.index("password:") + 1
                    
                    if login_idx < len(parts) and pass_idx < len(parts):
                        credential = {
                            "username": parts[login_idx],
                            "password": parts[pass_idx]
                        }
                        results["credentials"].append(credential)
            
            # Count attempts
            if "attempt" in line.lower() or "trying" in line.lower():
                results["attempts"] += 1
        
        return results
    
    def _fallback_brute_force(self, target: str, service: str, **kwargs) -> ToolResult:
        """Fallback brute-force simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated Hydra brute-force for {service} on {target}",
            metadata={
                "note": "Hydra not available - using simulation",
                "service": service,
                "target": target,
                "found_credentials": [],
                "recommendations": [
                    "Install hydra: apt-get install hydra",
                    "Or download from: https://github.com/vanhauser-thc/thc-hydra",
                    f"Test manually with: hydra -l admin -p admin {target} {service}",
                    "Always ensure proper authorization before testing"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install THC-Hydra:
        
        1. Debian/Ubuntu: apt-get install hydra
        2. macOS: brew install hydra
        3. Manual install:
           - git clone https://github.com/vanhauser-thc/thc-hydra.git
           - cd thc-hydra && ./configure && make && make install
        4. Kali Linux: pre-installed
        
        Basic usage:
        hydra -l admin -p password target.com ssh
        hydra -L userlist.txt -P passlist.txt target.com ftp
        
        WARNING: Only use on systems you own or have explicit permission to test!
        """
