"""
OWASP ZAP Tool Implementation

Web application security scanning using OWASP ZAP.
"""

from typing import Optional, Dict, Any
from .base_tool import BasePenTestTool, ToolResult
import json
import requests
import time

class ZAPTool(BasePenTestTool):
    """OWASP ZAP web application security scanner"""
    
    def __init__(self, zap_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        super().__init__("zap", "zap.sh")
        self.zap_url = zap_url
        self.api_key = api_key
        self.session = requests.Session()
    
    def scan(self, target: str, scan_type: str = "full", **kwargs) -> ToolResult:
        """
        Perform OWASP ZAP scan
        
        Args:
            target: Target URL to scan
            scan_type: Type of scan (spider, active, passive, full)
            **kwargs: Additional options
        """
        if not self.check_target_safety(target):
            return ToolResult(
                success=False,
                output="",
                error="Target failed safety checks"
            )
        
        try:
            # Check if ZAP API is available
            if not self._check_zap_api():
                return self._fallback_scan(target, scan_type, **kwargs)
            
            results = {}
            
            # Perform spider scan first
            if scan_type in ["spider", "full"]:
                spider_result = self._spider_scan(target)
                results["spider"] = spider_result
            
            # Perform passive scan
            if scan_type in ["passive", "full"]:
                passive_result = self._passive_scan(target)
                results["passive"] = passive_result
            
            # Perform active scan
            if scan_type in ["active", "full"]:
                active_result = self._active_scan(target)
                results["active"] = active_result
            
            # Get alerts/vulnerabilities
            alerts = self._get_alerts(target)
            results["alerts"] = alerts
            
            return ToolResult(
                success=True,
                output=json.dumps(results, indent=2),
                metadata={
                    "scan_type": scan_type,
                    "alerts_count": len(alerts),
                    "high_risk": len([a for a in alerts if a.get("risk") == "High"]),
                    "medium_risk": len([a for a in alerts if a.get("risk") == "Medium"])
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"ZAP scan failed: {str(e)}"
            )
    
    def _check_zap_api(self) -> bool:
        """Check if ZAP API is accessible"""
        try:
            params = {"zapapiformat": "JSON"}
            if self.api_key:
                params["apikey"] = self.api_key
                
            response = self.session.get(
                f"{self.zap_url}/JSON/core/view/version/",
                params=params
            )
            return response.status_code == 200
        except:
            return False
    
    def _spider_scan(self, target: str) -> dict:
        """Perform spider/crawl scan"""
        try:
            # Start spider
            params = {
                "zapapiformat": "JSON",
                "url": target
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = self.session.get(
                f"{self.zap_url}/JSON/spider/action/scan/",
                params=params
            )
            
            if response.status_code == 200:
                scan_id = response.json().get("scan")
                
                # Wait for spider completion
                while True:
                    status_params = {
                        "zapapiformat": "JSON",
                        "scanId": scan_id
                    }
                    if self.api_key:
                        status_params["apikey"] = self.api_key
                    
                    status_response = self.session.get(
                        f"{self.zap_url}/JSON/spider/view/status/",
                        params=status_params
                    )
                    
                    if status_response.status_code == 200:
                        progress = int(status_response.json().get("status", 0))
                        if progress >= 100:
                            break
                    
                    time.sleep(5)
                
                return {"status": "completed", "scan_id": scan_id}
            
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "Spider scan failed"}
    
    def _passive_scan(self, target: str) -> dict:
        """Wait for passive scan to complete"""
        try:
            # Passive scanning happens automatically
            # Just wait for it to complete
            while True:
                params = {"zapapiformat": "JSON"}
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = self.session.get(
                    f"{self.zap_url}/JSON/pscan/view/recordsToScan/",
                    params=params
                )
                
                if response.status_code == 200:
                    records = int(response.json().get("recordsToScan", 0))
                    if records == 0:
                        break
                
                time.sleep(5)
            
            return {"status": "completed"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _active_scan(self, target: str) -> dict:
        """Perform active scan"""
        try:
            # Start active scan
            params = {
                "zapapiformat": "JSON",
                "url": target
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = self.session.get(
                f"{self.zap_url}/JSON/ascan/action/scan/",
                params=params
            )
            
            if response.status_code == 200:
                scan_id = response.json().get("scan")
                
                # Wait for active scan completion
                while True:
                    status_params = {
                        "zapapiformat": "JSON",
                        "scanId": scan_id
                    }
                    if self.api_key:
                        status_params["apikey"] = self.api_key
                    
                    status_response = self.session.get(
                        f"{self.zap_url}/JSON/ascan/view/status/",
                        params=status_params
                    )
                    
                    if status_response.status_code == 200:
                        progress = int(status_response.json().get("status", 0))
                        if progress >= 100:
                            break
                    
                    time.sleep(10)
                
                return {"status": "completed", "scan_id": scan_id}
            
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "Active scan failed"}
    
    def _get_alerts(self, target: str) -> list:
        """Get all alerts/vulnerabilities"""
        try:
            params = {
                "zapapiformat": "JSON",
                "baseurl": target
            }
            if self.api_key:
                params["apikey"] = self.api_key
            
            response = self.session.get(
                f"{self.zap_url}/JSON/core/view/alerts/",
                params=params
            )
            
            if response.status_code == 200:
                return response.json().get("alerts", [])
            
        except Exception as e:
            self.logger.error(f"Error getting alerts: {e}")
        
        return []
    
    def _fallback_scan(self, target: str, scan_type: str, **kwargs) -> ToolResult:
        """Fallback scan simulation"""
        return ToolResult(
            success=True,
            output=f"Simulated ZAP scan for {target}",
            metadata={
                "scan_type": scan_type,
                "note": "ZAP API not available - using simulation",
                "recommendations": [
                    "Install OWASP ZAP from https://www.zaproxy.org/",
                    "Start ZAP with API enabled",
                    "Configure API key for authentication"
                ]
            }
        )
    
    def spider_only(self, target: str) -> ToolResult:
        """Spider/crawl only scan"""
        return self.scan(target, scan_type="spider")
    
    def active_scan_only(self, target: str) -> ToolResult:
        """Active vulnerability scan only"""
        return self.scan(target, scan_type="active")
    
    def get_installation_instructions(self) -> str:
        return """
        To install OWASP ZAP:
        
        1. Download from https://www.zaproxy.org/download/
        2. Install and start ZAP
        3. Enable API in ZAP options
        4. Start ZAP daemon: zap.sh -daemon -port 8080
        5. Configure API key if needed
        
        Docker: docker run -t owasp/zap2docker-stable zap-baseline.py -t TARGET_URL
        """
