"""
LLM integration for code generation and queries
"""

import subprocess
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

from logger import setup_logger

logger = setup_logger(__name__)

class LLMIntegration:
    """Handles integration with LLM providers via the 'llm' command"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.llm_config = config_manager.get('llm', {})
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Send a query to the LLM and return the response"""
        try:
            # Build the llm command
            cmd = ['llm']
            
            # Add model if specified
            model = self.llm_config.get('model')
            if model:
                cmd.extend(['-m', model])
            
            # Add system prompt if provided
            if system_prompt:
                cmd.extend(['-s', system_prompt])
            
            # Add the main prompt
            cmd.append(prompt)
            
            # Set environment variables for API keys
            env = os.environ.copy()
            
            # Try to get API key from environment
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
            if api_key:
                env['OPENAI_API_KEY'] = api_key
            
            logger.debug(f"Executing LLM command: {' '.join(cmd[:3])}...")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.llm_config.get('timeout', 30),
                env=env
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                logger.debug(f"LLM response length: {len(response)} characters")
                return response
            else:
                logger.error(f"LLM command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("LLM query timed out")
            return None
        except FileNotFoundError:
            logger.error("'llm' command not found. Please install it first.")
            return None
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return None
    
    def generate_code(self, description: str) -> Optional[str]:
        """Generate Python code based on description"""
        
        system_prompt = """You are a Python code generator for a self-evolving CLI tool.
Generate clean, safe, and functional Python code based on the user's description.
The code should be compatible with the Click framework and follow these guidelines:

1. Use only safe imports and avoid dangerous operations
2. Include proper error handling
3. Add docstrings and comments
4. Return complete, executable code
5. Use Click decorators for CLI commands when appropriate
6. Follow PEP 8 style guidelines

Return ONLY the Python code without any explanations or markdown formatting."""

        user_prompt = f"""Generate Python code for a CLI command with this functionality:
{description}

The code should be a complete function or class that can be dynamically loaded into a Click-based CLI application."""

        return self.query(user_prompt, system_prompt)
    
    def validate_code_with_llm(self, code: str) -> bool:
        """Use LLM to validate generated code for safety and correctness"""
        
        system_prompt = """You are a code validator for a self-evolving CLI tool.
Analyze the provided Python code and respond with only 'SAFE' or 'UNSAFE'.

Check for:
1. Dangerous imports or operations (eval, exec, os.system, etc.)
2. File system operations outside allowed directories
3. Network operations without proper validation
4. Infinite loops or resource exhaustion
5. Code injection vulnerabilities

Respond with only 'SAFE' if the code is acceptable, or 'UNSAFE' if it poses any security risks."""

        user_prompt = f"""Validate this Python code:

```python
{code}
```"""

        response = self.query(user_prompt, system_prompt)
        
        if response and 'SAFE' in response.upper():
            return True
        else:
            logger.warning(f"LLM validation failed: {response}")
            return False
    
    def improve_code(self, code: str, error_message: str) -> Optional[str]:
        """Improve code based on error feedback"""
        
        system_prompt = """You are a Python code improver for a self-evolving CLI tool.
Given code that has an error, fix the issues and return improved code.
Focus on fixing the specific error while maintaining the original functionality.

Return ONLY the improved Python code without any explanations or markdown formatting."""

        user_prompt = f"""Fix this Python code that has an error:

Error: {error_message}

Original code:
```python
{code}
```

Please provide the corrected code."""

        return self.query(user_prompt, system_prompt)
