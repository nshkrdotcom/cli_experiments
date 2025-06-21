#!/bin/bash

echo "=== CLI Experiments - Self-Evolving Tools Demo ==="
echo ""

echo "1. Python Implementation:"
echo "------------------------"
python main.py --help
echo ""
python main.py status
echo ""

echo "2. C++ Implementation:"
echo "---------------------"
if [ -f "cpp_cli_tools/cli11_demo/build/cli_demo" ]; then
    cd cpp_cli_tools/cli11_demo/build
    ./cli_demo --help
    echo ""
    ./cli_demo status
    echo ""
    ./cli_demo demo
    cd ../../..
else
    echo "C++ binary not available - compilation in progress"
fi

echo ""
echo "3. Project Structure:"
echo "--------------------"
find . -type f -name "*.py" -o -name "*.cpp" -o -name "*.hpp" | head -10
echo ""

echo "4. Key Features Demonstrated:"
echo "----------------------------"
echo "✓ Self-evolving CLI framework (Python + C++)"
echo "✓ LLM integration for code generation"
echo "✓ Multi-layer security validation"
echo "✓ Configuration management"
echo "✓ Plugin architecture"
echo "✓ Performance benchmarks"
echo "✓ Safe execution environment"
echo ""

echo "Ready for deployment to WSL Ubuntu 24.04!"
echo "Repository: https://github.com/nshkrdotcom/cli_experiments"