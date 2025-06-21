#!/bin/bash

# Download CLI11 header-only library
echo "Downloading CLI11 header..."

mkdir -p include/CLI
cd include/CLI

# Download the single header version
curl -L -o CLI.hpp https://github.com/CLIUtils/CLI11/releases/download/v2.3.2/CLI11.hpp

echo "CLI11 header downloaded successfully!"