#!/usr/bin/env python3
"""
🎭 Comprehensive InSilver Bot Tester
Combines Level 1-7 Autotester + Level 8 UI Workflow Tester
Complete testing solution for production readiness
"""

import asyncio
import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

# Cost tracking for comprehensive testing
TOTAL_COST = 0.0
BUDGET_LIMIT = 20.0

def track_comprehensive_cost(cost: float, component: str):
    """Track costs across all testing components"""
    global TOTAL_COST
    TOTAL_COST += cost
    print(f"💰 {component}: ${cost:.3f} (Total: ${TOTAL_COST:.3f}/${BUDGET_LIMIT})")

class ComprehensiveTester:
    """
    🎭 Comprehensive InSilver Bot Testing Suite
    """
    
    def __init__(self):
        self.project_root = Path("/home/sashok/.openclaw/workspace/insilver-v3")
        self.results = {}
        self.start_time = time.time()
        
        print("🎭 COMPREHENSIVE INSILVER BOT TESTING SUITE")
        print("=" * 55)
        print(f"💰 Total Budget: ${BUDGET_LIMIT}")
        print(f"📁 Project: {self.project_root}")
        print(f"🎯 Goal: Complete production readiness validation")
    
    async def run_level_1_7_autotester(self) -> Dict:
        """Run existing Level 1-7 Autotester"""
        print(f"\n🔧 LEVEL 1-7: AUTOTESTER (Code Quality + Mock AI)")
        print("=" * 50)
        
        try:
            # Run the existing autotester
            result = subprocess.run([
                str(self.project_root / "venv/bin/python3"),
                str(self.project_root / "autotester.py")
            ], capture_output=True, text=True, cwd=self.project_root, timeout=120)
            
            if result.returncode == 0:
                output_lines = result.stdout.split('\n')
                
                # Parse results from output
                test_results = {
                    "status": "passed",
                    "levels_completed": 0,
                    "total_tests": 0,
                    "passed_tests": 0,
                    "output": result.stdout
                }
                
                # Extract key metrics from output
                for line in output_lines:
                    if "РІВЕНЬ" in line and "✅" in line:
                        test_results["levels_completed"] += 1
                    elif "✅" in line and ("/" in line):
                        # Try to extract test counts
                        try:
                            parts = line.split()
                            for part in parts:
                                if "/" in part and part.replace("/", "").isdigit():
                                    passed, total = map(int, part.split("/"))
                                    test_results["passed_tests"] += passed
                                    test_results["total_tests"] += total
                        except:
                            pass
                
                track_comprehensive_cost(0.02, "Level 1-7 Autotester")
                print(f"✅ Level 1-7 completed: {test_results['levels_completed']} levels")
                
                return test_results
                
            else:
                error_result = {
                    "status": "failed",
                    "error": result.stderr,
                    "output": result.stdout
                }
                print(f"❌ Level 1-7 failed: {result.stderr[:100]}")
                track_comprehensive_cost(0.01, "Level 1-7 Error")
                return error_result
                
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Level 1-7 exception: {e}")
            track_comprehensive_cost(0.01, "Level 1-7 Exception")
            return error_result
    
    async def run_level_8_ui_tester(self, mode: str = "full") -> Dict:
        """Run Level 8 UI Workflow Tester"""
        print(f"\n🎭 LEVEL 8: UI WORKFLOW TESTING ({mode.upper()} MODE)")
        print("=" * 50)
        
        try:
            # Import and run UI tester
            from ui_workflow_tester import run_ui_workflow_tests, run_quick_tests
            
            if mode == "quick":
                result = await run_quick_tests()
                test_result = {
                    "status": "passed" if result else "failed",
                    "mode": "quick",
                    "scenarios_passed": 2 if result else 0,
                    "total_scenarios": 2
                }
            else:
                # Run full UI workflow tests
                result = await run_ui_workflow_tests()
                test_result = {
                    "status": "passed" if result["success_rate"] >= 75 else "failed",
                    "mode": "full",
                    "scenarios_passed": result["passed_scenarios"],
                    "total_scenarios": result["total_scenarios"],
                    "success_rate": result["success_rate"],
                    "cost": result["cost_tracking"]["total_cost"]
                }
                track_comprehensive_cost(result["cost_tracking"]["total_cost"], "Level 8 UI Tester")
            
            print(f"✅ Level 8 completed: {test_result['scenarios_passed']}/{test_result['total_scenarios']} scenarios")
            return test_result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ Level 8 exception: {e}")
            track_comprehensive_cost(0.01, "Level 8 Exception")
            return error_result
    
    async def run_integration_test(self) -> Dict:
        """Run integration test between components"""
        print(f"\n🔗 INTEGRATION TESTING")
        print("=" * 30)
        
        try:
            # Check if bot is running
            bot_status = subprocess.run([
                'systemctl', 'is-active', 'insilver-v3'
            ], capture_output=True, text=True)
            
            bot_running = bot_status.stdout.strip() == 'active'
            
            # Check orders file integrity
            orders_file = self.project_root / "data/orders/orders.json"
            orders_accessible = orders_file.exists() and orders_file.is_file()
            
            # Check log files
            bot_log = self.project_root / "logs/bot.log"
            logs_accessible = bot_log.exists()
            
            integration_result = {
                "status": "passed",
                "checks": {
                    "bot_running": bot_running,
                    "orders_file_accessible": orders_accessible,
                    "logs_accessible": logs_accessible
                },
                "integration_score": 0
            }
            
            # Calculate integration score
            checks_passed = sum(integration_result["checks"].values())
            total_checks = len(integration_result["checks"])
            integration_result["integration_score"] = (checks_passed / total_checks) * 100
            
            if integration_result["integration_score"] < 75:
                integration_result["status"] = "failed"
            
            track_comprehensive_cost(0.005, "Integration Testing")
            print(f"✅ Integration score: {integration_result['integration_score']:.1f}%")
            
            return integration_result
            
        except Exception as e:
            error_result = {
                "status": "error", 
                "error": str(e),
                "integration_score": 0
            }
            print(f"❌ Integration test exception: {e}")
            track_comprehensive_cost(0.002, "Integration Error")
            return error_result
    
    async def generate_comprehensive_report(self) -> Dict:
        """Generate final comprehensive test report"""
        print(f"\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 40)
        
        # Calculate overall metrics
        total_duration = time.time() - self.start_time
        
        # Analyze results
        components_tested = len(self.results)
        components_passed = len([r for r in self.results.values() if r.get("status") == "passed"])
        overall_success_rate = (components_passed / components_tested * 100) if components_tested > 0 else 0
        
        # Determine production readiness
        if overall_success_rate >= 90:
            readiness = "PRODUCTION READY"
            readiness_emoji = "🚀"
        elif overall_success_rate >= 75:
            readiness = "MOSTLY READY - Minor issues"
            readiness_emoji = "✅"
        elif overall_success_rate >= 50:
            readiness = "NEEDS WORK - Major issues"
            readiness_emoji = "⚠️"
        else:
            readiness = "NOT READY - Critical issues"
            readiness_emoji = "🔴"
        
        comprehensive_report = {
            "timestamp": time.time(),
            "duration": total_duration,
            "components_tested": components_tested,
            "components_passed": components_passed,
            "overall_success_rate": overall_success_rate,
            "production_readiness": readiness,
            "total_cost": TOTAL_COST,
            "budget_utilization": (TOTAL_COST / BUDGET_LIMIT) * 100,
            "detailed_results": self.results
        }
        
        # Display report
        print(f"🎭 Components tested: {components_tested}")
        print(f"✅ Components passed: {components_passed}")
        print(f"📈 Overall success rate: {overall_success_rate:.1f}%")
        print(f"⏱️ Total duration: {total_duration:.1f}s")
        print(f"💰 Total cost: ${TOTAL_COST:.3f}")
        print(f"📊 Budget utilization: {(TOTAL_COST/BUDGET_LIMIT)*100:.1f}%")
        print(f"\n{readiness_emoji} PRODUCTION READINESS: {readiness}")
        
        # Save comprehensive report
        report_file = self.project_root / "comprehensive_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Comprehensive report saved: {report_file}")
        
        return comprehensive_report

async def run_comprehensive_testing(mode: str = "full"):
    """
    🚀 Main Comprehensive Testing Function
    """
    tester = ComprehensiveTester()
    
    try:
        # Phase 1: Level 1-7 Autotester (Code Quality)
        level_1_7_result = await tester.run_level_1_7_autotester()
        tester.results["level_1_7_autotester"] = level_1_7_result
        
        await asyncio.sleep(1)
        
        # Phase 2: Level 8 UI Workflow Tester
        level_8_result = await tester.run_level_8_ui_tester(mode)
        tester.results["level_8_ui_tester"] = level_8_result
        
        await asyncio.sleep(1)
        
        # Phase 3: Integration Testing
        integration_result = await tester.run_integration_test()
        tester.results["integration_testing"] = integration_result
        
        # Phase 4: Final Report
        comprehensive_report = await tester.generate_comprehensive_report()
        
        return comprehensive_report
        
    except Exception as e:
        print(f"❌ Critical error in comprehensive testing: {e}")
        return {"status": "critical_error", "error": str(e)}

def create_comprehensive_cli():
    """CLI interface for comprehensive tester"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎭 Comprehensive InSilver Bot Tester")
    parser.add_argument('--mode', choices=['quick', 'full'], default='full',
                        help='Testing mode: quick (essential) or full (comprehensive)')
    parser.add_argument('--budget', type=float, default=20.0,
                        help='Set budget limit (default: $20.0)')
    parser.add_argument('--component', choices=['autotester', 'ui', 'integration', 'all'], 
                        default='all', help='Run specific component only')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = create_comprehensive_cli()
    
    # Set budget
    if args.budget:
        BUDGET_LIMIT = args.budget
    
    print(f"🎭 Starting comprehensive testing (mode: {args.mode}, budget: ${BUDGET_LIMIT})")
    
    # Run comprehensive testing
    result = asyncio.run(run_comprehensive_testing(args.mode))
    
    # Exit with appropriate code
    if result.get("overall_success_rate", 0) >= 75:
        print(f"\n🎉 SUCCESS: InSilver bot ready for production!")
        sys.exit(0)
    else:
        print(f"\n⚠️ WARNING: InSilver bot needs more work before production")
        sys.exit(1)