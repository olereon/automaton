#!/usr/bin/env python3
"""
Comprehensive Metadata Extraction Validation Suite

This is the master test suite that orchestrates all metadata extraction testing,
generates comprehensive reports, and provides quality assurance recommendations.

Focus: Complete validation workflow with detailed reporting and recommendations.
"""

import pytest
import asyncio
import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Test suite imports
from test_metadata_extraction_failure_reproduction import (
    TestMetadataExtractionFailureReproduction,
    generate_failure_reproduction_report
)
from test_metadata_extraction_performance_validation import (
    TestMetadataExtractionPerformanceValidation, 
    generate_performance_validation_report
)
from test_metadata_extraction_stress_testing import (
    TestMetadataExtractionStressTesting
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class ComprehensiveValidationOrchestrator:
    """Orchestrates comprehensive validation of metadata extraction fixes"""
    
    def __init__(self):
        self.validation_results = {
            "started_at": datetime.now().isoformat(),
            "test_suites": {},
            "overall_metrics": {},
            "quality_assessment": {},
            "recommendations": []
        }
        
    async def run_failure_reproduction_suite(self) -> Dict[str, Any]:
        """Run failure reproduction test suite"""
        logger.info("🔍 Running Failure Reproduction Test Suite...")
        
        suite_start = time.time()
        
        try:
            # Run failure reproduction tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_metadata_extraction_failure_reproduction.py",
                "-v", "--tb=short", "--json-report", "--json-report-file=failure_reproduction_report.json"
            ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=300)
            
            suite_end = time.time()
            
            suite_results = {
                "suite_name": "failure_reproduction",
                "duration": suite_end - suite_start,
                "exit_code": result.returncode,
                "tests_run": "determined from output",
                "failures_reproduced": True if result.returncode != 0 else False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "COMPLETED"
            }
            
            # Parse test results
            if "PASSED" in result.stdout:
                suite_results["failure_patterns_identified"] = self._extract_failure_patterns(result.stdout)
            
            logger.info(f"✅ Failure Reproduction Suite completed in {suite_results['duration']:.1f}s")
            return suite_results
            
        except subprocess.TimeoutExpired:
            return {
                "suite_name": "failure_reproduction", 
                "duration": 300,
                "status": "TIMEOUT",
                "error": "Test suite exceeded 5 minute timeout"
            }
        except Exception as e:
            return {
                "suite_name": "failure_reproduction",
                "status": "ERROR", 
                "error": str(e)
            }
    
    async def run_performance_validation_suite(self) -> Dict[str, Any]:
        """Run performance validation test suite"""
        logger.info("⚡ Running Performance Validation Test Suite...")
        
        suite_start = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_metadata_extraction_performance_validation.py",
                "-v", "--tb=short", "--json-report", "--json-report-file=performance_validation_report.json"
            ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=600)
            
            suite_end = time.time()
            
            suite_results = {
                "suite_name": "performance_validation",
                "duration": suite_end - suite_start,
                "exit_code": result.returncode,
                "tests_passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "COMPLETED"
            }
            
            # Extract performance metrics
            if "SUCCESS RATE" in result.stdout:
                suite_results["performance_metrics"] = self._extract_performance_metrics(result.stdout)
            
            logger.info(f"✅ Performance Validation Suite completed in {suite_results['duration']:.1f}s")
            return suite_results
            
        except subprocess.TimeoutExpired:
            return {
                "suite_name": "performance_validation",
                "duration": 600, 
                "status": "TIMEOUT",
                "error": "Test suite exceeded 10 minute timeout"
            }
        except Exception as e:
            return {
                "suite_name": "performance_validation",
                "status": "ERROR",
                "error": str(e)
            }
    
    async def run_stress_testing_suite(self) -> Dict[str, Any]:
        """Run stress testing suite"""
        logger.info("💥 Running Stress Testing Suite...")
        
        suite_start = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "test_metadata_extraction_stress_testing.py", 
                "-v", "--tb=short", "--json-report", "--json-report-file=stress_testing_report.json"
            ], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=900)
            
            suite_end = time.time()
            
            suite_results = {
                "suite_name": "stress_testing",
                "duration": suite_end - suite_start,
                "exit_code": result.returncode,
                "tests_passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "COMPLETED"
            }
            
            # Extract stress test results
            if "STRESS TEST" in result.stdout:
                suite_results["stress_metrics"] = self._extract_stress_metrics(result.stdout)
            
            logger.info(f"✅ Stress Testing Suite completed in {suite_results['duration']:.1f}s")
            return suite_results
            
        except subprocess.TimeoutExpired:
            return {
                "suite_name": "stress_testing",
                "duration": 900,
                "status": "TIMEOUT", 
                "error": "Test suite exceeded 15 minute timeout"
            }
        except Exception as e:
            return {
                "suite_name": "stress_testing",
                "status": "ERROR",
                "error": str(e)
            }
    
    def _extract_failure_patterns(self, output: str) -> List[str]:
        """Extract identified failure patterns from test output"""
        patterns = []
        
        # Look for failure pattern indicators in output
        pattern_keywords = [
            "empty_selectors", "malformed_elements", "timing_issues",
            "dom_structure_changed", "network_errors"
        ]
        
        for keyword in pattern_keywords:
            if keyword in output.lower():
                patterns.append(keyword.replace("_", " ").title())
        
        return patterns
    
    def _extract_performance_metrics(self, output: str) -> Dict[str, Any]:
        """Extract performance metrics from test output"""
        metrics = {}
        
        # Extract success rates
        import re
        success_rate_matches = re.findall(r'SUCCESS RATE.*?(\d+\.?\d*)%', output)
        if success_rate_matches:
            metrics["success_rate"] = float(success_rate_matches[-1])
        
        # Extract timing information
        timing_matches = re.findall(r'Average: (\d+\.?\d*)s', output)
        if timing_matches:
            metrics["average_extraction_time"] = float(timing_matches[-1])
        
        return metrics
    
    def _extract_stress_metrics(self, output: str) -> Dict[str, Any]:
        """Extract stress testing metrics from test output"""
        metrics = {}
        
        # Look for stress test results
        if "HIGH VOLUME" in output:
            metrics["high_volume_handled"] = True
        if "LATENCY RESILIENCE" in output:
            metrics["latency_resilient"] = True
        if "CONCURRENT ACCESS" in output:
            metrics["concurrent_safe"] = True
        if "MEMORY PRESSURE" in output:
            metrics["memory_efficient"] = True
        
        return metrics
    
    def analyze_overall_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall test results and generate quality assessment"""
        
        analysis = {
            "total_duration": sum(
                result.get("duration", 0) for result in test_results.values()
            ),
            "suites_completed": sum(
                1 for result in test_results.values() 
                if result.get("status") == "COMPLETED"
            ),
            "suites_passed": sum(
                1 for result in test_results.values()
                if result.get("tests_passed", False)
            ),
            "critical_issues": [],
            "performance_summary": {},
            "readiness_assessment": "UNKNOWN"
        }
        
        # Check for critical issues
        for suite_name, result in test_results.items():
            if result.get("status") == "TIMEOUT":
                analysis["critical_issues"].append(f"{suite_name} exceeded timeout")
            elif result.get("status") == "ERROR":
                analysis["critical_issues"].append(f"{suite_name} encountered errors")
        
        # Performance summary
        if "performance_validation" in test_results:
            perf_result = test_results["performance_validation"]
            if "performance_metrics" in perf_result:
                analysis["performance_summary"] = perf_result["performance_metrics"]
        
        # Readiness assessment
        if len(analysis["critical_issues"]) == 0:
            if analysis["suites_passed"] >= 2:
                analysis["readiness_assessment"] = "READY_FOR_PRODUCTION"
            elif analysis["suites_passed"] >= 1:
                analysis["readiness_assessment"] = "NEEDS_MINOR_FIXES"
            else:
                analysis["readiness_assessment"] = "MAJOR_FIXES_REQUIRED"
        else:
            analysis["readiness_assessment"] = "CRITICAL_ISSUES_FOUND"
        
        return analysis
    
    def generate_qa_recommendations(self, test_results: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate QA recommendations based on test results"""
        
        recommendations = []
        
        # Based on readiness assessment
        if analysis["readiness_assessment"] == "CRITICAL_ISSUES_FOUND":
            recommendations.append({
                "priority": "CRITICAL",
                "category": "System Stability",
                "recommendation": "Address critical issues before proceeding to production",
                "action": "Fix timeout and error conditions identified in test suites"
            })
        
        # Performance recommendations
        if "performance_validation" in test_results:
            perf_metrics = analysis.get("performance_summary", {})
            
            if perf_metrics.get("success_rate", 0) < 90:
                recommendations.append({
                    "priority": "HIGH", 
                    "category": "Success Rate",
                    "recommendation": f"Success rate {perf_metrics.get('success_rate', 0):.1f}% is below 90% target",
                    "action": "Implement additional error handling and retry logic"
                })
            
            if perf_metrics.get("average_extraction_time", 0) > 2.0:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "recommendation": f"Average extraction time {perf_metrics.get('average_extraction_time', 0):.2f}s exceeds 2.0s target",
                    "action": "Optimize extraction algorithms and reduce DOM query overhead"
                })
        
        # Stress testing recommendations
        if "stress_testing" in test_results:
            stress_metrics = test_results["stress_testing"].get("stress_metrics", {})
            
            if not stress_metrics.get("concurrent_safe", True):
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Concurrency",
                    "recommendation": "Concurrent access safety issues detected",
                    "action": "Implement proper thread safety and resource locking"
                })
            
            if not stress_metrics.get("memory_efficient", True):
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Memory Usage",
                    "recommendation": "Memory efficiency issues under stress conditions",
                    "action": "Optimize memory usage and implement garbage collection"
                })
        
        # General recommendations
        if analysis["suites_completed"] < 3:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Test Coverage",
                "recommendation": f"Only {analysis['suites_completed']}/3 test suites completed successfully",
                "action": "Investigate and resolve test execution issues"
            })
        
        # Success case recommendations
        if analysis["readiness_assessment"] == "READY_FOR_PRODUCTION":
            recommendations.append({
                "priority": "LOW",
                "category": "Monitoring",
                "recommendation": "System appears ready for production deployment",
                "action": "Implement monitoring and alerting for production metrics"
            })
        
        return recommendations
    
    def generate_comprehensive_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        analysis = self.analyze_overall_results(test_results)
        recommendations = self.generate_qa_recommendations(test_results, analysis)
        
        report = {
            "report_title": "Comprehensive Metadata Extraction Validation Report",
            "generated_at": datetime.now().isoformat(),
            "validation_scope": {
                "objective": "Validate metadata extraction system fixes and performance improvements",
                "approach": "Multi-tiered testing: failure reproduction, performance validation, stress testing",
                "success_criteria": [
                    "Achieve >90% metadata extraction success rate",
                    "Maintain <2s average extraction time", 
                    "Pass stress testing under concurrent load",
                    "Handle edge cases and error conditions gracefully"
                ]
            },
            "test_execution_summary": {
                "total_duration": f"{analysis['total_duration']:.1f} seconds",
                "suites_executed": len(test_results),
                "suites_completed": analysis["suites_completed"],
                "suites_passed": analysis["suites_passed"],
                "critical_issues_count": len(analysis["critical_issues"])
            },
            "test_suite_results": test_results,
            "performance_analysis": analysis["performance_summary"],
            "quality_assessment": {
                "readiness_status": analysis["readiness_assessment"],
                "critical_issues": analysis["critical_issues"],
                "overall_score": self._calculate_quality_score(test_results, analysis)
            },
            "qa_recommendations": recommendations,
            "next_steps": self._generate_next_steps(analysis, recommendations),
            "appendix": {
                "failure_reproduction_report": generate_failure_reproduction_report(),
                "performance_validation_report": generate_performance_validation_report()
            }
        }
        
        return report
    
    def _calculate_quality_score(self, test_results: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score (0.0 to 1.0)"""
        
        score = 0.0
        max_score = 1.0
        
        # Suite completion score (0.3 max)
        completion_score = (analysis["suites_completed"] / 3) * 0.3
        score += completion_score
        
        # Suite passing score (0.4 max)
        passing_score = (analysis["suites_passed"] / 3) * 0.4  
        score += passing_score
        
        # Performance score (0.2 max)
        perf_metrics = analysis.get("performance_summary", {})
        if perf_metrics:
            success_rate = perf_metrics.get("success_rate", 0) / 100
            time_score = max(0, 1 - (perf_metrics.get("average_extraction_time", 2) / 4))  # Penalty after 4s
            performance_score = ((success_rate + time_score) / 2) * 0.2
            score += performance_score
        
        # Critical issues penalty (0.1 max)
        if len(analysis["critical_issues"]) == 0:
            score += 0.1
        
        return min(score, max_score)
    
    def _generate_next_steps(self, analysis: Dict[str, Any], recommendations: List[Dict[str, str]]) -> List[str]:
        """Generate actionable next steps"""
        
        next_steps = []
        
        if analysis["readiness_assessment"] == "CRITICAL_ISSUES_FOUND":
            next_steps.extend([
                "🚨 IMMEDIATE: Address critical issues before any production deployment",
                "🔧 FIX: Resolve timeout and error conditions in test suites",
                "🧪 TEST: Re-run validation suite after fixes",
            ])
        elif analysis["readiness_assessment"] == "MAJOR_FIXES_REQUIRED":
            next_steps.extend([
                "⚠️ HIGH PRIORITY: Address major functionality issues",
                "🎯 IMPROVE: Focus on success rate and performance improvements",
                "📊 MEASURE: Implement metrics collection for monitoring",
            ])
        elif analysis["readiness_assessment"] == "NEEDS_MINOR_FIXES":
            next_steps.extend([
                "🔧 MEDIUM PRIORITY: Address minor issues and optimizations",
                "📈 OPTIMIZE: Fine-tune performance and error handling",
                "🚀 PREPARE: Set up production monitoring and deployment",
            ])
        else:  # READY_FOR_PRODUCTION
            next_steps.extend([
                "✅ DEPLOY: System ready for production deployment",
                "📊 MONITOR: Set up comprehensive monitoring and alerting",
                "📋 DOCUMENT: Create operational runbooks and troubleshooting guides",
            ])
        
        # Add recommendation-based steps
        critical_recs = [r for r in recommendations if r["priority"] == "CRITICAL"]
        high_recs = [r for r in recommendations if r["priority"] == "HIGH"]
        
        for rec in critical_recs[:2]:  # Top 2 critical
            next_steps.append(f"🚨 CRITICAL: {rec['action']}")
        
        for rec in high_recs[:3]:  # Top 3 high priority
            next_steps.append(f"⚠️ HIGH: {rec['action']}")
        
        return next_steps

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all test suites and generate comprehensive report"""
        
        logger.info("🎯 Starting Comprehensive Metadata Extraction Validation")
        logger.info("=" * 80)
        
        overall_start = time.time()
        test_results = {}
        
        try:
            # Run all test suites
            test_results["failure_reproduction"] = await self.run_failure_reproduction_suite()
            test_results["performance_validation"] = await self.run_performance_validation_suite()
            test_results["stress_testing"] = await self.run_stress_testing_suite()
            
            overall_end = time.time()
            
            # Generate comprehensive report
            report = self.generate_comprehensive_report(test_results)
            report["total_validation_time"] = overall_end - overall_start
            
            # Save report
            report_path = Path(__file__).parent / "comprehensive_validation_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info("=" * 80)
            logger.info(f"🎯 Comprehensive Validation Completed in {report['total_validation_time']:.1f}s")
            logger.info(f"📊 Quality Score: {report['quality_assessment']['overall_score']:.2f}/1.0")
            logger.info(f"🏆 Readiness Status: {report['quality_assessment']['readiness_status']}")
            logger.info(f"📋 Report saved to: {report_path}")
            logger.info("=" * 80)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {e}")
            return {
                "error": str(e),
                "partial_results": test_results,
                "validation_time": time.time() - overall_start
            }


class TestComprehensiveMetadataValidation:
    """Pytest wrapper for comprehensive validation"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_suite(self):
        """Run comprehensive validation and assert quality standards"""
        
        orchestrator = ComprehensiveValidationOrchestrator()
        report = await orchestrator.run_comprehensive_validation()
        
        # Assert quality standards
        assert "error" not in report, f"Validation failed with error: {report.get('error')}"
        
        quality_score = report["quality_assessment"]["overall_score"]
        readiness_status = report["quality_assessment"]["readiness_status"]
        
        # Quality assertions
        assert quality_score >= 0.7, f"Quality score {quality_score:.2f} below minimum 0.7"
        assert readiness_status != "CRITICAL_ISSUES_FOUND", f"Critical issues detected: {report['quality_assessment']['critical_issues']}"
        
        # Suite completion assertions
        suites_completed = report["test_execution_summary"]["suites_completed"]
        assert suites_completed >= 2, f"Only {suites_completed}/3 test suites completed"
        
        logger.info(f"✅ Comprehensive validation passed with quality score {quality_score:.2f}")


if __name__ == "__main__":
    # Run comprehensive validation directly
    async def main():
        orchestrator = ComprehensiveValidationOrchestrator()
        report = await orchestrator.run_comprehensive_validation()
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Quality Score: {report['quality_assessment']['overall_score']:.2f}/1.0")
        print(f"Readiness Status: {report['quality_assessment']['readiness_status']}")
        print(f"Total Time: {report.get('total_validation_time', 0):.1f}s")
        print(f"Test Suites: {report['test_execution_summary']['suites_completed']}/3 completed")
        
        if report["qa_recommendations"]:
            print("\n🔧 TOP RECOMMENDATIONS:")
            for rec in report["qa_recommendations"][:3]:
                print(f"  {rec['priority']}: {rec['recommendation']}")
        
        if report.get("next_steps"):
            print("\n🎯 NEXT STEPS:")
            for step in report["next_steps"][:5]:
                print(f"  {step}")
        
        print("=" * 80)
    
    asyncio.run(main())