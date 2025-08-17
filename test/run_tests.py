#!/usr/bin/env python3
"""
Test runner for strongbird test suite.
"""

import asyncio
import sys
import subprocess
from pathlib import Path

async def run_math_tests():
    """Run math extraction tests."""
    test_file = Path(__file__).parent / "test_math_extraction.py"
    
    print("🚀 Running Strongbird Test Suite")
    print("=" * 40)
    
    try:
        # Run the math extraction tests
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(test_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Print output
        if stdout:
            print(stdout.decode())
        if stderr:
            print("STDERR:", stderr.decode(), file=sys.stderr)
        
        return process.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_quick_validation():
    """Run a quick validation of the strongbird CLI."""
    print("\n🔧 Quick CLI Validation:")
    print("-" * 25)
    
    try:
        # Test that strongbird CLI is available
        result = subprocess.run(
            ["uv", "run", "strongbird", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Strongbird CLI is working")
            return True
        else:
            print("❌ Strongbird CLI failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ CLI validation error: {e}")
        return False

async def main():
    """Main test runner."""
    # Quick validation first
    cli_ok = run_quick_validation()
    
    if not cli_ok:
        print("❌ CLI validation failed, skipping math tests")
        sys.exit(1)
    
    # Run math extraction tests
    test_result = await run_math_tests()
    
    if test_result == 0:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(test_result)

if __name__ == "__main__":
    asyncio.run(main())