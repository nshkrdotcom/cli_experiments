"""
Dynamic command management and loading
"""

import importlib.util
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
import pickle
import click

from logger import setup_logger

logger = setup_logger(__name__)

class CommandManager:
    """Manages dynamic loading and registration of CLI commands"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.dynamic_commands: Dict[str, Any] = {}
        self.command_registry: Dict[str, Dict[str, Any]] = {}
        self.generated_dir = Path(config_manager.get('paths.generated_dir', 'generated'))
        self.generated_dir.mkdir(exist_ok=True)
    
    def save_command(self, command_id: str, code: str) -> bool:
        """Save a generated command permanently"""
        try:
            # Create command file
            command_file = self.generated_dir / f"{command_id}.py"
            
            with open(command_file, 'w') as f:
                f.write(code)
            
            # Save metadata
            metadata = {
                'id': command_id,
                'file': str(command_file),
                'code': code,
                'created_at': str(Path(command_file).stat().st_mtime)
            }
            
            self.command_registry[command_id] = metadata
            self._save_registry()
            
            logger.info(f"Command saved: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save command {command_id}: {e}")
            return False
    
    def load_dynamic_commands(self, cli_group):
        """Load all saved dynamic commands into the CLI"""
        try:
            self._load_registry()
            
            for command_id, metadata in self.command_registry.items():
                command_file = Path(metadata['file'])
                
                if command_file.exists():
                    self._load_command_file(command_file, cli_group)
                else:
                    logger.warning(f"Command file not found: {command_file}")
            
            logger.info(f"Loaded {len(self.dynamic_commands)} dynamic commands")
            
        except Exception as e:
            logger.error(f"Failed to load dynamic commands: {e}")
    
    def delete_command(self, command_id: str) -> bool:
        """Delete a saved command"""
        try:
            if command_id not in self.command_registry:
                logger.error(f"Command not found: {command_id}")
                return False
            
            metadata = self.command_registry[command_id]
            command_file = Path(metadata['file'])
            
            # Remove file
            if command_file.exists():
                command_file.unlink()
            
            # Remove from registry
            del self.command_registry[command_id]
            self._save_registry()
            
            # Remove from dynamic commands
            if command_id in self.dynamic_commands:
                del self.dynamic_commands[command_id]
            
            logger.info(f"Command deleted: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete command {command_id}: {e}")
            return False
    
    def list_commands(self) -> List[Dict[str, Any]]:
        """List all saved commands"""
        return [
            {
                'id': cmd_id,
                'file': metadata['file'],
                'created_at': metadata.get('created_at', 'unknown')
            }
            for cmd_id, metadata in self.command_registry.items()
        ]
    
    def get_command_code(self, command_id: str) -> Optional[str]:
        """Get the source code of a command"""
        if command_id in self.command_registry:
            return self.command_registry[command_id].get('code')
        return None
    
    def _load_command_file(self, command_file: Path, cli_group):
        """Load a command from a Python file"""
        try:
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"dynamic_command_{command_file.stem}",
                command_file
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create spec for {command_file}")
                return
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Click commands in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a Click command
                if hasattr(attr, '__click_params__'):
                    # Add command to CLI group
                    cli_group.add_command(attr)
                    
                    command_id = command_file.stem
                    self.dynamic_commands[command_id] = attr
                    
                    logger.info(f"Loaded dynamic command: {attr_name}")
            
        except Exception as e:
            logger.error(f"Failed to load command file {command_file}: {e}")
    
    def _save_registry(self):
        """Save command registry to disk"""
        try:
            registry_file = self.generated_dir / "command_registry.pkl"
            
            with open(registry_file, 'wb') as f:
                pickle.dump(self.command_registry, f)
            
            logger.debug("Command registry saved")
            
        except Exception as e:
            logger.error(f"Failed to save command registry: {e}")
    
    def _load_registry(self):
        """Load command registry from disk"""
        try:
            registry_file = self.generated_dir / "command_registry.pkl"
            
            if registry_file.exists():
                with open(registry_file, 'rb') as f:
                    self.command_registry = pickle.load(f)
                
                logger.debug("Command registry loaded")
            else:
                self.command_registry = {}
                logger.debug("No existing command registry found")
            
        except Exception as e:
            logger.error(f"Failed to load command registry: {e}")
            self.command_registry = {}
    
    def create_command_template(self, command_name: str, description: str) -> str:
        """Create a template for a new command"""
        template = f'''"""
Generated command: {command_name}
Description: {description}
"""

import click

@click.command(name="{command_name}")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def {command_name.replace('-', '_')}(verbose):
    """
    {description}
    """
    try:
        if verbose:
            click.echo(f"Executing {command_name}...")
        
        # TODO: Implement command logic here
        click.echo(f"Command {command_name} executed successfully!")
        
    except Exception as e:
        click.echo(f"Error in {command_name}: {{e}}", err=True)

# Make the command available for dynamic loading
__all__ = ["{command_name.replace('-', '_')}"]
'''
        return template
