# Deployment Guide

## Overview

This project contains both Python and C++ implementations of a self-evolving CLI tool that demonstrates the foundation concepts for AGI platform development.

## Python Implementation

### Local Development
```bash
# Install dependencies
pip install click pyyaml

# Run the tool
python main.py --help
python main.py status
```

### Using with LLM
```bash
# Set API key
export OPENAI_API_KEY="your-key-here"

# Test LLM integration
python main.py llm-query "Hello, can you help me?"

# Generate new functionality
python main.py evolve "create a command that lists files" --save --execute
```

## C++ Implementation

### Building
```bash
cd cpp_cli_tools/cli11_demo
./build.sh
```

### Testing
```bash
./test_cli.sh
```

### Usage Examples
```bash
# Basic commands
./build/cli_demo --help
./build/cli_demo status
./build/cli_demo demo

# Performance comparison
./build/cli_demo benchmark

# LLM integration (requires llm command)
./build/cli_demo query "Suggest improvements for this CLI tool"
./build/cli_demo evolve "create a file processor" --save
```

## Why C++ for CLI Tools?

### Performance Benefits
- **Execution Speed**: 10-100x faster than Python for intensive operations
- **Memory Efficiency**: Direct memory management, no garbage collection overhead
- **Startup Time**: Instant startup vs Python interpreter loading
- **Resource Usage**: Minimal CPU and RAM footprint

### System Integration
- **Native APIs**: Direct access to OS system calls
- **Binary Distribution**: Single executable, no runtime dependencies
- **Cross-Platform**: Compile once for each target platform
- **Real-Time**: Predictable performance for time-critical operations

### Development Advantages
- **Type Safety**: Compile-time error detection
- **Optimization**: Advanced compiler optimizations
- **Debugging**: Native debugging tools and profilers
- **Maintainability**: Strong typing reduces runtime errors

## Self-Replicating System Architecture

Both implementations demonstrate the core concept of a self-modifying system:

1. **LLM Integration**: Uses external AI to generate new functionality
2. **Code Validation**: Multi-layer security and correctness checking
3. **Dynamic Loading**: Runtime integration of new commands
4. **History Management**: Rollback and version control
5. **Configuration**: User-customizable behavior

This architecture serves as a foundation for more advanced AGI systems by providing:
- Self-modification capabilities
- Safe code execution
- Learning from interactions
- Extensible plugin system
- Performance optimization

## Deployment to WSL Ubuntu 24.04

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install -y build-essential cmake git

# Install Python dependencies
pip3 install click pyyaml

# Install LLM command (optional)
pip3 install llm
```

### Clone and Build
```bash
git clone https://github.com/nshkrdotcom/cli_experiments.git
cd cli_experiments

# Test Python version
python3 main.py --help

# Build C++ version
cd cpp_cli_tools/cli11_demo
./build.sh
./test_cli.sh
```

### Integration with Your AGI Platform

This CLI tool provides the foundation patterns for:
- Dynamic code generation and execution
- Self-modification capabilities
- Safe AI-assisted development
- Performance-critical system components
- Modular, extensible architecture

The C++ implementation is particularly suited for the performance-critical components of your AGI platform, while the Python version is ideal for rapid prototyping and development.