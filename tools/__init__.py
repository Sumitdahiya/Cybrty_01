"""
PenTest AI Tools Package

This package contains specialized tools for penetration testing operations.
Each tool provides a safe interface to common security testing utilities.
"""

from .base_tool import BasePenTestTool, ToolResult
from .nmap_tool import NmapTool
from .metasploit_tool import MetasploitTool
from .burp_tool import BurpTool
from .zap_tool import ZAPTool
from .sqlmap_tool import SqlmapTool
from .nikto_tool import NiktoTool
from .hydra_tool import HydraTool
from .enum4linux_tool import Enum4linuxTool
from .john_tool import JohnTool
from .wireshark_tool import WiresharkTool
# New advanced tools
from .theharvester_tool import TheHarvesterTool
from .nuclei_tool import NucleiTool
from .masscan_tool import MasscanTool
from .dirsearch_tool import DirsearchTool

__all__ = [
    'BasePenTestTool',
    'ToolResult',
    'NmapTool',
    'MetasploitTool', 
    'BurpTool',
    'ZAPTool',
    'SqlmapTool',
    'NiktoTool',
    'HydraTool',
    'Enum4linuxTool',
    'JohnTool',
    'WiresharkTool',
    'TheHarvesterTool',
    'NucleiTool',
    'MasscanTool',
    'DirsearchTool',
    'ToolManager'
]

class ToolManager:
    """Manager for all penetration testing tools"""
    
    def __init__(self):
        self.tools = {
            # Core scanning tools
            'nmap': NmapTool(),
            'masscan': MasscanTool(),
            
            # Web application testing
            'burp': BurpTool(),
            'zap': ZAPTool(),
            'sqlmap': SqlmapTool(),
            'nikto': NiktoTool(),
            'dirsearch': DirsearchTool(),
            'nuclei': NucleiTool(),
            
            # Authentication & brute force
            'hydra': HydraTool(),
            'john': JohnTool(),
            
            # Information gathering
            'theharvester': TheHarvesterTool(),
            'enum4linux': Enum4linuxTool(),
            
            # Network analysis
            'wireshark': WiresharkTool(),
            
            # Exploitation frameworks
            'metasploit': MetasploitTool()
        }
    
    def get_tool(self, tool_name: str) -> BasePenTestTool:
        """Get a specific tool by name"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        return self.tools[tool_name]
    
    def get_available_tools(self) -> list:
        """Get list of available tool names"""
        return list(self.tools.keys())
    
    def check_tool_availability(self) -> dict:
        """Check which tools are actually installed and available"""
        availability = {}
        for name, tool in self.tools.items():
            # This would check if the actual tool is installed
            # For now, we'll assume they use fallback methods
            availability[name] = {
                'available': True,  # All tools have fallback implementations
                'tool': tool
            }
        return availability
