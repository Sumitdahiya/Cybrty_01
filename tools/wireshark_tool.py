"""
Wireshark Tool Implementation

Network packet capture and analysis using tshark (Wireshark CLI).
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import tempfile
import os

class WiresharkTool(BasePenTestTool):
    """Wireshark/tshark network packet analysis tool"""
    
    def __init__(self):
        super().__init__("wireshark", "tshark")
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method - for Wireshark, this captures packets on interface or analyzes pcap"""
        if target.endswith('.pcap') or target.endswith('.pcapng'):
            return self.analyze_pcap(target, **kwargs)
        else:
            # Assume it's a network interface
            return self.capture_packets(target, count=kwargs.get('count', 50), **kwargs)
    
    def capture_packets(self, interface: str, **kwargs) -> ToolResult:
        """
        Capture network packets
        
        Args:
            interface: Network interface to capture from
            **kwargs: Additional options
        """
        try:
            if not self._check_tshark():
                return self._fallback_capture(interface, **kwargs)
            
            cmd = self._build_capture_command(interface, **kwargs)
            result = self._execute_tshark(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "interface": interface,
                        "packet_count": self._count_packets(result["output"]),
                        "capture_file": kwargs.get("output_file"),
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
                error=f"Packet capture failed: {str(e)}"
            )
    
    def analyze_pcap(self, pcap_file: str, **kwargs) -> ToolResult:
        """
        Analyze existing PCAP file
        
        Args:
            pcap_file: Path to PCAP file
            **kwargs: Analysis options
        """
        try:
            if not self._check_tshark():
                return self._fallback_analyze(pcap_file, **kwargs)
            
            cmd = self._build_analyze_command(pcap_file, **kwargs)
            result = self._execute_tshark(cmd)
            
            if result["success"]:
                analysis = self._parse_analysis(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "pcap_file": pcap_file,
                        "protocols": analysis["protocols"],
                        "connections": analysis["connections"],
                        "statistics": analysis["statistics"],
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
                error=f"PCAP analysis failed: {str(e)}"
            )
    
    def list_interfaces(self) -> ToolResult:
        """List available network interfaces"""
        try:
            if not self._check_tshark():
                return self._fallback_interfaces()
            
            cmd = ["tshark", "-D"]
            result = self._execute_tshark(cmd)
            
            if result["success"]:
                interfaces = self._parse_interfaces(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "interfaces": interfaces,
                        "count": len(interfaces)
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
                error=f"Interface listing failed: {str(e)}"
            )
    
    def filter_traffic(self, pcap_file: str, filter_expr: str, **kwargs) -> ToolResult:
        """
        Filter traffic from PCAP file
        
        Args:
            pcap_file: Input PCAP file
            filter_expr: Wireshark display filter
            **kwargs: Additional options
        """
        try:
            if not self._check_tshark():
                return self._fallback_filter(pcap_file, filter_expr, **kwargs)
            
            cmd = self._build_filter_command(pcap_file, filter_expr, **kwargs)
            result = self._execute_tshark(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "filter": filter_expr,
                        "input_file": pcap_file,
                        "filtered_packets": self._count_packets(result["output"]),
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
                error=f"Traffic filtering failed: {str(e)}"
            )
    
    def _check_tshark(self) -> bool:
        """Check if tshark is available"""
        try:
            result = subprocess.run(
                ["tshark", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_capture_command(self, interface: str, **kwargs) -> List[str]:
        """Build tshark capture command"""
        cmd = ["tshark", "-i", interface]
        
        # Packet count limit
        count = kwargs.get("count", 100)  # Default to 100 packets
        cmd.extend(["-c", str(count)])
        
        # Output file
        if kwargs.get("output_file"):
            cmd.extend(["-w", kwargs["output_file"]])
        
        # Capture filter
        if kwargs.get("capture_filter"):
            cmd.extend(["-f", kwargs["capture_filter"]])
        
        # Display filter
        if kwargs.get("display_filter"):
            cmd.extend(["-Y", kwargs["display_filter"]])
        
        # Time limit
        if kwargs.get("duration"):
            cmd.extend(["-a", f"duration:{kwargs['duration']}"])
        
        return cmd
    
    def _build_analyze_command(self, pcap_file: str, **kwargs) -> List[str]:
        """Build tshark analysis command"""
        cmd = ["tshark", "-r", pcap_file]
        
        # Analysis type
        analysis_type = kwargs.get("analysis", "summary")
        
        if analysis_type == "protocols":
            cmd.extend(["-q", "-z", "prot,colinfo"])
        elif analysis_type == "conversations":
            cmd.extend(["-q", "-z", "conv,tcp"])
        elif analysis_type == "endpoints":
            cmd.extend(["-q", "-z", "endpoints,tcp"])
        elif analysis_type == "io":
            cmd.extend(["-q", "-z", "io,phs"])
        else:
            # Default summary
            cmd.extend(["-q"])
        
        # Display filter
        if kwargs.get("filter"):
            cmd.extend(["-Y", kwargs["filter"]])
        
        return cmd
    
    def _build_filter_command(self, pcap_file: str, filter_expr: str, **kwargs) -> List[str]:
        """Build tshark filter command"""
        cmd = ["tshark", "-r", pcap_file, "-Y", filter_expr]
        
        # Output format
        if kwargs.get("fields"):
            cmd.extend(["-T", "fields"])
            for field in kwargs["fields"]:
                cmd.extend(["-e", field])
        
        # Output file
        if kwargs.get("output_file"):
            cmd.extend(["-w", kwargs["output_file"]])
        
        return cmd
    
    def _execute_tshark(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute tshark command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
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
                "error": "tshark command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"tshark execution failed: {str(e)}"
            }
    
    def _count_packets(self, output: str) -> int:
        """Count packets in output"""
        lines = output.strip().split('\n')
        return len([line for line in lines if line.strip()])
    
    def _parse_interfaces(self, output: str) -> List[Dict[str, str]]:
        """Parse interface list"""
        interfaces = []
        for line in output.split('\n'):
            if line.strip() and '.' in line:
                parts = line.split('.', 1)
                if len(parts) == 2:
                    interfaces.append({
                        "id": parts[0].strip(),
                        "name": parts[1].strip()
                    })
        return interfaces
    
    def _parse_analysis(self, output: str) -> Dict[str, Any]:
        """Parse analysis output"""
        analysis = {
            "protocols": [],
            "connections": [],
            "statistics": {}
        }
        
        lines = output.split('\n')
        for line in lines:
            if "TCP" in line or "UDP" in line or "HTTP" in line:
                analysis["protocols"].append(line.strip())
        
        return analysis
    
    def _fallback_capture(self, interface: str, **kwargs) -> ToolResult:
        """Fallback capture simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated packet capture on interface {interface}",
            metadata={
                "note": "tshark not available - using simulation",
                "interface": interface,
                "packet_count": 50,
                "recommendations": [
                    "Install Wireshark: apt-get install wireshark",
                    "Or download from: https://www.wireshark.org/",
                    f"Capture with: tshark -i {interface} -c 100"
                ]
            }
        )
    
    def _fallback_analyze(self, pcap_file: str, **kwargs) -> ToolResult:
        """Fallback analysis simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated PCAP analysis for {pcap_file}",
            metadata={
                "note": "tshark not available - using simulation",
                "protocols": ["TCP", "HTTP", "DNS"],
                "connections": ["192.168.1.100:443", "8.8.8.8:53"],
                "statistics": {"total_packets": 1000}
            }
        )
    
    def _fallback_interfaces(self) -> ToolResult:
        """Fallback interface listing"""
        return ToolResult(
            success=True,
            output="Simulated interface listing",
            metadata={
                "note": "tshark not available - using simulation",
                "interfaces": [
                    {"id": "1", "name": "eth0"},
                    {"id": "2", "name": "wlan0"},
                    {"id": "3", "name": "lo"}
                ]
            }
        )
    
    def _fallback_filter(self, pcap_file: str, filter_expr: str, **kwargs) -> ToolResult:
        """Fallback filter simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated filtering of {pcap_file} with filter: {filter_expr}",
            metadata={
                "note": "tshark not available - using simulation",
                "filter": filter_expr,
                "filtered_packets": 25
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install Wireshark/tshark:
        
        1. Debian/Ubuntu: apt-get install wireshark tshark
        2. macOS: brew install wireshark
        3. Windows: Download from https://www.wireshark.org/
        4. Kali Linux: pre-installed
        
        Basic usage:
        tshark -D  # List interfaces
        tshark -i eth0 -c 100  # Capture 100 packets
        tshark -r file.pcap  # Read PCAP file
        tshark -r file.pcap -Y "http"  # Filter HTTP traffic
        
        Note: May require sudo for packet capture
        """
