"""
Configuration management for the self-evolving CLI tool
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

from logger import setup_logger

logger = setup_logger(__name__)

class ConfigManager:
    """Manages configuration loading, saving, and validation"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_path: Optional[Path] = None
        self.verbose: bool = False
    
    def load_default_config(self):
        """Load the default configuration file"""
        default_config_path = Path(__file__).parent.parent / "config" / "default.yaml"
        self.load_config(str(default_config_path))
    
    def load_config(self, config_path: str):
        """Load configuration from a YAML file"""
        try:
            self.config_path = Path(config_path)
            
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {config_path}")
                self._create_default_config()
                return
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            
            logger.info(f"Configuration loaded from: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._create_default_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            if not self.config_path:
                self.config_path = Path.home() / ".evolve_cli_config.yaml"
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Config set: {key} = {value}")
    
    def set_verbose(self, verbose: bool):
        """Set verbose mode"""
        self.verbose = verbose
        self.set('verbose', verbose)
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            'version': '0.1.0',
            'verbose': False,
            'llm': {
                'provider': 'default',
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 2000,
                'timeout': 30
            },
            'code_generation': {
                'validation_enabled': True,
                'safe_execution': True,
                'backup_enabled': True,
                'max_code_length': 10000
            },
            'history': {
                'max_entries': 1000,
                'auto_cleanup': True,
                'backup_path': 'backups'
            },
            'plugins': {
                'auto_load': True,
                'plugin_dirs': ['plugins'],
                'allowed_imports': [
                    'os', 'sys', 'pathlib', 'json', 'yaml', 'click',
                    'datetime', 'time', 'subprocess', 'shutil', 'glob'
                ]
            },
            'security': {
                'restricted_modules': [
                    'eval', 'exec', 'compile', '__import__'
                ],
                'max_execution_time': 60,
                'sandbox_enabled': True
            },
            'paths': {
                'generated_dir': 'generated',
                'plugins_dir': 'plugins',
                'templates_dir': 'templates',
                'logs_dir': 'logs',
                'backups_dir': 'backups'
            }
        }
        
        logger.info("Default configuration created")
