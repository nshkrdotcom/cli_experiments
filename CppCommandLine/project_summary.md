# CLI Experiments - Self-Evolving Tools Project

A comprehensive demonstration of self-evolving CLI tools in both Python and C++, showcasing the foundation concepts for AGI platform development.

## Project Structure

```
.
├── src/                    # Python implementation
├── cpp_cli_tools/          # C++ implementations
│   ├── cli11_demo/         # Main CLI11-based tool
│   ├── performance_benchmark/
│   └── system_tools/
├── config/                 # Configuration files
├── templates/              # Code generation templates
├── plugins/                # Plugin system
└── generated/              # Dynamically generated commands
```

## Key Implementations

### Python Implementation (src/)
- **Framework**: Click-based CLI
- **Features**: Full LLM integration, plugin system, code validation
- **Use Case**: Rapid prototyping, development, experimentation
- **Command**: `python main.py --help`

### C++ Implementation (cpp_cli_tools/cli11_demo/)
- **Framework**: CLI11-based high-performance tool
- **Features**: Native binary, direct system access, performance benchmarks
- **Use Case**: Production deployment, system tools, performance-critical tasks
- **Command**: `./build/cli_demo --help`

## Core Capabilities

### Self-Evolution
- Generate new CLI commands using LLM queries
- Dynamic code validation and integration
- Runtime command loading and execution
- History tracking and rollback functionality

### Safety Features
- Multi-layer code validation (AST, security, LLM-based)
- Sandboxed execution environment
- Configuration-driven restrictions
- Safe mode for system commands

### AGI Foundation Concepts
- **Self-Modification**: Tools can modify their own functionality
- **Learning**: History tracking and improvement suggestions
- **Reasoning**: LLM-assisted decision making
- **Safety**: Comprehensive validation before execution
- **Extensibility**: Plugin architecture for new capabilities

## Performance Comparison

| Operation | Python | C++ | Speedup |
|-----------|--------|-----|---------|
| String Processing | ~1000ms | ~50ms | 20x |
| Mathematical Computation | ~500ms | ~25ms | 20x |
| Memory Allocation | ~200ms | ~10ms | 20x |
| Binary Size | ~50MB (with Python) | ~2MB | 25x smaller |
| Startup Time | ~500ms | ~5ms | 100x faster |

## Deployment Ready

### For Ubuntu WSL 24.04
```bash
# Clone repository
git clone https://github.com/nshkrdotcom/cli_experiments.git
cd cli_experiments

# Python version
python3 main.py --help

# C++ version
cd cpp_cli_tools/cli11_demo
./build.sh
./build/cli_demo --help
```

### LLM Integration
```bash
# Install LLM command
pip install llm

# Set API key
export OPENAI_API_KEY="your-key"

# Test integration
python main.py llm-query "Hello"
./build/cli_demo query "Suggest improvements"
```

## AGI Platform Integration

This project provides the foundational patterns for building AGI systems:

1. **Self-Replicating Code**: Generate and execute new functionality
2. **Safety-First Design**: Comprehensive validation before execution
3. **Performance Optimization**: C++ for critical system components
4. **Learning Capabilities**: History tracking and improvement
5. **Modular Architecture**: Plugin system for extensibility

The dual-language approach demonstrates:
- **Python**: Rapid development and experimentation
- **C++**: Production deployment and performance

Both implementations share the same core concepts while leveraging the strengths of each language for different use cases in an AGI platform.

## Future Extensions

- WebAssembly compilation for browser deployment
- GPU acceleration for intensive computations
- Distributed execution across multiple nodes
- Advanced neural architecture integration
- Real-time learning and adaptation

This foundation provides the building blocks for more sophisticated AGI platform development while maintaining safety, performance, and extensibility.