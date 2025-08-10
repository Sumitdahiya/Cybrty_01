#!/usr/bin/env python3
"""
MongoDB Writer for CrewAI UI Consumption

This script writes data to MongoDB in the exact format expected by the CrewAI UI.
It ensures compatibility with Prisma schema and provides UI-ready data structures.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mongodb_integration import CrewAIMongoDB
from datetime import datetime, timezone
import json
from bson import ObjectId

class CrewAIUIDataWriter:
    """Writes data to MongoDB for CrewAI UI consumption"""
    
    def __init__(self):
        self.mongo = CrewAIMongoDB()
        print("📝 CrewAI UI Data Writer - MongoDB Integration")
    
    def write_ui_compatible_agents(self):
        """Write agents in CrewAI UI compatible format"""
        
        print("\n🤖 Writing UI-Compatible Agents...")
        
        # UI-specific agent data with proper field mapping
        ui_agents = [
            {
                "role": "Senior Penetration Tester",
                "goal": "Lead comprehensive security assessments and coordinate pentesting operations",
                "backstory": "Senior cybersecurity professional with 15+ years of experience in penetration testing, vulnerability assessment, and security consulting. Certified OSCP, CISSP, and CEH.",
                "tools": "nmap,metasploit,burpsuite,enum4linux,sqlmap,nikto,gobuster,john,hashcat,bloodhound",
                "allowDelegation": True,
                "verbose": True,
                "image": None,
                "specialization": "Penetration Testing Leadership",
                "experience_years": 15,
                "certifications": ["OSCP", "CISSP", "CEH", "GPEN"],
                "primary_expertise": ["Network Penetration", "Web Application Security", "Red Team Operations"]
            },
            {
                "role": "OSINT Intelligence Analyst",
                "goal": "Gather and analyze open-source intelligence to support cybersecurity operations",
                "backstory": "Intelligence analyst specializing in OSINT collection, threat intelligence, and reconnaissance. Expert in social media intelligence and digital footprint analysis.",
                "tools": "maltego,theharvester,recon-ng,shodan,spiderfoot,amass,subfinder,googleharvester,haveibeenpwned",
                "allowDelegation": False,
                "verbose": True,
                "image": None,
                "specialization": "Open Source Intelligence",
                "experience_years": 8,
                "certifications": ["GCTI", "SANS SEC487"],
                "primary_expertise": ["OSINT Collection", "Social Engineering Recon", "Digital Footprinting"]
            },
            {
                "role": "API Security Specialist",
                "goal": "Conduct specialized security assessments of REST APIs, GraphQL, and microservices architectures",
                "backstory": "API security expert with deep knowledge of modern web service architectures. Specializes in OAuth, JWT, and API gateway security testing.",
                "tools": "postman,insomnia,burpsuite,owasp-zap,ffuf,nuclei,jwt-tool,oauth-scanner,graphql-voyager",
                "allowDelegation": False,
                "verbose": True,
                "image": None,
                "specialization": "API Security Testing",
                "experience_years": 6,
                "certifications": ["GWEB", "API Security Professional"],
                "primary_expertise": ["REST API Testing", "GraphQL Security", "OAuth/JWT Analysis"]
            },
            {
                "role": "Cloud Security Architect",
                "goal": "Assess cloud infrastructure security across AWS, Azure, and GCP environments",
                "backstory": "Cloud security specialist with expertise in container security, serverless architectures, and cloud-native security controls. AWS and Azure certified.",
                "tools": "prowler,scout-suite,cloudsploit,pacbot,kubernetes-bench,docker-bench,terraform-compliance",
                "allowDelegation": True,
                "verbose": True,
                "image": None,
                "specialization": "Cloud Security Assessment",
                "experience_years": 7,
                "certifications": ["AWS Security Specialty", "Azure Security Engineer", "CKS"],
                "primary_expertise": ["Cloud Configuration Review", "Container Security", "IaC Security"]
            },
            {
                "role": "Mobile Application Security Tester",
                "goal": "Perform comprehensive security testing of iOS and Android mobile applications",
                "backstory": "Mobile security expert with deep knowledge of mobile application architectures, reverse engineering, and mobile-specific attack vectors.",
                "tools": "mobsf,frida,objection,apktool,jadx,class-dump,idb,needle,drozer,qark",
                "allowDelegation": False,
                "verbose": True,
                "image": None,
                "specialization": "Mobile Application Security",
                "experience_years": 5,
                "certifications": ["GMOB", "Mobile Security Professional"],
                "primary_expertise": ["iOS Security Testing", "Android Security Testing", "Mobile Reverse Engineering"]
            },
            {
                "role": "Threat Hunting Analyst",
                "goal": "Proactively hunt for advanced threats and analyze security incidents",
                "backstory": "Cybersecurity analyst specializing in threat hunting, incident response, and advanced persistent threat detection. Expert in behavioral analysis and threat intelligence.",
                "tools": "splunk,elk-stack,sigma,yara,osquery,volatility,autopsy,wireshark,zeek,suricata",
                "allowDelegation": True,
                "verbose": True,
                "image": None,
                "specialization": "Threat Hunting & Analysis",
                "experience_years": 9,
                "certifications": ["GCTH", "GCFA", "GCIH"],
                "primary_expertise": ["Advanced Threat Detection", "Incident Response", "Malware Analysis"]
            }
        ]
        
        agent_ids = []
        for i, agent_data in enumerate(ui_agents, 1):
            # Add timestamps in the format expected by the UI
            agent_data['created_at'] = datetime.now(timezone.utc)
            agent_data['updated_at'] = datetime.now(timezone.utc)
            
            agent_id = self.mongo.create_agent(agent_data)
            agent_ids.append(agent_id)
            print(f"   ✅ UI Agent {i}: {agent_data['role']} (ID: {agent_id})")
        
        return agent_ids
    
    def write_ui_compatible_missions(self, agent_ids):
        """Write missions in CrewAI UI compatible format"""
        
        print("\n🚀 Writing UI-Compatible Missions...")
        
        # Multiple mission scenarios for the UI
        ui_missions = [
            {
                "name": "Enterprise Web Application Security Assessment",
                "description": "Comprehensive security testing of a large-scale enterprise web application with multiple modules and integrations",
                "target": "enterprise-app.cybrty.com",
                "agent_ids": agent_ids[:4],  # Use first 4 agents
                "tasks": json.dumps([
                    {
                        "id": 1,
                        "name": "Application Discovery and Enumeration",
                        "description": "Map the application architecture and identify all endpoints",
                        "agent": "OSINT Intelligence Analyst",
                        "status": "pending",
                        "priority": "high"
                    },
                    {
                        "id": 2,
                        "name": "Authentication and Authorization Testing",
                        "description": "Test authentication mechanisms and access controls",
                        "agent": "Senior Penetration Tester",
                        "status": "pending",
                        "priority": "critical"
                    },
                    {
                        "id": 3,
                        "name": "API Security Assessment",
                        "description": "Comprehensive testing of REST and GraphQL APIs",
                        "agent": "API Security Specialist",
                        "status": "pending",
                        "priority": "high"
                    }
                ]),
                "verbose": True,
                "process": "SEQUENTIAL",
                "priority": "high",
                "estimated_duration": "10 days",
                "compliance_requirements": ["OWASP ASVS", "PCI DSS", "SOC 2"]
            },
            {
                "name": "Cloud Infrastructure Security Review",
                "description": "Security assessment of AWS cloud infrastructure including containers and serverless components",
                "target": "aws-infrastructure.cybrty.com",
                "agent_ids": [agent_ids[3], agent_ids[0]],  # Cloud architect + Pentester
                "tasks": json.dumps([
                    {
                        "id": 1,
                        "name": "Cloud Configuration Assessment",
                        "description": "Review AWS security groups, IAM policies, and service configurations",
                        "agent": "Cloud Security Architect",
                        "status": "pending",
                        "priority": "critical"
                    },
                    {
                        "id": 2,
                        "name": "Container Security Audit",
                        "description": "Assess container images and Kubernetes cluster security",
                        "agent": "Cloud Security Architect",
                        "status": "pending",
                        "priority": "high"
                    }
                ]),
                "verbose": True,
                "process": "HIERARCHICAL",
                "priority": "critical",
                "estimated_duration": "7 days",
                "compliance_requirements": ["CIS Benchmarks", "AWS Well-Architected"]
            },
            {
                "name": "Mobile Banking App Security Assessment",
                "description": "Complete security evaluation of iOS and Android mobile banking applications",
                "target": "mobile-banking-app",
                "agent_ids": [agent_ids[4], agent_ids[1]],  # Mobile specialist + OSINT
                "tasks": json.dumps([
                    {
                        "id": 1,
                        "name": "Mobile App Static Analysis",
                        "description": "Static code analysis and reverse engineering of mobile apps",
                        "agent": "Mobile Application Security Tester",
                        "status": "pending",
                        "priority": "critical"
                    },
                    {
                        "id": 2,
                        "name": "Runtime Application Security Testing",
                        "description": "Dynamic testing using instrumentation and hooking",
                        "agent": "Mobile Application Security Tester",
                        "status": "pending",
                        "priority": "high"
                    }
                ]),
                "verbose": True,
                "process": "SEQUENTIAL",
                "priority": "critical",
                "estimated_duration": "14 days",
                "compliance_requirements": ["OWASP MASVS", "PCI Mobile Payment", "Financial Services Security"]
            },
            {
                "name": "Advanced Persistent Threat Simulation",
                "description": "Red team exercise simulating advanced persistent threat scenarios",
                "target": "corporate-network.cybrty.com",
                "agent_ids": [agent_ids[0], agent_ids[5]],  # Pentester + Threat hunter
                "tasks": json.dumps([
                    {
                        "id": 1,
                        "name": "Initial Access and Persistence",
                        "description": "Establish initial foothold and persistence mechanisms",
                        "agent": "Senior Penetration Tester",
                        "status": "pending",
                        "priority": "critical"
                    },
                    {
                        "id": 2,
                        "name": "Threat Detection Evasion",
                        "description": "Test security monitoring and detection capabilities",
                        "agent": "Threat Hunting Analyst",
                        "status": "pending",
                        "priority": "high"
                    }
                ]),
                "verbose": True,
                "process": "SEQUENTIAL",
                "priority": "critical",
                "estimated_duration": "21 days",
                "compliance_requirements": ["NIST Cybersecurity Framework", "MITRE ATT&CK"]
            }
        ]
        
        mission_ids = []
        for i, mission_data in enumerate(ui_missions, 1):
            # Add timestamps and status
            mission_data['created_at'] = datetime.now(timezone.utc)
            mission_data['updated_at'] = datetime.now(timezone.utc)
            mission_data['status'] = 'created'
            
            mission_id = self.mongo.create_mission(mission_data)
            mission_ids.append(mission_id)
            print(f"   ✅ UI Mission {i}: {mission_data['name']} (ID: {mission_id})")
        
        return mission_ids
    
    def write_sample_tool_results(self):
        """Write sample tool results for UI demonstration"""
        
        print("\n🔧 Writing Sample Tool Results...")
        
        # Sample enum4linux results
        enum4linux_results = [
            {
                "tool": "enum4linux",
                "target": "192.168.1.100",
                "result": {
                    "success": True,
                    "command": "enum4linux -a 192.168.1.100",
                    "shares": [
                        {"name": "ADMIN$", "type": "Disk", "comment": "Remote Admin"},
                        {"name": "C$", "type": "Disk", "comment": "Default share"},
                        {"name": "IPC$", "type": "IPC", "comment": "Remote IPC"},
                        {"name": "NETLOGON", "type": "Disk", "comment": "Logon server share"},
                        {"name": "SYSVOL", "type": "Disk", "comment": "Logon server share"}
                    ],
                    "users": ["Administrator", "Guest", "krbtgt", "testuser", "serviceaccount"],
                    "groups": ["Domain Admins", "Domain Users", "Enterprise Admins", "Schema Admins"],
                    "os_info": {"os": "Windows Server 2019 Standard 17763"}
                }
            },
            {
                "tool": "nmap",
                "target": "cybersecurity-platform.company.com",
                "result": {
                    "success": True,
                    "command": "nmap -sV -sC cybersecurity-platform.company.com",
                    "open_ports": [
                        {"port": 22, "service": "ssh", "version": "OpenSSH 8.2p1"},
                        {"port": 80, "service": "http", "version": "nginx 1.18.0"},
                        {"port": 443, "service": "https", "version": "nginx 1.18.0"},
                        {"port": 3306, "service": "mysql", "version": "MySQL 8.0.25"}
                    ],
                    "host_status": "up",
                    "scan_time": "45.23 seconds"
                }
            },
            {
                "tool": "sqlmap",
                "target": "api.cybersecurity-platform.company.com/api/v1/users",
                "result": {
                    "success": True,
                    "command": "sqlmap -u 'api.cybersecurity-platform.company.com/api/v1/users?id=1' --dbs",
                    "vulnerability_found": True,
                    "injection_type": "Boolean-based blind",
                    "databases": ["information_schema", "cybrty_app", "mysql", "performance_schema"],
                    "risk_level": "Critical",
                    "recommendation": "Use parameterized queries to prevent SQL injection"
                }
            }
        ]
        
        result_ids = []
        for i, result_data in enumerate(enum4linux_results, 1):
            result_id = self.mongo.store_tool_result(
                result_data["tool"],
                result_data["target"],
                result_data["result"]
            )
            result_ids.append(result_id)
            print(f"   ✅ Tool Result {i}: {result_data['tool']} on {result_data['target']} (ID: {result_id})")
        
        return result_ids
    
    def write_pentest_results(self):
        """Write comprehensive pentest results"""
        
        print("\n🔒 Writing Penetration Test Results...")
        
        pentest_results = [
            {
                "target": "cybersecurity-platform.company.com",
                "test_type": "comprehensive",
                "severity": "critical",
                "findings": {
                    "critical": 2,
                    "high": 5,
                    "medium": 8,
                    "low": 12,
                    "info": 15
                },
                "vulnerabilities": [
                    {
                        "title": "SQL Injection in User Authentication",
                        "severity": "Critical",
                        "cvss_score": 9.8,
                        "description": "SQL injection vulnerability allows authentication bypass",
                        "impact": "Complete database compromise possible",
                        "recommendation": "Implement parameterized queries"
                    },
                    {
                        "title": "Cross-Site Scripting (XSS) in User Profile",
                        "severity": "High",
                        "cvss_score": 7.2,
                        "description": "Stored XSS vulnerability in user profile fields",
                        "impact": "Session hijacking and privilege escalation",
                        "recommendation": "Implement proper input validation and output encoding"
                    }
                ],
                "executive_summary": "Critical security vulnerabilities identified requiring immediate attention",
                "methodology": "OWASP WSTG 4.2",
                "compliance_status": {
                    "PCI_DSS": "Non-compliant",
                    "SOC_2": "Major deficiencies",
                    "ISO_27001": "Gaps identified"
                }
            },
            {
                "target": "api.cybersecurity-platform.company.com",
                "test_type": "api_security",
                "severity": "high",
                "findings": {
                    "critical": 1,
                    "high": 3,
                    "medium": 4,
                    "low": 6,
                    "info": 8
                },
                "vulnerabilities": [
                    {
                        "title": "Broken Authentication in JWT Implementation",
                        "severity": "Critical",
                        "cvss_score": 8.9,
                        "description": "JWT tokens accept 'none' algorithm allowing signature bypass",
                        "impact": "Complete authentication bypass",
                        "recommendation": "Enforce strong JWT signature algorithms"
                    }
                ],
                "executive_summary": "API security assessment reveals authentication vulnerabilities",
                "methodology": "OWASP API Security Top 10",
                "compliance_status": {
                    "API_Security_Standard": "Non-compliant"
                }
            }
        ]
        
        result_ids = []
        for i, result_data in enumerate(pentest_results, 1):
            result_id = self.mongo.store_pentest_result(result_data)
            result_ids.append(result_id)
            print(f"   ✅ Pentest Result {i}: {result_data['target']} - {result_data['severity']} (ID: {result_id})")
        
        return result_ids
    
    def generate_ui_dashboard_data(self):
        """Generate data specifically for UI dashboard consumption"""
        
        print("\n📊 Generating UI Dashboard Data...")
        
        # Get current statistics
        stats = self.mongo.get_agent_stats()
        
        # Enhanced statistics for UI
        dashboard_data = {
            "overview": {
                "total_agents": stats['total_agents'],
                "active_missions": stats['total_missions'],
                "completed_assessments": stats['completed_missions'],
                "total_vulnerabilities_found": 42,  # Sample data
                "critical_findings": 8,
                "security_score": 73.5
            },
            "recent_activity": [
                {
                    "type": "vulnerability_found",
                    "title": "Critical SQL Injection Discovered",
                    "target": "api.cybersecurity-platform.company.com",
                    "severity": "critical",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": "API Security Specialist"
                },
                {
                    "type": "scan_completed",
                    "title": "Network Scan Completed",
                    "target": "192.168.1.0/24",
                    "status": "completed",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": "Senior Penetration Tester"
                },
                {
                    "type": "mission_started",
                    "title": "Mobile App Assessment Started",
                    "target": "mobile-banking-app",
                    "status": "in_progress",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": "Mobile Application Security Tester"
                }
            ],
            "agent_performance": [
                {"agent": "Senior Penetration Tester", "assessments": 15, "findings": 45, "efficiency": 92},
                {"agent": "API Security Specialist", "assessments": 8, "findings": 28, "efficiency": 88},
                {"agent": "Cloud Security Architect", "assessments": 6, "findings": 22, "efficiency": 85}
            ],
            "threat_landscape": {
                "trending_vulnerabilities": ["SQL Injection", "XSS", "Broken Authentication"],
                "attack_vectors": ["Web Application", "API", "Network Services"],
                "industry_threats": ["Ransomware", "Data Breach", "Supply Chain Attack"]
            }
        }
        
        # Store dashboard data using the new method
        dashboard_id = self.mongo.store_dashboard_data(dashboard_data)
        print(f"   ✅ Dashboard Data Created (ID: {dashboard_id})")
        
        return dashboard_id
    
    def run_complete_setup(self):
        """Run complete data setup for CrewAI UI"""
        
        print("\n🚀 Running Complete CrewAI UI Data Setup")
        print("=" * 60)
        
        try:
            # Write all data types
            agent_ids = self.write_ui_compatible_agents()
            mission_ids = self.write_ui_compatible_missions(agent_ids)
            tool_result_ids = self.write_sample_tool_results()
            pentest_result_ids = self.write_pentest_results()
            dashboard_id = self.generate_ui_dashboard_data()
            
            # Final statistics
            print("\n📈 Final Database Statistics:")
            stats = self.mongo.get_agent_stats()
            print(f"   • Total Agents: {stats['total_agents']}")
            print(f"   • Total Missions: {stats['total_missions']}")
            print(f"   • Tool Results: {stats['total_tool_results']}")
            print(f"   • Pentest Results: {stats['total_pentest_results']}")
            
            print(f"\n🎯 CrewAI UI Data Setup Complete!")
            print(f"   📱 Access CrewAI UI: http://localhost:3000")
            print(f"   🗄️  MongoDB Database: crewai_pentest")
            print(f"   📊 Dashboard Data ID: {dashboard_id}")
            
            # Provide query examples for the UI
            print(f"\n📝 MongoDB Query Examples for UI:")
            print(f"   • List Agents: db.agents.find().pretty()")
            print(f"   • List Missions: db.missions.find().pretty()")
            print(f"   • Get Tool Results: db.tool_results.find().pretty()")
            print(f"   • Get Dashboard Data: db.dashboard_data.find().pretty()")
            
            self.mongo.disconnect()
            return True
            
        except Exception as e:
            print(f"❌ Error during UI data setup: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main execution function"""
    writer = CrewAIUIDataWriter()
    success = writer.run_complete_setup()
    
    if success:
        print("\n✅ All data successfully written to MongoDB for CrewAI UI consumption!")
    else:
        print("\n❌ Data setup failed. Check error messages above.")

if __name__ == "__main__":
    main()
