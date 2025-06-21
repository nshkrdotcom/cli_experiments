#!/bin/bash

# Test script for the C++ CLI tool
set -e

echo "Testing C++ CLI Tool..."
echo "======================="

if [ ! -f "build/cli_demo" ]; then
    echo "Error: cli_demo not found. Run ./build.sh first."
    exit 1
fi

cd build

echo "1. Testing help command:"
./cli_demo --help
echo ""

echo "2. Testing status command:"
./cli_demo status
echo ""

echo "3. Testing version command:"
./cli_demo version
echo ""

echo "4. Testing config show:"
./cli_demo config show
echo ""

echo "5. Testing benchmark:"
./cli_demo benchmark
echo ""

echo "6. Testing demo (C++ advantages):"
./cli_demo demo
echo ""

echo "7. Testing safe execution:"
./cli_demo exec "echo 'Hello from C++ CLI!'"
echo ""

echo "All tests completed successfully!"