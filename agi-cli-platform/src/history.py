"""
Command history and rollback capabilities
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil

from logger import setup_logger

logger = setup_logger(__name__)

class HistoryManager:
    """Manages command history, backups, and rollbacks"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.history_config = config_manager.get('history', {})
        self.history_dir = Path(config_manager.get('paths.backups_dir', 'backups'))
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "command_history.json"
        self.history_data = self._load_history()
    
    def save_command(self, description: str, code: str) -> str:
        """Save a command to history"""
        try:
            command_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().isoformat()
            
            entry = {
                'id': command_id,
                'description': description,
                'code': code,
                'timestamp': timestamp,
                'status': 'saved'
            }
            
            # Save code to separate file
            code_file = self.history_dir / f"{command_id}.py"
            with open(code_file, 'w') as f:
                f.write(code)
            
            entry['code_file'] = str(code_file)
            
            # Add to history
            self.history_data.append(entry)
            
            # Cleanup old entries if needed
            self._cleanup_history()
            
            # Save history
            self._save_history()
            
            logger.info(f"Command saved to history: {command_id}")
            return command_id
            
        except Exception as e:
            logger.error(f"Failed to save command to history: {e}")
            return ""
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get command history"""
        history = sorted(self.history_data, key=lambda x: x['timestamp'], reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    def get_history_count(self) -> int:
        """Get total number of history entries"""
        return len(self.history_data)
    
    def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific command by ID"""
        for entry in self.history_data:
            if entry['id'] == command_id:
                return entry
        return None
    
    def rollback_command(self, command_id: str) -> bool:
        """Rollback a command (mark as inactive)"""
        try:
            entry = self.get_command(command_id)
            if not entry:
                logger.error(f"Command not found in history: {command_id}")
                return False
            
            # Create rollback entry
            rollback_entry = {
                'id': str(uuid.uuid4())[:8],
                'description': f"Rollback of {command_id}: {entry['description']}",
                'code': f"# Rollback of command {command_id}\n# Original: {entry['description']}\npass",
                'timestamp': datetime.now().isoformat(),
                'status': 'rollback',
                'rollback_of': command_id
            }
            
            self.history_data.append(rollback_entry)
            
            # Mark original as rolled back
            entry['status'] = 'rolled_back'
            entry['rolled_back_at'] = datetime.now().isoformat()
            
            self._save_history()
            
            logger.info(f"Command rolled back: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback command {command_id}: {e}")
            return False
    
    def delete_command(self, command_id: str) -> bool:
        """Delete a command from history"""
        try:
            entry = self.get_command(command_id)
            if not entry:
                logger.error(f"Command not found in history: {command_id}")
                return False
            
            # Remove code file
            code_file = Path(entry.get('code_file', ''))
            if code_file.exists():
                code_file.unlink()
            
            # Remove from history
            self.history_data = [e for e in self.history_data if e['id'] != command_id]
            
            self._save_history()
            
            logger.info(f"Command deleted from history: {command_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete command {command_id}: {e}")
            return False
    
    def backup_system_state(self) -> str:
        """Create a full system backup"""
        try:
            backup_id = str(uuid.uuid4())[:8]
            backup_timestamp = datetime.now().isoformat()
            backup_dir = self.history_dir / f"backup_{backup_id}"
            backup_dir.mkdir(exist_ok=True)
            
            # Backup configuration
            config_backup = backup_dir / "config.json"
            with open(config_backup, 'w') as f:
                json.dump(self.config_manager.config, f, indent=2)
            
            # Backup generated commands
            generated_dir = Path(self.config_manager.get('paths.generated_dir', 'generated'))
            if generated_dir.exists():
                shutil.copytree(generated_dir, backup_dir / "generated", dirs_exist_ok=True)
            
            # Backup plugins
            plugins_dir = Path(self.config_manager.get('paths.plugins_dir', 'plugins'))
            if plugins_dir.exists():
                shutil.copytree(plugins_dir, backup_dir / "plugins", dirs_exist_ok=True)
            
            # Create backup metadata
            backup_metadata = {
                'id': backup_id,
                'timestamp': backup_timestamp,
                'description': 'Full system backup',
                'type': 'system_backup',
                'files': [
                    str(config_backup),
                    str(backup_dir / "generated"),
                    str(backup_dir / "plugins")
                ]
            }
            
            metadata_file = backup_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(backup_metadata, f, indent=2)
            
            # Add to history
            history_entry = {
                'id': backup_id,
                'description': 'System backup created',
                'code': '# System backup - no code',
                'timestamp': backup_timestamp,
                'status': 'backup',
                'backup_dir': str(backup_dir)
            }
            
            self.history_data.append(history_entry)
            self._save_history()
            
            logger.info(f"System backup created: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create system backup: {e}")
            return ""
    
    def restore_system_backup(self, backup_id: str) -> bool:
        """Restore from a system backup"""
        try:
            backup_entry = self.get_command(backup_id)
            if not backup_entry or backup_entry.get('status') != 'backup':
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_dir = Path(backup_entry['backup_dir'])
            if not backup_dir.exists():
                logger.error(f"Backup directory not found: {backup_dir}")
                return False
            
            # Restore configuration
            config_backup = backup_dir / "config.json"
            if config_backup.exists():
                with open(config_backup, 'r') as f:
                    restored_config = json.load(f)
                self.config_manager.config = restored_config
                self.config_manager.save_config()
            
            # Restore generated commands
            generated_backup = backup_dir / "generated"
            generated_dir = Path(self.config_manager.get('paths.generated_dir', 'generated'))
            if generated_backup.exists():
                if generated_dir.exists():
                    shutil.rmtree(generated_dir)
                shutil.copytree(generated_backup, generated_dir)
            
            # Restore plugins
            plugins_backup = backup_dir / "plugins"
            plugins_dir = Path(self.config_manager.get('paths.plugins_dir', 'plugins'))
            if plugins_backup.exists():
                if plugins_dir.exists():
                    shutil.rmtree(plugins_dir)
                shutil.copytree(plugins_backup, plugins_dir)
            
            # Create restore entry
            restore_entry = {
                'id': str(uuid.uuid4())[:8],
                'description': f"Restored from backup {backup_id}",
                'code': f"# Restored from backup {backup_id}",
                'timestamp': datetime.now().isoformat(),
                'status': 'restore',
                'restored_from': backup_id
            }
            
            self.history_data.append(restore_entry)
            self._save_history()
            
            logger.info(f"System restored from backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore system backup {backup_id}: {e}")
            return False
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history_data, f, indent=2)
            
            logger.debug("History saved")
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def _cleanup_history(self):
        """Clean up old history entries"""
        try:
            max_entries = self.history_config.get('max_entries', 1000)
            
            if len(self.history_data) > max_entries:
                # Sort by timestamp and keep the most recent
                sorted_history = sorted(self.history_data, key=lambda x: x['timestamp'], reverse=True)
                entries_to_remove = sorted_history[max_entries:]
                
                # Remove old code files
                for entry in entries_to_remove:
                    code_file = Path(entry.get('code_file', ''))
                    if code_file.exists():
                        code_file.unlink()
                
                # Keep only recent entries
                self.history_data = sorted_history[:max_entries]
                
                logger.info(f"Cleaned up {len(entries_to_remove)} old history entries")
        
        except Exception as e:
            logger.error(f"Failed to cleanup history: {e}")
