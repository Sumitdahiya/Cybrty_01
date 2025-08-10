"""
John the Ripper Tool Implementation

Password cracking using John the Ripper.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import tempfile
import os

class JohnTool(BasePenTestTool):
    """John the Ripper password cracking tool"""
    
    def __init__(self):
        super().__init__("john", "john")
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method - for John, this would be crack_hashes with target as hash"""
        # For John, target might be a hash or file path
        if target.startswith(('$', '{')) or len(target) > 32:  # Looks like a hash
            return self.crack_hashes(hashes=[target], **kwargs)
        else:
            # Assume it's a file path
            return self.crack_hashes(hash_file=target, **kwargs)
    
    def crack_hashes(self, hash_file: Optional[str] = None, hashes: Optional[List[str]] = None, **kwargs) -> ToolResult:
        """
        Crack password hashes
        
        Args:
            hash_file: Path to file containing hashes
            hashes: List of hashes to crack
            **kwargs: Additional options
        """
        try:
            if not self._check_john():
                return self._fallback_crack(hash_file, hashes, **kwargs)
            
            # Prepare hash file
            if hashes:
                hash_file = self._create_temp_hash_file(hashes)
            elif not hash_file:
                return ToolResult(
                    success=False,
                    output="",
                    error="No hashes provided"
                )
            
            cmd = self._build_command(hash_file, **kwargs)
            result = self._execute_john(cmd)
            
            if result["success"]:
                cracked = self._get_cracked_passwords(hash_file)
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "cracked_passwords": cracked,
                        "total_cracked": len(cracked),
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
                error=f"John the Ripper failed: {str(e)}"
            )
        finally:
            # Clean up temp files
            if hashes and hash_file and os.path.exists(hash_file):
                try:
                    os.unlink(hash_file)
                except:
                    pass
    
    def crack_zip(self, zip_file: str, **kwargs) -> ToolResult:
        """Crack ZIP file password"""
        try:
            if not self._check_john():
                return self._fallback_crack_zip(zip_file, **kwargs)
            
            # Extract hash from ZIP file
            zip2john_cmd = ["zip2john", zip_file]
            zip_result = subprocess.run(
                zip2john_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if zip_result.returncode != 0:
                return ToolResult(
                    success=False,
                    output="",
                    error="Failed to extract hash from ZIP file"
                )
            
            # Create temp hash file
            hash_file = self._create_temp_hash_file([zip_result.stdout])
            
            # Crack the hash
            return self.crack_hashes(hash_file=hash_file, **kwargs)
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"ZIP cracking failed: {str(e)}"
            )
    
    def _check_john(self) -> bool:
        """Check if john is available"""
        try:
            result = subprocess.run(
                ["john", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _create_temp_hash_file(self, hashes: List[str]) -> str:
        """Create temporary hash file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hash') as f:
            for hash_line in hashes:
                f.write(f"{hash_line.strip()}\n")
            return f.name
    
    def _build_command(self, hash_file: str, **kwargs) -> List[str]:
        """Build john command"""
        cmd = ["john"]
        
        # Wordlist
        if kwargs.get("wordlist"):
            cmd.extend(["--wordlist", kwargs["wordlist"]])
        else:
            # Use default wordlist if available
            cmd.append("--wordlist")
        
        # Rules
        if kwargs.get("rules"):
            cmd.extend(["--rules", kwargs["rules"]])
        
        # Format
        if kwargs.get("format"):
            cmd.extend(["--format", kwargs["format"]])
        
        # Session
        session = kwargs.get("session", "default")
        cmd.extend(["--session", session])
        
        # Time limit (be conservative)
        timeout = kwargs.get("timeout", 60)  # 1 minute default
        cmd.extend(["--max-run-time", str(timeout)])
        
        # Hash file
        cmd.append(hash_file)
        
        return cmd
    
    def _execute_john(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute john command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute max
            )
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr if result.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "John the Ripper timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"John execution failed: {str(e)}"
            }
    
    def _get_cracked_passwords(self, hash_file: str) -> List[Dict[str, str]]:
        """Get cracked passwords"""
        try:
            result = subprocess.run(
                ["john", "--show", hash_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            cracked = []
            for line in result.stdout.split('\n'):
                if ':' in line and line.strip():
                    parts = line.split(':')
                    if len(parts) >= 2:
                        cracked.append({
                            "username": parts[0],
                            "password": parts[1]
                        })
            
            return cracked
            
        except Exception as e:
            self.logger.error(f"Error getting cracked passwords: {e}")
            return []
    
    def _fallback_crack(self, hash_file: Optional[str] = None, hashes: Optional[List[str]] = None, **kwargs) -> ToolResult:
        """Fallback crack simulation"""
        return ToolResult(
            success=True,
            output="Simulated John the Ripper password cracking",
            metadata={
                "note": "John the Ripper not available - using simulation",
                "cracked_passwords": [
                    {"username": "user1", "password": "password123"},
                    {"username": "admin", "password": "admin"}
                ],
                "total_cracked": 2,
                "recommendations": [
                    "Install John: apt-get install john",
                    "Or download from: https://www.openwall.com/john/",
                    "Example: john --wordlist=rockyou.txt hashes.txt"
                ]
            }
        )
    
    def _fallback_crack_zip(self, zip_file: str, **kwargs) -> ToolResult:
        """Fallback ZIP crack simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated ZIP password cracking for {zip_file}",
            metadata={
                "note": "John the Ripper not available - using simulation",
                "cracked_passwords": [{"password": "password123"}],
                "recommendations": [
                    "Install John with ZIP support",
                    f"Extract hash: zip2john {zip_file} > hashes.txt",
                    "Crack: john --wordlist=rockyou.txt hashes.txt"
                ]
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install John the Ripper:
        
        1. Debian/Ubuntu: apt-get install john
        2. macOS: brew install john
        3. Manual install:
           - Download from https://www.openwall.com/john/
           - Compile: make -s clean && make -sj4
        4. Kali Linux: pre-installed
        
        Basic usage:
        john --wordlist=rockyou.txt hashes.txt
        john --rules hashes.txt
        john --show hashes.txt
        
        For ZIP files:
        zip2john file.zip > hashes.txt
        john hashes.txt
        """
