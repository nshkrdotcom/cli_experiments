"""
Code generation and execution pipeline
"""

import ast
import importlib.util
import sys
import tempfile
import subprocess
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
import uuid

from logger import setup_logger

logger = setup_logger(__name__)

class CodeGenerator:
    """Handles code generation, validation, and execution"""
    
    def __init__(self, config_manager, llm_integration):
        self.config_manager = config_manager
        self.llm_integration = llm_integration
        self.generation_config = config_manager.get('code_generation', {})
        self.security_config = config_manager.get('security', {})
    
    def generate_command(self, description: str) -> Optional[str]:
        """Generate a new CLI command based on description"""
        try:
            logger.info(f"Generating command: {description}")
            
            # Use LLM to generate code
            generated_code = self.llm_integration.generate_code(description)
            
            if not generated_code:
                logger.error("Failed to generate code from LLM")
                return None
            
            # Basic length check
            max_length = self.generation_config.get('max_code_length', 10000)
            if len(generated_code) > max_length:
                logger.error(f"Generated code too long: {len(generated_code)} > {max_length}")
                return None
            
            logger.info(f"Code generated successfully: {len(generated_code)} characters")
            return generated_code
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return None
    
    def validate_code(self, code: str) -> bool:
        """Validate generated code for safety and correctness"""
        try:
            if not self.generation_config.get('validation_enabled', True):
                logger.warning("Code validation is disabled")
                return True
            
            # Step 1: AST parsing validation
            if not self._validate_ast(code):
                return False
            
            # Step 2: Security validation
            if not self._validate_security(code):
                return False
            
            # Step 3: LLM-based validation (if available)
            if not self._validate_with_llm(code):
                return False
            
            logger.info("Code validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return False
    
    def execute_code(self, code: str) -> bool:
        """Execute generated code in a controlled environment"""
        try:
            if not self.generation_config.get('safe_execution', True):
                logger.warning("Safe execution is disabled")
            
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name
            
            try:
                # Execute in a subprocess for isolation
                if self.security_config.get('sandbox_enabled', True):
                    return self._execute_sandboxed(temp_path)
                else:
                    return self._execute_direct(code)
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return False
    
    def _validate_ast(self, code: str) -> bool:
        """Validate code using AST parsing"""
        try:
            tree = ast.parse(code)
            
            # Check for dangerous operations
            dangerous_nodes = []
            
            for node in ast.walk(tree):
                # Check for eval/exec calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile']:
                            dangerous_nodes.append(f"Dangerous function: {node.func.id}")
                
                # Check for dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.security_config.get('restricted_modules', []):
                            dangerous_nodes.append(f"Restricted import: {alias.name}")
                
                if isinstance(node, ast.ImportFrom):
                    if node.module in self.security_config.get('restricted_modules', []):
                        dangerous_nodes.append(f"Restricted import from: {node.module}")
            
            if dangerous_nodes:
                logger.error(f"AST validation failed: {dangerous_nodes}")
                return False
            
            logger.debug("AST validation passed")
            return True
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated code: {e}")
            return False
        except Exception as e:
            logger.error(f"AST validation error: {e}")
            return False
    
    def _validate_security(self, code: str) -> bool:
        """Basic security validation using string analysis"""
        try:
            restricted_patterns = [
                'os.system', 'subprocess.call', 'eval(', 'exec(',
                '__import__', 'open(', 'file(', 'input(',
                'raw_input(', 'execfile(', 'reload('
            ]
            
            for pattern in restricted_patterns:
                if pattern in code:
                    logger.error(f"Security validation failed: found '{pattern}'")
                    return False
            
            logger.debug("Security validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return False
    
    def _validate_with_llm(self, code: str) -> bool:
        """Use LLM for additional code validation"""
        try:
            return self.llm_integration.validate_code_with_llm(code)
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            # If LLM validation fails, don't block execution
            return True
    
    def _execute_sandboxed(self, script_path: str) -> bool:
        """Execute code in a sandboxed subprocess"""
        try:
            timeout = self.security_config.get('max_execution_time', 60)
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(script_path).parent
            )
            
            if result.returncode == 0:
                logger.info("Sandboxed execution completed successfully")
                if result.stdout:
                    logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"Sandboxed execution failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Code execution timed out")
            return False
        except Exception as e:
            logger.error(f"Sandboxed execution error: {e}")
            return False
    
    def _execute_direct(self, code: str) -> bool:
        """Execute code directly in the current process (less safe)"""
        try:
            # Create a restricted globals environment
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'bool': bool,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                }
            }
            
            exec(code, restricted_globals)
            logger.info("Direct execution completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Direct execution failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def improve_code(self, code: str, error_message: str) -> Optional[str]:
        """Improve code based on error feedback"""
        try:
            improved_code = self.llm_integration.improve_code(code, error_message)
            
            if improved_code and self.validate_code(improved_code):
                logger.info("Code improved successfully")
                return improved_code
            else:
                logger.error("Code improvement failed validation")
                return None
                
        except Exception as e:
            logger.error(f"Code improvement failed: {e}")
            return None
