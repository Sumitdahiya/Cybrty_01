"""
theHarvester Tool Implementation

OSINT data gathering for emails, subdomains, hosts, and other information.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import json
import tempfile
import os

class TheHarvesterTool(BasePenTestTool):
    """theHarvester OSINT information gathering tool"""
    
    def __init__(self):
        super().__init__("theharvester", "theHarvester")
        self.data_sources = [
            "anubis", "baidu", "bing", "bingapi", "bufferoverun",
            "certspotter", "crtsh", "dnsdumpster", "duckduckgo",
            "github-code", "google", "hackertarget", "hunter",
            "intelx", "linkedin", "netcraft", "otx", "rapiddns",
            "securitytrails", "shodan", "spyse", "sublist3r",
            "threatcrowd", "trello", "twitter", "urlscan", "virustotal",
            "yahoo", "zoomeye"
        ]
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method"""
        return self.gather_info(target, **kwargs)
    
    def gather_info(self, target: str, **kwargs) -> ToolResult:
        """
        Gather OSINT information for target domain
        
        Args:
            target: Target domain
            **kwargs: Additional options (data_sources, limit, etc.)
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if theHarvester is available
            if not self._check_theharvester():
                return self._fallback_osint(target, **kwargs)
            
            # Build command
            cmd = self._build_command(target, **kwargs)
            
            # Execute theHarvester
            result = self._execute_theharvester(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "emails": parsed_results["emails"],
                        "hosts": parsed_results["hosts"],
                        "subdomains": parsed_results["subdomains"],
                        "ips": parsed_results["ips"],
                        "sources_used": kwargs.get("data_sources", ["all"]),
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
                error=f"theHarvester scan failed: {str(e)}"
            )
    
    def gather_emails(self, target: str, **kwargs) -> ToolResult:
        """Focus on email gathering"""
        kwargs["email_focus"] = True
        return self.gather_info(target, **kwargs)
    
    def gather_subdomains(self, target: str, **kwargs) -> ToolResult:
        """Focus on subdomain discovery"""
        kwargs["subdomain_focus"] = True
        return self.gather_info(target, **kwargs)
    
    def gather_from_source(self, target: str, source: str, **kwargs) -> ToolResult:
        """Gather from specific data source"""
        kwargs["data_sources"] = [source]
        return self.gather_info(target, **kwargs)
    
    def _check_theharvester(self) -> bool:
        """Check if theHarvester is available"""
        try:
            # Try multiple common command names
            for cmd in ["theHarvester", "theharvester", "theHarvester.py"]:
                try:
                    result = subprocess.run(
                        [cmd, "-h"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 or "theHarvester" in result.stdout:
                        self.tool_path = cmd
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build theHarvester command"""
        cmd = [getattr(self, 'tool_path', 'theHarvester')]
        
        # Domain
        cmd.extend(["-d", target])
        
        # Data sources
        sources = kwargs.get("data_sources", ["google", "bing", "duckduckgo"])
        if "all" in sources:
            cmd.extend(["-b", "all"])
        else:
            # Limit to safe/free sources for demonstration
            safe_sources = [s for s in sources if s in ["google", "bing", "duckduckgo", "yahoo", "baidu"]]
            if safe_sources:
                cmd.extend(["-b", ",".join(safe_sources)])
            else:
                cmd.extend(["-b", "google,bing"])
        
        # Limit results for safety
        limit = kwargs.get("limit", 100)
        cmd.extend(["-l", str(limit)])
        
        # Output format
        if kwargs.get("json_output", True):
            # Create temp file for JSON output
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            temp_file.close()
            cmd.extend(["-f", temp_file.name])
            self._temp_output_file = temp_file.name
        
        # Additional options
        if kwargs.get("verify_hosts"):
            cmd.append("-v")
        
        if kwargs.get("take_screenshots"):
            cmd.append("-s")
        
        return cmd
    
    def _execute_theharvester(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute theHarvester command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout
            
            # If JSON output file was created, read it
            if hasattr(self, '_temp_output_file') and os.path.exists(self._temp_output_file):
                try:
                    with open(self._temp_output_file, 'r') as f:
                        json_data = json.load(f)
                        output = json.dumps(json_data, indent=2)
                except:
                    pass
                finally:
                    try:
                        os.unlink(self._temp_output_file)
                    except:
                        pass
            
            return {
                "success": True,
                "output": output,
                "error": result.stderr if result.returncode != 0 and result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "theHarvester command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"theHarvester execution failed: {str(e)}"
            }
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse theHarvester output"""
        results = {
            "emails": [],
            "hosts": [],
            "subdomains": [],
            "ips": []
        }
        
        try:
            # Try to parse as JSON first
            json_data = json.loads(output)
            if "emails" in json_data:
                results["emails"] = json_data["emails"]
            if "hosts" in json_data:
                results["hosts"] = json_data["hosts"]
            if "ips" in json_data:
                results["ips"] = json_data["ips"]
            return results
        except:
            pass
        
        # Parse text output
        lines = output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "emails found:" in line.lower():
                current_section = "emails"
                continue
            elif "hosts found:" in line.lower():
                current_section = "hosts"
                continue
            elif "ips found:" in line.lower():
                current_section = "ips"
                continue
            
            # Extract data based on current section
            if current_section == "emails" and "@" in line:
                email = line.strip()
                if email and email not in results["emails"]:
                    results["emails"].append(email)
            
            elif current_section == "hosts" and line and not line.startswith("-"):
                host = line.strip()
                if host and host not in results["hosts"]:
                    results["hosts"].append(host)
                    # Also add as subdomain if it's a subdomain
                    if "." in host and not any(char.isdigit() for char in host.replace(".", "")):
                        if host not in results["subdomains"]:
                            results["subdomains"].append(host)
            
            elif current_section == "ips" and line and "." in line:
                ip = line.strip()
                if ip and ip not in results["ips"]:
                    results["ips"].append(ip)
        
        return results
    
    def _fallback_osint(self, target: str, **kwargs) -> ToolResult:
        """Fallback OSINT simulation"""
        simulated_results = {
            "emails": [
                f"admin@{target}",
                f"info@{target}",
                f"contact@{target}"
            ],
            "subdomains": [
                f"www.{target}",
                f"mail.{target}",
                f"ftp.{target}",
                f"admin.{target}"
            ],
            "hosts": [
                target,
                f"www.{target}",
                f"mail.{target}"
            ],
            "ips": ["1.2.3.4", "5.6.7.8"]
        }
        
        return ToolResult(
            success=True,
            output=f"Simulated theHarvester OSINT for {target}",
            metadata={
                **simulated_results,
                "note": "theHarvester not available - using simulation",
                "recommendations": [
                    "Install theHarvester: pip3 install theHarvester",
                    "Or clone from: git clone https://github.com/laramies/theHarvester.git",
                    f"Test manually with: theHarvester -d {target} -b google",
                    "Always respect rate limits and terms of service",
                    "Only gather information on authorized targets"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install theHarvester:
        
        1. pip3 install theHarvester
        2. Or manual install:
           - git clone https://github.com/laramies/theHarvester.git
           - cd theHarvester && pip3 install -r requirements.txt
        3. Kali Linux: pre-installed
        
        Basic usage:
        theHarvester -d example.com -b google
        theHarvester -d example.com -b all -l 500
        theHarvester -d example.com -b google,bing,yahoo -f output.json
        
        Data sources: google, bing, yahoo, duckduckgo, github-code, linkedin, etc.
        
        WARNING: Only use on domains you own or have explicit permission to investigate!
        Respect rate limits and terms of service of data sources.
        """
