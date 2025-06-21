#!/usr/bin/env python3
"""
Test runner for the Self-Evolving CLI Tool

Usage:
    python run_tests.py                    # Run all tests except live API tests
    python run_tests.py --live             # Run all tests including live API tests
    python run_tests.py --coverage         # Run tests with detailed coverage report
    python run_tests.py --fast             # Run only fast tests
"""

import sys
import subprocess
import argparse
import os


def run_pytest(args_list):
    """Run pytest with the given arguments"""
    cmd = ['python', '-m', 'pytest'] + args_list
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Test runner for CLI tool')
    parser.add_argument('--live', action='store_true',
                        help='Include live API tests (requires valid API keys)')
    parser.add_argument('--coverage', action='store_true',
                        help='Generate detailed coverage report')
    parser.add_argument('--fast', action='store_true',
                        help='Run only fast tests (exclude slow and live tests)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--pattern', '-k', 
                        help='Run tests matching pattern')
    parser.add_argument('--file', '-f',
                        help='Run specific test file')
    
    args = parser.parse_args()
    
    # Build pytest arguments
    pytest_args = []
    
    # Test selection
    if args.file:
        pytest_args.append(f"tests/{args.file}")
    elif args.pattern:
        pytest_args.extend(['-k', args.pattern])
    
    # Marker selection
    if args.fast:
        pytest_args.extend(['-m', 'not slow and not live'])
    elif not args.live:
        pytest_args.extend(['-m', 'not live'])
    
    # Coverage options
    if args.coverage:
        pytest_args.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml'
        ])
    
    # Verbosity
    if args.verbose:
        pytest_args.append('-v')
    
    # Check for API keys if running live tests
    if args.live:
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("⚠️  WARNING: No Gemini API key found!")
            print("   Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
            print("   Live API tests will be skipped automatically")
        else:
            print("✅ API key found - live tests will run")
    
    # Run the tests
    print("🧪 Running Self-Evolving CLI Tool Tests")
    print("=" * 50)
    
    if args.live:
        print("🌐 Including live API tests")
    else:
        print("🔒 Excluding live API tests (use --live to include)")
    
    if args.fast:
        print("⚡ Running fast tests only")
    
    print()
    
    exit_code = run_pytest(pytest_args)
    
    print()
    print("=" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("❌ Some tests failed!")
        sys.exit(exit_code)


if __name__ == "__main__":
    main() 