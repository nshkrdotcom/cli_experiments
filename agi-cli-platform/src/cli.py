"""
Main CLI interface using Click framework
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from config import ConfigManager
from llm_integration import LLMIntegration
from code_generator import CodeGenerator
from command_manager import CommandManager
from plugin_system import PluginSystem
from history import HistoryManager
from logger import setup_logger

# Try to import enhanced components
try:
    from multi_provider_llm import MultiProviderLLM
    MULTI_PROVIDER_AVAILABLE = True
except ImportError:
    MULTI_PROVIDER_AVAILABLE = False

# Setup logging
logger = setup_logger(__name__)

class CLIContext:
    """Context object to share state between commands"""
    def __init__(self):
        self.config_manager = ConfigManager()
        
        # Use multi-provider LLM if available, otherwise fall back to basic
        if MULTI_PROVIDER_AVAILABLE:
            self.llm_integration = MultiProviderLLM(self.config_manager)
            logger.info("Using multi-provider LLM integration")
        else:
            self.llm_integration = LLMIntegration(self.config_manager)
            logger.info("Using basic LLM integration")
        
        self.code_generator = CodeGenerator(self.config_manager, self.llm_integration)
        self.command_manager = CommandManager(self.config_manager)
        self.plugin_system = PluginSystem(self.config_manager)
        self.history_manager = HistoryManager(self.config_manager)

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """Self-Evolving CLI Tool - A foundation for AGI platform development"""
    
    # Initialize context
    ctx.ensure_object(CLIContext)
    cli_ctx = ctx.obj
    
    # Load configuration
    if config:
        cli_ctx.config_manager.load_config(config)
    else:
        cli_ctx.config_manager.load_default_config()
    
    # Set verbose mode
    if verbose:
        cli_ctx.config_manager.set_verbose(True)
    
    # Load existing plugins and commands
    cli_ctx.plugin_system.load_plugins()
    cli_ctx.command_manager.load_dynamic_commands(cli)
    
    logger.info("CLI initialized successfully")

@cli.command()
@click.argument('description')
@click.option('--execute', '-e', is_flag=True, 
              help='Execute the generated command immediately')
@click.option('--save', '-s', is_flag=True, 
              help='Save the generated command permanently')
@click.pass_context
def evolve(ctx, description: str, execute: bool, save: bool):
    """Generate and integrate new functionality using LLM"""
    
    cli_ctx = ctx.obj
    
    try:
        click.echo(f"🧠 Evolving: {description}")
        
        # Generate code using LLM
        generated_code = cli_ctx.code_generator.generate_command(description)
        
        if not generated_code:
            click.echo("❌ Failed to generate code", err=True)
            return
        
        click.echo("✅ Code generated successfully")
        click.echo(f"Generated code preview:\n{generated_code[:200]}...")
        
        if execute or save:
            # Validate generated code
            if not cli_ctx.code_generator.validate_code(generated_code):
                click.echo("❌ Generated code failed validation", err=True)
                return
            
            # Save to history
            command_id = cli_ctx.history_manager.save_command(description, generated_code)
            
            if save:
                # Save permanently
                cli_ctx.command_manager.save_command(command_id, generated_code)
                click.echo(f"💾 Command saved with ID: {command_id}")
            
            if execute:
                # Execute the command
                result = cli_ctx.code_generator.execute_code(generated_code)
                if result:
                    click.echo(f"🚀 Command executed successfully")
                else:
                    click.echo("❌ Command execution failed", err=True)
        
    except Exception as e:
        logger.error(f"Evolution failed: {e}")
        click.echo(f"❌ Evolution failed: {e}", err=True)

@cli.command()
@click.pass_context
def status(ctx):
    """Show current tool status and configuration"""
    
    cli_ctx = ctx.obj
    config = cli_ctx.config_manager.config
    
    click.echo("🔧 Self-Evolving CLI Tool Status")
    click.echo("=" * 40)
    click.echo(f"Version: {config.get('version', 'unknown')}")
    click.echo(f"Config file: {cli_ctx.config_manager.config_path}")
    click.echo(f"LLM provider: {config.get('llm', {}).get('provider', 'default')}")
    click.echo(f"Loaded plugins: {len(cli_ctx.plugin_system.loaded_plugins)}")
    click.echo(f"Dynamic commands: {len(cli_ctx.command_manager.dynamic_commands)}")
    click.echo(f"Command history: {cli_ctx.history_manager.get_history_count()} entries")

@cli.command()
@click.pass_context
def history(ctx):
    """Show command generation history"""
    
    cli_ctx = ctx.obj
    history_entries = cli_ctx.history_manager.get_history()
    
    if not history_entries:
        click.echo("📜 No command history found")
        return
    
    click.echo("📜 Command History")
    click.echo("=" * 40)
    
    for entry in history_entries[-10:]:  # Show last 10 entries
        click.echo(f"ID: {entry['id']}")
        click.echo(f"Description: {entry['description']}")
        click.echo(f"Created: {entry['timestamp']}")
        click.echo("-" * 20)

@cli.command()
@click.argument('command_id')
@click.pass_context
def rollback(ctx, command_id: str):
    """Rollback a command by ID"""
    
    cli_ctx = ctx.obj
    
    try:
        success = cli_ctx.history_manager.rollback_command(command_id)
        if success:
            click.echo(f"↩️ Successfully rolled back command: {command_id}")
        else:
            click.echo(f"❌ Failed to rollback command: {command_id}", err=True)
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        click.echo(f"❌ Rollback failed: {e}", err=True)

@cli.command()
@click.argument('plugin_name')
@click.pass_context
def install_plugin(ctx, plugin_name: str):
    """Install a new plugin"""
    
    cli_ctx = ctx.obj
    
    try:
        success = cli_ctx.plugin_system.install_plugin(plugin_name)
        if success:
            click.echo(f"🔌 Plugin '{plugin_name}' installed successfully")
        else:
            click.echo(f"❌ Failed to install plugin: {plugin_name}", err=True)
    except Exception as e:
        logger.error(f"Plugin installation failed: {e}")
        click.echo(f"❌ Plugin installation failed: {e}", err=True)

@cli.command()
@click.pass_context
def list_plugins(ctx):
    """List all available and loaded plugins"""
    
    cli_ctx = ctx.obj
    
    loaded_plugins = cli_ctx.plugin_system.loaded_plugins
    
    click.echo("🔌 Loaded Plugins")
    click.echo("=" * 40)
    
    if not loaded_plugins:
        click.echo("No plugins loaded")
        return
    
    for plugin_name, plugin in loaded_plugins.items():
        click.echo(f"Name: {plugin_name}")
        click.echo(f"Description: {getattr(plugin, 'description', 'No description')}")
        click.echo(f"Version: {getattr(plugin, 'version', 'unknown')}")
        click.echo("-" * 20)

@cli.command()
@click.argument('query')
@click.pass_context
def llm_query(ctx, query: str):
    """Direct LLM query for experimentation"""
    
    cli_ctx = ctx.obj
    
    try:
        click.echo(f"🤖 Querying LLM: {query}")
        response = cli_ctx.llm_integration.query(query)
        
        if response:
            click.echo("Response:")
            click.echo("-" * 20)
            click.echo(response)
        else:
            click.echo("❌ No response from LLM", err=True)
            
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        click.echo(f"❌ LLM query failed: {e}", err=True)

@cli.command()
@click.pass_context
def providers(ctx):
    """Show LLM provider statistics (multi-provider only)"""
    
    cli_ctx = ctx.obj
    
    if not MULTI_PROVIDER_AVAILABLE or not hasattr(cli_ctx.llm_integration, 'get_provider_stats'):
        click.echo("📊 Provider statistics not available (using basic LLM integration)")
        return
    
    try:
        stats = cli_ctx.llm_integration.get_provider_stats()
        available = cli_ctx.llm_integration.get_available_providers()
        
        click.echo("📊 LLM Provider Statistics")
        click.echo("=" * 40)
        click.echo(f"Available providers: {', '.join(available)}")
        click.echo()
        
        for provider_name, provider_stats in stats.items():
            status = "🟢 Available" if provider_name in available else "🔴 Unavailable"
            click.echo(f"{provider_name.upper()} ({provider_stats['model']}) - {status}")
            click.echo(f"  Requests: {provider_stats['requests']}")
            click.echo(f"  Errors: {provider_stats['errors']} ({provider_stats['error_rate']:.1%})")
            click.echo(f"  Avg Response Time: {provider_stats['avg_response_time']:.2f}s")
            click.echo()
    
    except Exception as e:
        logger.error(f"Failed to get provider stats: {e}")
        click.echo(f"❌ Failed to get provider stats: {e}", err=True)

def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
