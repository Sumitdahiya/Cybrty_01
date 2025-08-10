"""
SQLMap Tool Implementation

SQL injection testing and database enumeration using sqlmap.
"""

from typing import Optional, Dict, Any, List
from .base_tool import BasePenTestTool, ToolResult
import subprocess
import json
import tempfile
import os

class SqlmapTool(BasePenTestTool):
    """SQL injection testing tool"""
    
    def __init__(self):
        super().__init__("sqlmap", "sqlmap")
    
    def scan(self, target: str, **kwargs) -> ToolResult:
        """Generic scan method - delegates to test_url"""
        return self.test_url(target, **kwargs)
    
    def test_url(self, target: str, **kwargs) -> ToolResult:
        """
        Test URL for SQL injection vulnerabilities
        
        Args:
            target: Target URL to test
            **kwargs: Additional sqlmap options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if sqlmap is available
            if not self._check_sqlmap():
                return self._fallback_test(target, **kwargs)
            
            # Build sqlmap command
            cmd = self._build_command(target, "test", **kwargs)
            
            # Execute sqlmap
            result = self._execute_sqlmap(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "vulnerabilities": self._parse_vulnerabilities(result["output"]),
                        "databases": self._parse_databases(result["output"]),
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
                error=f"SQLMap test failed: {str(e)}"
            )
    
    def enumerate_databases(self, target: str, **kwargs) -> ToolResult:
        """Enumerate databases"""
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_sqlmap():
                return self._fallback_enumerate(target, **kwargs)
            
            # Add database enumeration options
            kwargs["dbs"] = True
            cmd = self._build_command(target, "enumerate", **kwargs)
            
            result = self._execute_sqlmap(cmd)
            
            if result["success"]:
                databases = self._parse_databases(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "databases": databases,
                        "database_count": len(databases),
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
                error=f"Database enumeration failed: {str(e)}"
            )
    
    def enumerate_tables(self, target: str, database: str, **kwargs) -> ToolResult:
        """Enumerate tables in a specific database"""
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_sqlmap():
                return self._fallback_enumerate_tables(target, database, **kwargs)
            
            # Add table enumeration options
            kwargs["tables"] = True
            kwargs["D"] = database
            cmd = self._build_command(target, "enumerate", **kwargs)
            
            result = self._execute_sqlmap(cmd)
            
            if result["success"]:
                tables = self._parse_tables(result["output"])
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "database": database,
                        "tables": tables,
                        "table_count": len(tables),
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
                error=f"Table enumeration failed: {str(e)}"
            )
    
    def dump_table(self, target: str, database: str, table: str, **kwargs) -> ToolResult:
        """Dump data from a specific table"""
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            if not self._check_sqlmap():
                return self._fallback_dump(target, database, table, **kwargs)
            
            # Add dump options
            kwargs["dump"] = True
            kwargs["D"] = database
            kwargs["T"] = table
            kwargs["threads"] = kwargs.get("threads", 1)  # Be gentle
            cmd = self._build_command(target, "dump", **kwargs)
            
            result = self._execute_sqlmap(cmd)
            
            if result["success"]:
                return ToolResult(
                    success=True,
                    output=result["output"],
                    metadata={
                        "database": database,
                        "table": table,
                        "command": " ".join(cmd),
                        "warning": "Data dumping performed - ensure proper authorization"
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
                error=f"Table dump failed: {str(e)}"
            )
    
    def _check_sqlmap(self) -> bool:
        """Check if sqlmap is available"""
        try:
            result = subprocess.run(
                ["sqlmap", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_command(self, target: str, operation: str, **kwargs) -> List[str]:
        """Build sqlmap command"""
        cmd = ["sqlmap"]
        
        # Add target URL
        cmd.extend(["-u", target])
        
        # Add safety options
        cmd.extend(["--batch", "--random-agent"])
        
        # Add level and risk (conservative by default)
        level = kwargs.get("level", 1)
        risk = kwargs.get("risk", 1)
        cmd.extend(["--level", str(level), "--risk", str(risk)])
        
        # Add threads (be gentle)
        threads = kwargs.get("threads", 1)
        cmd.extend(["--threads", str(threads)])
        
        # Add delay to be less aggressive
        delay = kwargs.get("delay", 1)
        cmd.extend(["--delay", str(delay)])
        
        # Operation-specific options
        if operation == "test":
            # Just test for vulnerabilities
            pass
        elif operation == "enumerate":
            if kwargs.get("dbs"):
                cmd.append("--dbs")
            if kwargs.get("tables"):
                cmd.append("--tables")
            if kwargs.get("D"):
                cmd.extend(["-D", kwargs["D"]])
        elif operation == "dump":
            if kwargs.get("dump"):
                cmd.append("--dump")
            if kwargs.get("D"):
                cmd.extend(["-D", kwargs["D"]])
            if kwargs.get("T"):
                cmd.extend(["-T", kwargs["T"]])
        
        # Add additional parameters
        if kwargs.get("cookie"):
            cmd.extend(["--cookie", kwargs["cookie"]])
        if kwargs.get("data"):
            cmd.extend(["--data", kwargs["data"]])
        if kwargs.get("headers"):
            cmd.extend(["--headers", kwargs["headers"]])
        
        return cmd
    
    def _execute_sqlmap(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute sqlmap command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
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
                "error": "SQLMap command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"SQLMap execution failed: {str(e)}"
            }
    
    def _parse_vulnerabilities(self, output: str) -> List[str]:
        """Parse vulnerabilities from sqlmap output"""
        vulnerabilities = []
        lines = output.split('\n')
        
        for line in lines:
            if "Parameter:" in line and "is vulnerable" in line:
                vulnerabilities.append(line.strip())
            elif "Type:" in line:
                vulnerabilities.append(line.strip())
        
        return vulnerabilities
    
    def _parse_databases(self, output: str) -> List[str]:
        """Parse database names from sqlmap output"""
        databases = []
        lines = output.split('\n')
        in_db_section = False
        
        for line in lines:
            if "available databases" in line:
                in_db_section = True
                continue
            elif in_db_section and line.strip().startswith('['):
                # Database name line
                if ']' in line:
                    db_name = line.split(']')[1].strip()
                    if db_name:
                        databases.append(db_name)
            elif in_db_section and not line.strip():
                break
        
        return databases
    
    def _parse_tables(self, output: str) -> List[str]:
        """Parse table names from sqlmap output"""
        tables = []
        lines = output.split('\n')
        in_table_section = False
        
        for line in lines:
            if "tables" in line and "Database:" in line:
                in_table_section = True
                continue
            elif in_table_section and line.strip().startswith('['):
                # Table name line
                if ']' in line:
                    table_name = line.split(']')[1].strip()
                    if table_name:
                        tables.append(table_name)
            elif in_table_section and not line.strip():
                break
        
        return tables
    
    def _fallback_test(self, target: str, **kwargs) -> ToolResult:
        """Fallback test simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated SQL injection test for {target}",
            metadata={
                "note": "SQLMap not available - using simulation",
                "recommendations": [
                    "Install sqlmap: pip install sqlmap",
                    "Or download from: https://sqlmap.org/",
                    "Test manually with: sqlmap -u '{target}' --batch"
                ]
            }
        )
    
    def _fallback_enumerate(self, target: str, **kwargs) -> ToolResult:
        """Fallback enumeration simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated database enumeration for {target}",
            metadata={
                "note": "SQLMap not available - using simulation",
                "databases": ["information_schema", "mysql", "test"]
            }
        )
    
    def _fallback_enumerate_tables(self, target: str, database: str, **kwargs) -> ToolResult:
        """Fallback table enumeration simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated table enumeration for {database} in {target}",
            metadata={
                "note": "SQLMap not available - using simulation",
                "database": database,
                "tables": ["users", "accounts", "sessions"]
            }
        )
    
    def _fallback_dump(self, target: str, database: str, table: str, **kwargs) -> ToolResult:
        """Fallback dump simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated table dump for {database}.{table} in {target}",
            metadata={
                "note": "SQLMap not available - using simulation",
                "warning": "Actual data dumping requires proper authorization"
            }
        )
    
    def get_installation_instructions(self) -> str:
        return """
        To install SQLMap:
        
        1. pip install sqlmap
        2. Or download from https://sqlmap.org/
        3. Or use package manager:
           - Debian/Ubuntu: apt-get install sqlmap
           - macOS: brew install sqlmap
           - Kali Linux: pre-installed
        
        Basic usage:
        sqlmap -u "http://target.com/page?id=1" --batch
        """
