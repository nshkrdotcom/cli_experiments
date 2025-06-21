# AGI CLI Platform

A self-evolving command-line platform that serves as a foundation for AGI (Artificial General Intelligence) development with advanced self-modification capabilities.

## Overview

This AGI CLI Platform uses LLM integration to generate and integrate new functionality dynamically. It demonstrates core AGI concepts including self-modification, autonomous code generation, multi-layer safety validation, and adaptive learning - serving as a practical foundation for building more advanced AGI systems.

## Features

- **Core CLI Framework**: Built with Click for robust command-line interface
- **Gemini AI Integration**: Uses Google's Gemini 2.0 Flash model for code generation
- **Self-Modification**: Can generate and integrate new commands dynamically
- **Code Validation**: Multiple layers of security and correctness validation
- **Plugin System**: Extensible architecture for additional functionality
- **Command History**: Complete history and rollback capabilities
- **Safe Execution**: Sandboxed execution environment with validation
- **Configuration Management**: YAML-based configuration with user customization
- **Comprehensive Testing**: Full test suite with mocking and live API testing

## Installation

### Quick Setup with Virtual Environment (Recommended)

1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd agi-cli-platform
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

4. **Set up your Gemini API key** (required for AI features)
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   # or alternatively
   export GOOGLE_API_KEY="your-google-api-key"
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

### Testing

The project includes a comprehensive test suite:

```bash
# Run all tests (mocked, no live API calls)
python run_tests.py

# Run fast tests only
python run_tests.py --fast

# Run tests with coverage report
python run_tests.py --coverage

# Run live API tests (requires valid GEMINI_API_KEY)
python run_tests.py --live

# Run specific test file
python run_tests.py -f tests/test_llm_integration.py
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
agi-cli-platform/
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
3. **Gemini API issues**: Check your `GEMINI_API_KEY` or `GOOGLE_API_KEY` and network connectivity
4. **Test failures**: Run tests without live API calls using `python run_tests.py` (default mode)

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
