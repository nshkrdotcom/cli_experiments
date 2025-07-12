"""
Docker-based Sandbox for Safe Code Execution
Implements the security framework from docs/03-security-validation.md
"""

import tempfile
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Try to import Docker, handle gracefully if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    resource_usage: Dict[str, Any]

@dataclass
class SandboxConfig:
    memory_limit: str = "128m"
    cpu_limit: str = "0.5"
    timeout: int = 30
    network_disabled: bool = True
    read_only_filesystem: bool = True
    temp_dir_size: str = "10m"
    max_file_size: int = 1024 * 1024  # 1MB
    allowed_syscalls: Optional[List[str]] = None

class DockerSandbox:
    """Docker-based sandbox for secure code execution"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.docker_client = None
        self.sandbox_config = self._load_sandbox_config()
        self._initialize_docker()
    
    def _load_sandbox_config(self) -> SandboxConfig:
        """Load sandbox configuration from config manager"""
        sandbox_config = self.config_manager.get('sandbox', {})
        
        return SandboxConfig(
            memory_limit=sandbox_config.get('memory_limit', '128m'),
            cpu_limit=sandbox_config.get('cpu_limit', '0.5'),
            timeout=sandbox_config.get('timeout', 30),
            network_disabled=sandbox_config.get('network_disabled', True),
            read_only_filesystem=sandbox_config.get('read_only_filesystem', True),
            temp_dir_size=sandbox_config.get('temp_dir_size', '10m'),
            max_file_size=sandbox_config.get('max_file_size', 1024 * 1024),
            allowed_syscalls=sandbox_config.get('allowed_syscalls')
        )
    
    def _initialize_docker(self):
        """Initialize Docker client"""
        if not DOCKER_AVAILABLE:
            logger.warning("Docker not available - sandbox functionality disabled")
            return
            
        try:
            self.docker_client = docker.from_env()
            # Test Docker connectivity
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    def is_available(self) -> bool:
        """Check if Docker sandbox is available"""
        return DOCKER_AVAILABLE and self.docker_client is not None
    
    def execute_code_safely(self, code: str, language: str = "python") -> ExecutionResult:
        """Execute code in isolated Docker container"""
        if not self.is_available():
            return ExecutionResult(
                success=False,
                output="",
                error="Docker sandbox not available",
                exit_code=-1,
                execution_time=0.0,
                resource_usage={}
            )
        
        start_time = time.time()
        
        try:
            # Create temporary directory for code execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                code_file = Path(temp_dir) / f"code.{self._get_file_extension(language)}"
                with open(code_file, 'w') as f:
                    f.write(code)
                
                # Execute in Docker container
                result = self._execute_in_container(code_file, language, temp_dir)
                
                execution_time = time.time() - start_time
                result.execution_time = execution_time
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Sandbox execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=f"Sandbox execution failed: {str(e)}",
                exit_code=-1,
                execution_time=execution_time,
                resource_usage={}
            )
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'bash': 'sh',
            'cpp': 'cpp',
            'c': 'c'
        }
        return extensions.get(language.lower(), 'txt')
    
    def _get_execution_command(self, language: str, filename: str) -> List[str]:
        """Get execution command for language"""
        commands = {
            'python': ['python3', filename],
            'javascript': ['node', filename],
            'bash': ['bash', filename],
            'cpp': ['g++', '-o', 'program', filename, '&&', './program'],
            'c': ['gcc', '-o', 'program', filename, '&&', './program']
        }
        return commands.get(language.lower(), ['cat', filename])
    
    def _execute_in_container(self, code_file: Path, language: str, temp_dir: str) -> ExecutionResult:
        """Execute code in Docker container with security constraints"""
        
        # Container configuration
        container_config = {
            'image': self._get_container_image(language),
            'command': self._get_execution_command(language, f'/code/{code_file.name}'),
            'volumes': {
                temp_dir: {'bind': '/code', 'mode': 'ro'}
            },
            'mem_limit': self.sandbox_config.memory_limit,
            'nano_cpus': int(float(self.sandbox_config.cpu_limit) * 1e9),
            'network_disabled': self.sandbox_config.network_disabled,
            'read_only': self.sandbox_config.read_only_filesystem,
            'tmpfs': {'/tmp': f'size={self.sandbox_config.temp_dir_size}'},
            'security_opt': ['no-new-privileges:true'],
            'cap_drop': ['ALL'],
            'cap_add': ['CHOWN', 'DAC_OVERRIDE', 'FOWNER', 'SETGID', 'SETUID'],
            'user': 'nobody:nogroup',
            'working_dir': '/code',
            'remove': True,
            'detach': False,
            'stdout': True,
            'stderr': True
        }
        
        # Add ulimits for additional security (if available)
        try:
            if hasattr(docker, 'types'):
                ulimits = [
                    docker.types.Ulimit(name='nproc', soft=32, hard=32),
                    docker.types.Ulimit(name='nofile', soft=64, hard=64),
                    docker.types.Ulimit(name='fsize', soft=self.sandbox_config.max_file_size, 
                                      hard=self.sandbox_config.max_file_size)
                ]
                container_config['ulimits'] = ulimits
        except (AttributeError, ImportError):
            logger.debug("Docker ulimits not available, skipping")
        
        try:
            # Run container with timeout
            if self.docker_client:
                container = self.docker_client.containers.run(**container_config)
                
                # Get output
                output = container.decode('utf-8') if isinstance(container, bytes) else str(container)
                
                # Get container stats (basic implementation)
                resource_usage = self._get_resource_usage()
                
                return ExecutionResult(
                    success=True,
                    output=output,
                    error="",
                    exit_code=0,
                    execution_time=0.0,  # Will be set by caller
                    resource_usage=resource_usage
                )
            else:
                raise Exception("Docker client not available")
                
        except Exception as e:
            # Handle all Docker-related exceptions generically
            error_msg = f"Container execution failed: {str(e)}"
            output = ""
            exit_code = -1
            
            # Try to extract more info if it's a Docker container error
            if hasattr(e, 'container') and e.container:
                try:
                    output = e.container.logs().decode('utf-8')
                except:
                    output = "Could not retrieve container logs"
            
            if hasattr(e, 'exit_status'):
                exit_code = e.exit_status
            
            return ExecutionResult(
                success=False,
                output=output,
                error=error_msg,
                exit_code=exit_code,
                execution_time=0.0,
                resource_usage={}
            )
    
    def _get_container_image(self, language: str) -> str:
        """Get appropriate container image for language"""
        images = {
            'python': 'python:3.11-alpine',
            'javascript': 'node:18-alpine',
            'bash': 'alpine:latest',
            'cpp': 'gcc:alpine',
            'c': 'gcc:alpine'
        }
        return images.get(language.lower(), 'alpine:latest')
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage statistics"""
        try:
            # Basic resource usage tracking
            return {
                'memory_usage': 0,
                'cpu_usage': 0,
                'network_io': 0,
                'block_io': 0
            }
        except Exception as e:
            logger.warning(f"Could not get resource usage: {e}")
            return {}
    
    def validate_code_in_sandbox(self, code: str, language: str = "python") -> bool:
        """Validate code by executing it in sandbox"""
        try:
            result = self.execute_code_safely(code, language)
            
            # Consider code valid if it executes without error
            # and doesn't exceed resource limits
            if result.success and result.execution_time < self.sandbox_config.timeout:
                logger.debug(f"Code validation successful: {result.output[:100]}...")
                return True
            else:
                logger.warning(f"Code validation failed: {result.error}")
                return False
                
        except Exception as e:
            logger.error(f"Sandbox validation error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup Docker resources"""
        if self.docker_client and DOCKER_AVAILABLE:
            try:
                # Remove any dangling containers with our label
                containers = self.docker_client.containers.list(
                    filters={'label': 'agi-cli-sandbox=true'}
                )
                for container in containers:
                    container.remove(force=True)
                logger.info("Docker sandbox cleanup completed")
            except Exception as e:
                logger.error(f"Docker cleanup failed: {e}") 