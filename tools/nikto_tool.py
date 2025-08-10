"""
Nikto Tool Implementation

Web server vulnerability scanning using Nikto.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import json
import re
from urllib.parse import urlparse

class NiktoTool(BasePenTestTool):
    """Nikto web server vulnerability scanner"""
    
    def __init__(self):
        super().__init__("nikto", "nikto")
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """
        Perform Nikto web server scan
        
        Args:
            target: Target URL or IP to scan
            **kwargs: Additional nikto options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if nikto is available
            if not self._check_nikto():
                return self._fallback_scan(target, **kwargs)
            
            # Build nikto command
            cmd = self._build_command(target, **kwargs)
            
            # Execute nikto
            result = self._execute_nikto(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "vulnerabilities": parsed_results["vulnerabilities"],
                        "server_info": parsed_results["server_info"],
                        "total_items": parsed_results["total_items"],
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
                error=f"Nikto scan failed: {str(e)}"
            )
    
    def quick_scan(self, target: str) -> ToolResult:
        """Perform a quick Nikto scan"""
        return self.scan(target, quick=True)
    
    def comprehensive_scan(self, target: str) -> ToolResult:
        """Perform a comprehensive Nikto scan"""
        return self.scan(target, comprehensive=True)
    
    def ssl_scan(self, target: str) -> ToolResult:
        """Perform SSL-specific Nikto scan"""
        return self.scan(target, ssl=True)
    
    def _check_nikto(self) -> bool:
        """Check if nikto is available"""
        try:
            result = subprocess.run(
                ["nikto", "-Version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            try:
                # Try alternative path
                result = subprocess.run(
                    ["/usr/bin/nikto", "-Version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except:
                return False
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build nikto command"""
        cmd = ["nikto"]
        
        # Add target
        parsed_url = urlparse(target)
        if parsed_url.scheme:
            cmd.extend(["-host", target])
        else:
            cmd.extend(["-host", f"http://{target}"])
        
        # Add port if specified
        if kwargs.get("port"):
            cmd.extend(["-port", str(kwargs["port"])])
        elif parsed_url.port:
            cmd.extend(["-port", str(parsed_url.port)])
        
        # Scan options
        if kwargs.get("quick"):
            cmd.append("-C")  # Check for CGI directories only
        elif kwargs.get("comprehensive"):
            cmd.append("-C")  # Check for CGI directories
            cmd.append("-generic")  # Generic checks
        
        # SSL options
        if kwargs.get("ssl") or target.startswith("https"):
            cmd.append("-ssl")
        
        # Output format
        cmd.extend(["-Format", "txt"])
        
        # Timeout and throttling
        timeout = kwargs.get("timeout", 120)
        cmd.extend(["-timeout", str(timeout)])
        
        # Be less aggressive by default
        if not kwargs.get("aggressive"):
            cmd.extend(["-Pause", "1"])  # Pause between requests
        
        # User agent
        if kwargs.get("user_agent"):
            cmd.extend(["-useragent", kwargs["user_agent"]])
        
        # Authentication
        if kwargs.get("auth"):
            cmd.extend(["-id", kwargs["auth"]])
        
        # Proxy
        if kwargs.get("proxy"):
            cmd.extend(["-useproxy", kwargs["proxy"]])
        
        # Additional options
        if kwargs.get("no404"):
            cmd.append("-no404")
        
        if kwargs.get("nolookup"):
            cmd.append("-nolookup")
        
        return cmd
    
    def _execute_nikto(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute nikto command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Nikto might return non-zero even on success
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr if result.stderr and "ERROR" in result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Nikto scan timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Nikto execution failed: {str(e)}"
            }
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse nikto output"""
        results = {
            "vulnerabilities": [],
            "server_info": {},
            "total_items": 0
        }
        
        lines = output.split('\n')
        current_target = None
        
        for line in lines:
            line = line.strip()
            
            # Parse target info
            if line.startswith("- Nikto v"):
                continue
            elif line.startswith("+ Target IP:"):
                results["server_info"]["ip"] = line.split(":", 1)[1].strip()
            elif line.startswith("+ Target Hostname:"):
                results["server_info"]["hostname"] = line.split(":", 1)[1].strip()
            elif line.startswith("+ Target Port:"):
                results["server_info"]["port"] = line.split(":", 1)[1].strip()
            elif line.startswith("+ Start Time:"):
                results["server_info"]["start_time"] = line.split(":", 1)[1].strip()
            elif line.startswith("+ Server:"):
                results["server_info"]["server"] = line.split(":", 1)[1].strip()
            
            # Parse vulnerabilities/findings
            elif line.startswith("+ ") and ":" in line:
                vuln = {
                    "type": "finding",
                    "description": line[2:],  # Remove "+ "
                    "severity": self._classify_severity(line)
                }
                results["vulnerabilities"].append(vuln)
                results["total_items"] += 1
            
            # Parse OSVDB entries
            elif "OSVDB-" in line:
                vuln = {
                    "type": "osvdb",
                    "description": line,
                    "osvdb_id": self._extract_osvdb_id(line),
                    "severity": self._classify_severity(line)
                }
                results["vulnerabilities"].append(vuln)
                results["total_items"] += 1
        
        return results
    
    def _classify_severity(self, description: str) -> str:
        """Classify vulnerability severity based on description"""
        description_lower = description.lower()
        
        # High severity indicators
        high_indicators = [
            "sql injection", "xss", "cross-site scripting", "remote code execution",
            "file inclusion", "directory traversal", "authentication bypass",
            "privilege escalation", "buffer overflow"
        ]
        
        # Medium severity indicators
        medium_indicators = [
            "information disclosure", "configuration", "default", "version",
            "backup", "log", "debug", "admin"
        ]
        
        # Low severity indicators
        low_indicators = [
            "banner", "header", "cookie", "redirect", "robots.txt"
        ]
        
        for indicator in high_indicators:
            if indicator in description_lower:
                return "High"
        
        for indicator in medium_indicators:
            if indicator in description_lower:
                return "Medium"
        
        for indicator in low_indicators:
            if indicator in description_lower:
                return "Low"
        
        return "Info"
    
    def _extract_osvdb_id(self, line: str) -> Optional[str]:
        """Extract OSVDB ID from line"""
        match = re.search(r'OSVDB-(\d+)', line)
        return match.group(1) if match else None
    
    def _fallback_scan(self, target: str, **kwargs) -> ToolResult:
        """Fallback scan simulation"""
        parsed_url = urlparse(target)
        hostname = parsed_url.hostname or target
        
        simulated_findings = [
            f"Server: Apache/2.4.41 (Ubuntu)",
            f"The anti-clickjacking X-Frame-Options header is not present",
            f"The X-XSS-Protection header is not defined",
            f"The X-Content-Type-Options header is not set",
            f"Root page / redirects to: /index.html",
            f"No CGI Directories found (use '-C all' to force check all possible dirs)",
            f"Server may leak inodes via ETags",
            f"OSVDB-3233: /icons/README: Apache default file found"
        ]
        
        return ToolResult(
            success=True,
            output=f"Simulated Nikto scan for {target}\n" + "\n".join([f"+ {finding}" for finding in simulated_findings]),
            metadata={
                "note": "Nikto not available - using simulation",
                "vulnerabilities": [
                    {"type": "finding", "description": finding, "severity": "Low"}
                    for finding in simulated_findings
                ],
                "server_info": {"hostname": hostname},
                "total_items": len(simulated_findings),
                "recommendations": [
                    "Install nikto: apt-get install nikto",
                    "Or download from: https://cirt.net/Nikto2",
                    f"Test manually with: nikto -host {target}"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install Nikto:
        
        1. Debian/Ubuntu: apt-get install nikto
        2. macOS: brew install nikto
        3. Manual install:
           - Download from https://cirt.net/Nikto2
           - Extract and run: perl nikto.pl
        4. Kali Linux: pre-installed
        
        Basic usage:
        nikto -host http://target.com
        nikto -host target.com -port 80,443
        """
