"""
Metasploit Tool Implementation

Penetration testing framework using Metasploit.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import tempfile
import os
import json

class MetasploitTool(BasePenTestTool):
    """Metasploit penetration testing framework"""
    
    def __init__(self):
        super().__init__("metasploit", "msfconsole")
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method - searches for exploits for the target"""
        return self.search_exploits(target, **kwargs)
    
    def search_exploits(self, target: str, **kwargs) -> ToolResult:
        """
        Search for exploits for a target
        
        Args:
            target: Target service/application to search exploits for
            **kwargs: Additional search options
        """
        try:
            if not self._check_metasploit():
                return self._fallback_search(target, **kwargs)
            
            # Build search command
            search_terms = self._build_search_terms(target, **kwargs)
            cmd = self._build_search_command(search_terms)
            
            result = self._execute_msfconsole(cmd)
            
            if result["success"]:
                exploits = self._parse_search_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "exploits": exploits,
                        "search_terms": search_terms,
                        "exploit_count": len(exploits),
                        "command": " ".join(cmd)
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
                error=f"Metasploit search failed: {str(e)}"
            )
    
    def exploit_info(self, exploit_name: str) -> ToolResult:
        """
        Get information about a specific exploit
        
        Args:
            exploit_name: Name of the exploit module
        """
        try:
            if not self._check_metasploit():
                return self._fallback_info(exploit_name)
            
            cmd = self._build_info_command(exploit_name)
            result = self._execute_msfconsole(cmd)
            
            if result["success"]:
                info = self._parse_exploit_info(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "exploit": exploit_name,
                        "info": info,
                        "command": " ".join(cmd)
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
                error=f"Exploit info failed: {str(e)}"
            )
    
    def generate_payload(self, payload_type: str, **kwargs) -> ToolResult:
        """
        Generate a payload
        
        Args:
            payload_type: Type of payload to generate
            **kwargs: Payload options
        """
        if not self.check_target_safety(kwargs.get("lhost", "127.0.0.1")):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_msfvenom():
                return self._fallback_payload(payload_type, **kwargs)
            
            cmd = self._build_payload_command(payload_type, **kwargs)
            result = self._execute_command(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "payload_type": payload_type,
                        "options": kwargs,
                        "command": " ".join(cmd),
                        "warning": "Generated payload for educational purposes only"
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
                error=f"Payload generation failed: {str(e)}"
            )
    
    def scan_auxiliary(self, target: str, module: str, **kwargs) -> ToolResult:
        """
        Run auxiliary scan module
        
        Args:
            target: Target to scan
            module: Auxiliary module to use
            **kwargs: Module options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_metasploit():
                return self._fallback_auxiliary(target, module, **kwargs)
            
            cmd = self._build_auxiliary_command(target, module, **kwargs)
            result = self._execute_msfconsole(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "target": target,
                        "module": module,
                        "command": " ".join(cmd)
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
                error=f"Auxiliary scan failed: {str(e)}"
            )
    
    def _check_metasploit(self) -> bool:
        """Check if Metasploit is available"""
        try:
            result = subprocess.run(
                ["msfconsole", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_msfvenom(self) -> bool:
        """Check if msfvenom is available"""
        try:
            result = subprocess.run(
                ["msfvenom", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_search_terms(self, target: str, **kwargs) -> str:
        """Build search terms for exploit search"""
        terms = [target]
        
        if kwargs.get("platform"):
            terms.append(f"platform:{kwargs['platform']}")
        if kwargs.get("type"):
            terms.append(f"type:{kwargs['type']}")
        if kwargs.get("rank"):
            terms.append(f"rank:{kwargs['rank']}")
        
        return " ".join(terms)
    
    def _build_search_command(self, search_terms: str) -> List[str]:
        """Build msfconsole search command"""
        script = f"""
search {search_terms}
exit
"""
        return ["msfconsole", "-q", "-x", script.strip()]
    
    def _build_info_command(self, exploit_name: str) -> List[str]:
        """Build exploit info command"""
        script = f"""
info {exploit_name}
exit
"""
        return ["msfconsole", "-q", "-x", script.strip()]
    
    def _build_payload_command(self, payload_type: str, **kwargs) -> List[str]:
        """Build msfvenom payload command"""
        cmd = ["msfvenom", "-p", payload_type]
        
        # Add options
        if kwargs.get("lhost"):
            cmd.extend(["LHOST=" + kwargs["lhost"]])
        if kwargs.get("lport"):
            cmd.extend(["LPORT=" + str(kwargs["lport"])])
        if kwargs.get("format"):
            cmd.extend(["-f", kwargs["format"]])
        if kwargs.get("output"):
            cmd.extend(["-o", kwargs["output"]])
        
        # Add encoder for evasion
        if kwargs.get("encoder"):
            cmd.extend(["-e", kwargs["encoder"]])
        
        return cmd
    
    def _build_auxiliary_command(self, target: str, module: str, **kwargs) -> List[str]:
        """Build auxiliary module command"""
        script = f"""
use {module}
set RHOSTS {target}
"""
        
        # Add additional options
        for key, value in kwargs.items():
            if key not in ["target", "module"]:
                script += f"set {key.upper()} {value}\n"
        
        script += "run\nexit\n"
        
        return ["msfconsole", "-q", "-x", script.strip()]
    
    def _execute_msfconsole(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute msfconsole command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
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
                "error": "Metasploit command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Metasploit execution failed: {str(e)}"
            }
    
    def _execute_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute general command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
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
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Command execution failed: {str(e)}"
            }
    
    def _parse_search_results(self, output: str) -> List[Dict[str, str]]:
        """Parse exploit search results"""
        exploits = []
        lines = output.split('\n')
        
        for line in lines:
            if "exploit/" in line and "/" in line:
                parts = line.split()
                if len(parts) >= 3:
                    exploits.append({
                        "name": parts[0],
                        "disclosure_date": parts[1] if len(parts) > 1 else "",
                        "rank": parts[2] if len(parts) > 2 else "",
                        "description": " ".join(parts[3:]) if len(parts) > 3 else ""
                    })
        
        return exploits
    
    def _parse_exploit_info(self, output: str) -> Dict[str, Any]:
        """Parse exploit info"""
        info = {}
        lines = output.split('\n')
        
        for line in lines:
            if "Name:" in line:
                info["name"] = line.split("Name:", 1)[1].strip()
            elif "Platform:" in line:
                info["platform"] = line.split("Platform:", 1)[1].strip()
            elif "Privileged:" in line:
                info["privileged"] = line.split("Privileged:", 1)[1].strip()
            elif "License:" in line:
                info["license"] = line.split("License:", 1)[1].strip()
            elif "Rank:" in line:
                info["rank"] = line.split("Rank:", 1)[1].strip()
        
        return info
    
    def _fallback_search(self, target: str, **kwargs) -> ToolResult:
        """Fallback search simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated Metasploit search for {target}",
            metadata={
                "note": "Metasploit not available - using simulation",
                "exploits": [
                    {
                        "name": "exploit/windows/smb/ms17_010_eternalblue",
                        "rank": "Average",
                        "description": "MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption"
                    },
                    {
                        "name": "exploit/multi/handler",
                        "rank": "Manual",
                        "description": "Generic Payload Handler"
                    }
                ],
                "recommendations": [
                    "Install Metasploit Framework",
                    "Download from: https://www.metasploit.com/",
                    f"Search with: msfconsole -x 'search {target}'"
                ]
            }
        )
    
    def _fallback_info(self, exploit_name: str) -> ToolResult:
        """Fallback info simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated exploit info for {exploit_name}",
            metadata={
                "note": "Metasploit not available - using simulation",
                "info": {
                    "name": exploit_name,
                    "rank": "Average",
                    "platform": "Windows"
                }
            }
        )
    
    def _fallback_payload(self, payload_type: str, **kwargs) -> ToolResult:
        """Fallback payload simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated payload generation for {payload_type}",
            metadata={
                "note": "Metasploit not available - using simulation",
                "payload_type": payload_type,
                "warning": "For educational purposes only"
            }
        )
    
    def _fallback_auxiliary(self, target: str, module: str, **kwargs) -> ToolResult:
        """Fallback auxiliary simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated auxiliary scan of {target} with {module}",
            metadata={
                "note": "Metasploit not available - using simulation",
                "target": target,
                "module": module
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install Metasploit Framework:
        
        1. Kali Linux: pre-installed
        2. Ubuntu/Debian:
           curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && chmod 755 msfinstall && ./msfinstall
        3. macOS: Download installer from https://www.metasploit.com/
        4. Docker: docker run --rm -it -v ~/.msf4:/home/msf/.msf4 metasploitframework/metasploit-framework
        
        Basic usage:
        msfconsole
        search windows smb
        use exploit/windows/smb/ms17_010_eternalblue
        set RHOSTS target_ip
        exploit
        
        WARNING: Only use on systems you own or have explicit permission to test!
        """
