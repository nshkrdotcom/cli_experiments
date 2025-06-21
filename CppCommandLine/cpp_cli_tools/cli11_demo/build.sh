#!/bin/bash

# Build script for CLI11 Demo
set -e

echo "Building CLI11 Demo..."

# Download CLI11 header if needed
if [ ! -f "include/CLI/CLI.hpp" ]; then
    echo "Downloading CLI11 header..."
    ./download_cli11.sh
fi

# Create build directory
mkdir -p build
cd build

# Configure with CMake
echo "Configuring with CMake..."
cmake ..

# Build the project
echo "Compiling..."
make -j$(nproc)

echo "Build complete!"
echo "Executable: ./cli_demo"
echo ""
echo "Try running:"
echo "  ./cli_demo --help"
echo "  ./cli_demo status"
echo "  ./cli_demo demo"
echo "  ./cli_demo benchmark"