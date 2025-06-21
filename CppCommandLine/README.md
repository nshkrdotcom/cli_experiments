# Self-Evolving CLI Tool

A foundation for AGI platform development with self-modification capabilities.

## Overview

This CLI tool can use LLM queries to generate and integrate new functionality dynamically. It serves as a foundation for building more advanced AGI platforms by demonstrating self-modification, code generation, and safe execution capabilities.

## Features

- **Core CLI Framework**: Built with Click for robust command-line interface
- **LLM Integration**: Uses the `llm` command for code generation and queries
- **Self-Modification**: Can generate and integrate new commands dynamically
- **Code Validation**: Multiple layers of security and correctness validation
- **Plugin System**: Extensible architecture for additional functionality
- **Command History**: Complete history and rollback capabilities
- **Safe Execution**: Sandboxed execution environment with validation
- **Configuration Management**: YAML-based configuration with user customization

## Installation

### Quick Setup with Virtual Environment (Recommended)

1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd CppCommandLine
   ```

2. **One-command setup** (Linux/macOS)
   ```bash
   # Use the convenience script
   source activate_env.sh
   ```

3. **Manual setup** (alternative)
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   
   # Install the project and its dependencies
   pip install -e .
   ```

4. **Set up your API keys** (optional, for LLM integration)
   ```bash
   export OPENAI_API_KEY="your-api-key"
   # or
   export LLM_API_KEY="your-api-key"
   ```

5. **Run the tool**
   ```bash
   python main.py --help
   ```

### Alternative Installation Methods

#### Using pip directly
```bash
pip install pyyaml>=6.0 click>=8.0.0 stringzilla>=3.12.5
python main.py --help
```

#### Development mode
```bash
# After setting up virtual environment
pip install -e .
```

## Usage

### Basic Commands

```bash
# Show help
python main.py --help

# Check tool status
python main.py status

# Generate new functionality
python main.py evolve "create a command to list files"

# Execute generated command immediately
python main.py evolve "create a backup utility" --execute

# Save generated command permanently
python main.py evolve "create a log analyzer" --save

# View command history
python main.py history

# Rollback a command
python main.py rollback <command-id>

# List available plugins
python main.py list-plugins

# Install a plugin
python main.py install-plugin <plugin-name>
```

### Configuration

The tool uses YAML configuration files. Default configuration is loaded from `config/default.yaml`. You can specify a custom config file:

```bash
python main.py --config /path/to/your/config.yaml --verbose
```

## C++ CLI Tools

For high-performance system tools, see the `cpp_cli_tools/` directory:

```bash
cd cpp_cli_tools/cli11_demo
./build.sh
./build/cli_demo --help
```

The C++ version demonstrates:
- **10x+ faster execution** for intensive operations
- **Native binary deployment** (no Python runtime required)
- **Direct system API access** for advanced functionality
- **Minimal memory footprint** compared to interpreted languages

## Development

### Project Structure

```
CppCommandLine/
├── src/                    # Python source code
│   ├── cli.py             # Main CLI interface
│   ├── config.py          # Configuration management
│   ├── llm_integration.py # LLM API integration
│   ├── code_generator.py  # Code generation logic
│   ├── command_manager.py # Dynamic command management
│   ├── plugin_system.py   # Plugin architecture
│   ├── history.py         # Command history
│   ├── validator.py       # Code validation
│   └── logger.py          # Logging utilities
├── config/                # Configuration files
├── templates/             # Code templates
├── plugins/               # Plugin directory
├── generated/             # Generated code storage
├── logs/                  # Log files
├── backups/               # Backup storage
└── cpp_cli_tools/         # C++ implementations
```

### Contributing

1. Set up development environment with virtual environment
2. Install in development mode: `pip install -e .`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated your virtual environment and installed dependencies
2. **Permission errors**: Ensure proper file permissions for generated code
3. **LLM integration issues**: Check your API keys and network connectivity

### Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf venv

# Create new environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```
