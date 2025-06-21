"""
Plugin system for extending functionality
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from logger import setup_logger

logger = setup_logger(__name__)

class PluginSystem:
    """Manages plugin loading, activation, and deactivation"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugin_config = config_manager.get('plugins', {})
        self.loaded_plugins: Dict[str, Any] = {}
        self.active_plugins: Dict[str, Any] = {}
        self.plugin_dirs = self._get_plugin_directories()
    
    def load_plugins(self):
        """Load all available plugins"""
        try:
            if not self.plugin_config.get('auto_load', True):
                logger.info("Plugin auto-loading is disabled")
                return
            
            for plugin_dir in self.plugin_dirs:
                if plugin_dir.exists():
                    self._scan_plugin_directory(plugin_dir)
            
            logger.info(f"Loaded {len(self.loaded_plugins)} plugins")
            
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")
    
    def install_plugin(self, plugin_name: str) -> bool:
        """Install a new plugin"""
        try:
            # For now, we'll generate a plugin using LLM
            # In a real implementation, this could download from a repository
            
            plugin_code = self._generate_plugin_template(plugin_name)
            if not plugin_code:
                return False
            
            # Save plugin to disk
            plugin_file = self.plugin_dirs[0] / f"{plugin_name}.py"
            
            with open(plugin_file, 'w') as f:
                f.write(plugin_code)
            
            # Load the plugin
            return self._load_plugin_file(plugin_file)
            
        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_name}: {e}")
            return False
    
    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin"""
        try:
            if plugin_name not in self.loaded_plugins:
                logger.error(f"Plugin not loaded: {plugin_name}")
                return False
            
            plugin = self.loaded_plugins[plugin_name]
            
            # Call plugin activation method if it exists
            if hasattr(plugin, 'activate'):
                plugin.activate()
            
            self.active_plugins[plugin_name] = plugin
            logger.info(f"Plugin activated: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate plugin {plugin_name}: {e}")
            return False
    
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate an active plugin"""
        try:
            if plugin_name not in self.active_plugins:
                logger.error(f"Plugin not active: {plugin_name}")
                return False
            
            plugin = self.active_plugins[plugin_name]
            
            # Call plugin deactivation method if it exists
            if hasattr(plugin, 'deactivate'):
                plugin.deactivate()
            
            del self.active_plugins[plugin_name]
            logger.info(f"Plugin deactivated: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate plugin {plugin_name}: {e}")
            return False
    
    def get_plugin_commands(self, plugin_name: str) -> List[Any]:
        """Get commands provided by a plugin"""
        try:
            if plugin_name not in self.active_plugins:
                return []
            
            plugin = self.active_plugins[plugin_name]
            
            if hasattr(plugin, 'get_commands'):
                return plugin.get_commands()
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get commands for plugin {plugin_name}: {e}")
            return []
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their status"""
        plugin_list = {}
        
        for name, plugin in self.loaded_plugins.items():
            plugin_list[name] = {
                'name': name,
                'version': getattr(plugin, 'version', 'unknown'),
                'description': getattr(plugin, 'description', 'No description'),
                'active': name in self.active_plugins,
                'file': getattr(plugin, '__file__', 'unknown')
            }
        
        return plugin_list
    
    def _get_plugin_directories(self) -> List[Path]:
        """Get list of plugin directories"""
        dirs = []
        
        for dir_name in self.plugin_config.get('plugin_dirs', ['plugins']):
            plugin_dir = Path(dir_name)
            if not plugin_dir.is_absolute():
                # Make relative to project root
                plugin_dir = Path(__file__).parent.parent / plugin_dir
            
            dirs.append(plugin_dir)
            
            # Ensure directory exists
            plugin_dir.mkdir(parents=True, exist_ok=True)
        
        return dirs
    
    def _scan_plugin_directory(self, plugin_dir: Path):
        """Scan a directory for plugins"""
        try:
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue
                
                self._load_plugin_file(plugin_file)
            
        except Exception as e:
            logger.error(f"Failed to scan plugin directory {plugin_dir}: {e}")
    
    def _load_plugin_file(self, plugin_file: Path) -> bool:
        """Load a plugin from a Python file"""
        try:
            plugin_name = plugin_file.stem
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}",
                plugin_file
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create spec for plugin: {plugin_file}")
                return False
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            plugin_class = None
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Look for class with plugin interface
                if (isinstance(attr, type) and 
                    hasattr(attr, '__init__') and
                    not attr_name.startswith('_')):
                    plugin_class = attr
                    break
            
            if plugin_class:
                # Instantiate plugin
                plugin_instance = plugin_class()
                self.loaded_plugins[plugin_name] = plugin_instance
                
                logger.info(f"Loaded plugin: {plugin_name}")
                
                # Auto-activate if configured
                if self.plugin_config.get('auto_activate', True):
                    self.activate_plugin(plugin_name)
                
                return True
            else:
                logger.error(f"No valid plugin class found in: {plugin_file}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to load plugin file {plugin_file}: {e}")
            return False
    
    def _generate_plugin_template(self, plugin_name: str) -> Optional[str]:
        """Generate a basic plugin template"""
        template = f'''"""
Plugin: {plugin_name}
Auto-generated plugin template
"""

import click
from typing import List, Any

class {plugin_name.title().replace('_', '')}Plugin:
    """
    {plugin_name} plugin for the self-evolving CLI tool
    """
    
    def __init__(self):
        self.name = "{plugin_name}"
        self.version = "1.0.0"
        self.description = "Auto-generated {plugin_name} plugin"
        self.enabled = False
    
    def activate(self):
        """Activate the plugin"""
        self.enabled = True
        print(f"Plugin {{self.name}} activated")
    
    def deactivate(self):
        """Deactivate the plugin"""
        self.enabled = False
        print(f"Plugin {{self.name}} deactivated")
    
    def get_commands(self) -> List[Any]:
        """Return list of Click commands provided by this plugin"""
        return [self.{plugin_name}_command]
    
    @click.command(name="{plugin_name}")
    @click.option('--message', '-m', default="Hello from {plugin_name}!", 
                  help='Message to display')
    def {plugin_name}_command(self, message: str):
        """
        Example command provided by {plugin_name} plugin
        """
        click.echo(f"🔌 {{message}}")

# Plugin entry point
plugin_class = {plugin_name.title().replace('_', '')}Plugin
'''
        return template
