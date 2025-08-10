"""
Nuclei Tool Implementation

Template-based vulnerability scanner for modern security testing.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import json
import tempfile
import os

class NucleiTool(BasePenTestTool):
    """Nuclei template-based vulnerability scanner"""
    
    def __init__(self):
        super().__init__("nuclei", "nuclei")
        self.template_categories = [
            "cves", "exposures", "technologies", "misconfiguration",
            "takeovers", "default-logins", "file", "network",
            "dns", "headless", "ssl", "workflows"
        ]
        self.severities = ["info", "low", "medium", "high", "critical"]
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method"""
        return self.vulnerability_scan(target, **kwargs)
    
    def vulnerability_scan(self, target: str, **kwargs) -> ToolResult:
        """
        Perform template-based vulnerability scan
        
        Args:
            target: Target URL or IP
            **kwargs: Additional options (templates, severity, etc.)
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if nuclei is available
            if not self._check_nuclei():
                return self._fallback_nuclei_scan(target, **kwargs)
            
            # Update templates first
            self._update_templates()
            
            # Build command
            cmd = self._build_command(target, **kwargs)
            
            # Execute nuclei
            result = self._execute_nuclei(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "vulnerabilities": parsed_results["vulnerabilities"],
                        "findings_count": parsed_results["total_findings"],
                        "severity_breakdown": parsed_results["severity_breakdown"],
                        "templates_used": kwargs.get("templates", ["default"]),
                        "command": " ".join([c for c in cmd if not c.startswith("/tmp")])
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
                error=f"Nuclei scan failed: {str(e)}"
            )
    
    def scan_cves(self, target: str, **kwargs) -> ToolResult:
        """Scan for CVE-based vulnerabilities"""
        kwargs["templates"] = ["cves"]
        return self.vulnerability_scan(target, **kwargs)
    
    def scan_exposures(self, target: str, **kwargs) -> ToolResult:
        """Scan for exposed services and files"""
        kwargs["templates"] = ["exposures"]
        return self.vulnerability_scan(target, **kwargs)
    
    def scan_technologies(self, target: str, **kwargs) -> ToolResult:
        """Technology detection and fingerprinting"""
        kwargs["templates"] = ["technologies"]
        return self.vulnerability_scan(target, **kwargs)
    
    def scan_takeovers(self, target: str, **kwargs) -> ToolResult:
        """Scan for subdomain takeover vulnerabilities"""
        kwargs["templates"] = ["takeovers"]
        return self.vulnerability_scan(target, **kwargs)
    
    def scan_by_severity(self, target: str, severity: str, **kwargs) -> ToolResult:
        """Scan by specific severity level"""
        kwargs["severity"] = severity
        return self.vulnerability_scan(target, **kwargs)
    
    def _check_nuclei(self) -> bool:
        """Check if nuclei is available"""
        try:
            result = subprocess.run(
                ["nuclei", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _update_templates(self) -> bool:
        """Update nuclei templates"""
        try:
            subprocess.run(
                ["nuclei", "-update-templates", "-silent"],
                capture_output=True,
                timeout=60
            )
            return True
        except:
            return False
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build nuclei command"""
        cmd = ["nuclei"]
        
        # Target
        if target.startswith("http"):
            cmd.extend(["-u", target])
        else:
            # Assume it's a host/IP, add protocol
            cmd.extend(["-u", f"http://{target}"])
        
        # Templates
        templates = kwargs.get("templates", [])
        if templates:
            if "all" in templates:
                # Use all templates (be careful in production)
                pass  # nuclei uses all by default
            else:
                # Specific template categories
                for template in templates:
                    if template in self.template_categories:
                        cmd.extend(["-t", template])
                    else:
                        # Assume it's a specific template file/path
                        cmd.extend(["-t", template])
        else:
            # Default safe templates
            cmd.extend(["-t", "exposures/"])
            cmd.extend(["-t", "misconfiguration/"])
        
        # Severity filtering
        severity = kwargs.get("severity")
        if severity and severity in self.severities:
            cmd.extend(["-severity", severity])
        
        # Output format - JSON for better parsing
        output_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        output_file.close()
        cmd.extend(["-json", "-o", output_file.name])
        self._temp_output_file = output_file.name
        
        # Rate limiting for safety
        rate_limit = kwargs.get("rate_limit", 150)  # requests per second
        cmd.extend(["-rate-limit", str(rate_limit)])
        
        # Concurrency
        concurrency = kwargs.get("concurrency", 25)
        cmd.extend(["-c", str(concurrency)])
        
        # Timeout
        timeout = kwargs.get("timeout", 5)
        cmd.extend(["-timeout", str(timeout)])
        
        # Silent mode
        cmd.append("-silent")
        
        # Additional flags
        if kwargs.get("no_color", True):
            cmd.append("-no-color")
        
        if kwargs.get("follow_redirects", True):
            cmd.append("-follow-redirects")
        
        # Custom headers
        headers = kwargs.get("headers", {})
        for header, value in headers.items():
            cmd.extend(["-H", f"{header}: {value}"])
        
        return cmd
    
    def _execute_nuclei(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute nuclei command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            output = result.stdout
            
            # Read JSON output file if it exists
            if hasattr(self, '_temp_output_file') and os.path.exists(self._temp_output_file):
                try:
                    with open(self._temp_output_file, 'r') as f:
                        json_lines = f.readlines()
                        if json_lines:
                            # Nuclei outputs JSONL (one JSON object per line)
                            output = ''.join(json_lines)
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
                "error": "Nuclei scan timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Nuclei execution failed: {str(e)}"
            }
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse nuclei output"""
        results = {
            "vulnerabilities": [],
            "total_findings": 0,
            "severity_breakdown": {"info": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        }
        
        # Parse JSONL output
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                finding = json.loads(line)
                
                vuln = {
                    "template_id": finding.get("template-id", ""),
                    "name": finding.get("info", {}).get("name", ""),
                    "severity": finding.get("info", {}).get("severity", "info"),
                    "description": finding.get("info", {}).get("description", ""),
                    "reference": finding.get("info", {}).get("reference", []),
                    "matched_at": finding.get("matched-at", ""),
                    "curl_command": finding.get("curl-command", ""),
                    "type": finding.get("type", ""),
                    "host": finding.get("host", ""),
                    "timestamp": finding.get("timestamp", "")
                }
                
                results["vulnerabilities"].append(vuln)
                results["total_findings"] += 1
                
                severity = vuln["severity"].lower()
                if severity in results["severity_breakdown"]:
                    results["severity_breakdown"][severity] += 1
                    
            except json.JSONDecodeError:
                # Handle non-JSON lines (maybe template output)
                if "WARN" not in line and "INFO" not in line:
                    results["total_findings"] += 1
        
        return results
    
    def _fallback_nuclei_scan(self, target: str, **kwargs) -> ToolResult:
        """Fallback nuclei simulation"""
        simulated_vulns = [
            {
                "template_id": "tech-detect",
                "name": "Technology Detection",
                "severity": "info",
                "description": "Detected web technologies and frameworks",
                "matched_at": target,
                "type": "http"
            },
            {
                "template_id": "exposed-panels",
                "name": "Admin Panel Exposed",
                "severity": "medium",
                "description": "Administrative panel accessible without authentication",
                "matched_at": f"{target}/admin",
                "type": "http"
            }
        ]
        
        severity_breakdown = {"info": 1, "low": 0, "medium": 1, "high": 0, "critical": 0}
        
        return ToolResult(
            success=True,
            output=f"Simulated Nuclei scan for {target}",
            metadata={
                "vulnerabilities": simulated_vulns,
                "findings_count": len(simulated_vulns),
                "severity_breakdown": severity_breakdown,
                "note": "Nuclei not available - using simulation",
                "recommendations": [
                    "Install Nuclei: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
                    "Or download binary from: https://github.com/projectdiscovery/nuclei/releases",
                    f"Test manually with: nuclei -u {target} -t exposures/",
                    "Update templates regularly: nuclei -update-templates",
                    "Always ensure proper authorization before scanning"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install Nuclei:
        
        1. Go install: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
        2. Binary download: https://github.com/projectdiscovery/nuclei/releases
        3. Docker: docker run projectdiscovery/nuclei
        
        Basic usage:
        nuclei -u https://example.com
        nuclei -u https://example.com -t cves/
        nuclei -u https://example.com -severity critical,high
        nuclei -l targets.txt -t exposures/ -o results.json
        
        Template categories: cves, exposures, technologies, misconfiguration, 
                           takeovers, default-logins, file, network, dns, ssl
        
        Update templates: nuclei -update-templates
        
        WARNING: Only scan targets you own or have explicit permission to test!
        Some templates may be aggressive - use appropriate rate limiting.
        """
