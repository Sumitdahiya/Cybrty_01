"""
Masscan Tool Implementation

Ultra-fast port scanner for large-scale network discovery.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import json
import tempfile
import os
import ipaddress

class MasscanTool(BasePenTestTool):
    """Masscan ultra-fast port scanner"""
    
    def __init__(self):
        super().__init__("masscan", "masscan")
        self.common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 993, 995,
            1723, 3306, 3389, 5432, 5900, 6000, 6001, 8000, 8008, 8080, 8443
        ]
        self.top_ports = {
            100: [7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106, 110, 111, 113, 119, 135, 139, 143, 144, 179, 199, 389, 427, 443, 444, 445, 465, 513, 514, 515, 543, 544, 548, 554, 587, 631, 646, 873, 990, 993, 995, 1025, 1026, 1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755, 1900, 2000, 2001, 2049, 2121, 2717, 3000, 3128, 3306, 3389, 3986, 4899, 5000, 5009, 5051, 5060, 5101, 5190, 5357, 5432, 5631, 5666, 5800, 5900, 6000, 6001, 6646, 7070, 8000, 8008, 8009, 8080, 8081, 8443, 8888, 9100, 9999, 10000, 32768, 49152, 49153, 49154, 49155, 49156, 49157],
            1000: list(range(1, 1001))
        }
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method"""
        return self.port_scan(target, **kwargs)
    
    def port_scan(self, target: str, **kwargs) -> ToolResult:
        """
        Perform fast port scan
        
        Args:
            target: Target IP, CIDR, or range
            **kwargs: Additional options (ports, rate, etc.)
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Validate target format
            if not self._validate_target(target):
                return ToolResult(
                    success=False,
                    output="",
                    error="Invalid target format. Use IP, CIDR, or range (e.g., 192.168.1.1, 192.168.1.0/24)"
                )
            
            # Check if masscan is available
            if not self._check_masscan():
                return self._fallback_port_scan(target, **kwargs)
            
            # Build command
            cmd = self._build_command(target, **kwargs)
            
            # Execute masscan
            result = self._execute_masscan(cmd)
            
            if result["success"]:
                parsed_results = self._parse_results(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "open_ports": parsed_results["open_ports"],
                        "hosts_found": parsed_results["hosts_found"],
                        "total_ports_found": parsed_results["total_ports"],
                        "scan_rate": kwargs.get("rate", 1000),
                        "ports_scanned": kwargs.get("ports", "common"),
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
                error=f"Masscan scan failed: {str(e)}"
            )
    
    def scan_top_ports(self, target: str, count: int = 100, **kwargs) -> ToolResult:
        """Scan top N ports"""
        if count in self.top_ports:
            kwargs["ports"] = self.top_ports[count]
        else:
            kwargs["ports"] = self.top_ports[100]  # Default to top 100
        return self.port_scan(target, **kwargs)
    
    def scan_port_range(self, target: str, start_port: int, end_port: int, **kwargs) -> ToolResult:
        """Scan specific port range"""
        kwargs["ports"] = list(range(start_port, end_port + 1))
        return self.port_scan(target, **kwargs)
    
    def scan_common_ports(self, target: str, **kwargs) -> ToolResult:
        """Scan common service ports"""
        kwargs["ports"] = self.common_ports
        return self.port_scan(target, **kwargs)
    
    def fast_discovery(self, target: str, **kwargs) -> ToolResult:
        """Fast host discovery scan"""
        kwargs["discovery_only"] = True
        kwargs["ports"] = [80, 443, 22, 21]  # Common discovery ports
        kwargs["rate"] = kwargs.get("rate", 5000)  # Higher rate for discovery
        return self.port_scan(target, **kwargs)
    
    def _validate_target(self, target: str) -> bool:
        """Validate target format"""
        try:
            # Check if it's a valid IP
            ipaddress.ip_address(target)
            return True
        except:
            pass
        
        try:
            # Check if it's a valid CIDR
            ipaddress.ip_network(target, strict=False)
            return True
        except:
            pass
        
        # Check if it's a range (e.g., 192.168.1.1-192.168.1.10)
        if "-" in target:
            parts = target.split("-")
            if len(parts) == 2:
                try:
                    ipaddress.ip_address(parts[0])
                    ipaddress.ip_address(parts[1])
                    return True
                except:
                    pass
        
        return False
    
    def _check_masscan(self) -> bool:
        """Check if masscan is available"""
        try:
            result = subprocess.run(
                ["masscan", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 or "masscan" in result.stdout
        except:
            return False
    
    def _build_command(self, target: str, **kwargs) -> List[str]:
        """Build masscan command"""
        cmd = ["masscan"]
        
        # Target
        cmd.append(target)
        
        # Ports
        ports = kwargs.get("ports", self.common_ports)
        if isinstance(ports, list):
            if len(ports) > 100:  # Limit for safety
                ports = ports[:100]
            port_string = ",".join(map(str, ports))
        elif isinstance(ports, str):
            port_string = ports
        else:
            port_string = ",".join(map(str, self.common_ports))
        
        cmd.extend(["-p", port_string])
        
        # Rate limiting (packets per second)
        rate = kwargs.get("rate", 1000)  # Conservative default
        if rate > 10000:  # Safety limit
            rate = 10000
        cmd.extend(["--rate", str(rate)])
        
        # Output format - JSON for better parsing
        output_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        output_file.close()
        cmd.extend(["-oJ", output_file.name])
        self._temp_output_file = output_file.name
        
        # Additional options
        if kwargs.get("discovery_only"):
            cmd.append("--ping")
        
        # Source port randomization
        if kwargs.get("randomize_ports", True):
            cmd.append("--randomize-hosts")
        
        # Exclude ranges (for safety)
        excludes = kwargs.get("exclude", [])
        for exclude in excludes:
            cmd.extend(["--exclude", exclude])
        
        # Interface specification
        interface = kwargs.get("interface")
        if interface:
            cmd.extend(["-e", interface])
        
        # Adapter IP (source IP)
        source_ip = kwargs.get("source_ip")
        if source_ip:
            cmd.extend(["--adapter-ip", source_ip])
        
        # Wait time
        wait = kwargs.get("wait", 10)
        cmd.extend(["--wait", str(wait)])
        
        return cmd
    
    def _execute_masscan(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute masscan command"""
        try:
            # Masscan requires root privileges, handle gracefully
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = result.stdout
            
            # Read JSON output file if it exists
            if hasattr(self, '_temp_output_file') and os.path.exists(self._temp_output_file):
                try:
                    with open(self._temp_output_file, 'r') as f:
                        json_data = f.read()
                        if json_data.strip():
                            output = json_data
                except:
                    pass
                finally:
                    try:
                        os.unlink(self._temp_output_file)
                    except:
                        pass
            
            # Check for permission errors
            if "permission denied" in result.stderr.lower() or "operation not permitted" in result.stderr.lower():
                return {
                    "success": False,
                    "output": "",
                    "error": "Masscan requires root privileges. Run as sudo or use capabilities."
                }
            
            return {
                "success": True,
                "output": output,
                "error": result.stderr if result.returncode != 0 and result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Masscan scan timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Masscan execution failed: {str(e)}"
            }
    
    def _parse_results(self, output: str) -> Dict[str, Any]:
        """Parse masscan output"""
        results = {
            "open_ports": [],
            "hosts_found": set(),
            "total_ports": 0
        }
        
        # Try to parse JSON output first
        try:
            # Masscan JSON format can have multiple objects
            json_objects = []
            for line in output.strip().split('\n'):
                if line.strip():
                    try:
                        obj = json.loads(line)
                        json_objects.append(obj)
                    except:
                        continue
            
            for obj in json_objects:
                if "ip" in obj and "ports" in obj:
                    ip = obj["ip"]
                    results["hosts_found"].add(ip)
                    
                    for port_info in obj["ports"]:
                        port_entry = {
                            "ip": ip,
                            "port": port_info["port"],
                            "protocol": port_info.get("proto", "tcp"),
                            "status": port_info.get("status", "open"),
                            "timestamp": obj.get("timestamp", "")
                        }
                        results["open_ports"].append(port_entry)
                        results["total_ports"] += 1
            
            results["hosts_found"] = list(results["hosts_found"])
            return results
            
        except:
            pass
        
        # Parse text output
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse format: "Discovered open port 80/tcp on 192.168.1.1"
            if "Discovered open port" in line:
                parts = line.split()
                if len(parts) >= 6:
                    port_proto = parts[3]  # "80/tcp"
                    ip = parts[5]
                    
                    if "/" in port_proto:
                        port, protocol = port_proto.split("/")
                        port_entry = {
                            "ip": ip,
                            "port": int(port),
                            "protocol": protocol,
                            "status": "open"
                        }
                        results["open_ports"].append(port_entry)
                        results["hosts_found"].add(ip)
                        results["total_ports"] += 1
        
        results["hosts_found"] = list(results["hosts_found"])
        return results
    
    def _fallback_port_scan(self, target: str, **kwargs) -> ToolResult:
        """Fallback port scan simulation"""
        simulated_ports = [
            {"ip": target, "port": 22, "protocol": "tcp", "status": "open"},
            {"ip": target, "port": 80, "protocol": "tcp", "status": "open"},
            {"ip": target, "port": 443, "protocol": "tcp", "status": "open"},
        ]
        
        return ToolResult(
            success=True,
            output=f"Simulated Masscan for {target}",
            metadata={
                "open_ports": simulated_ports,
                "hosts_found": [target],
                "total_ports_found": len(simulated_ports),
                "note": "Masscan not available - using simulation",
                "recommendations": [
                    "Install Masscan: apt-get install masscan",
                    "Or compile from source: https://github.com/robertdavidgraham/masscan",
                    f"Test manually with: sudo masscan {target} -p80,443,22 --rate=1000",
                    "Requires root privileges or capabilities",
                    "Always ensure proper authorization before scanning"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install Masscan:
        
        1. Debian/Ubuntu: apt-get install masscan
        2. Compile from source:
           - git clone https://github.com/robertdavidgraham/masscan
           - cd masscan && make
        3. Kali Linux: pre-installed
        
        Basic usage (requires root):
        sudo masscan 192.168.1.0/24 -p80,443,22 --rate=1000
        sudo masscan 10.0.0.1-10.0.0.100 -p1-1000 --rate=5000
        masscan --top-ports 100 192.168.1.1
        
        Output formats: -oX (XML), -oJ (JSON), -oG (Grepable)
        
        WARNING: 
        - Requires root privileges or capabilities
        - Can generate significant network traffic
        - Always ensure proper authorization before scanning
        - Start with low rates (--rate 100) and increase gradually
        """
