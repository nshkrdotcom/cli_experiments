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

import json
import requests
from typing import Optional, Dict, Any

class LLMIntegration:
    """Handles integration with LLM providers via direct API and fallback to 'llm' command"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.llm_config = config_manager.get('llm', {})
        self.api_providers = {
            'gemini': self._query_gemini,
            'openai': self._query_openai,
            'anthropic': self._query_anthropic,
            'local': self._query_local
        }
        self.use_direct_api = self.llm_config.get('use_direct_api', True)
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Send a query to the LLM and return the response"""
        try:
            # Try direct API first if enabled
            if self.use_direct_api:
                for provider_name in self.llm_config.get('providers', ['gemini']):
                    if provider_name in self.api_providers:
                        try:
                            response = self.api_providers[provider_name](prompt, system_prompt)
                            if response:
                                logger.debug(f"Direct API response from {provider_name}: {len(response)} chars")
                                return response
                        except Exception as e:
                            logger.error(f"Direct API failed for {provider_name}: {e}")
                            # Don't continue to other providers, fail fast for Gemini-only setup
                            return None
            
            # Don't fallback to external llm command for Gemini-only setup
            logger.error("No LLM providers available or all failed")
            return None
            
        except Exception as e:
            logger.error(f"All LLM query methods failed: {e}")
            return None
    
    def _query_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Query Google Gemini API directly"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Build the content parts
        parts = []
        if system_prompt:
            parts.append({"text": f"System: {system_prompt}\n\nUser: {prompt}"})
        else:
            parts.append({"text": prompt})
        
        data = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "temperature": self.llm_config.get('temperature', 0.7),
                "maxOutputTokens": self.llm_config.get('max_tokens', 2000)
            }
        }
        
        model = self.llm_config.get('gemini_model', 'gemini-2.0-flash')
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=self.llm_config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']
                if 'parts' in content and len(content['parts']) > 0:
                    return content['parts'][0]['text'].strip()
            raise Exception("No valid response from Gemini API")
        else:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

    def _query_openai(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Query OpenAI API directly"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.llm_config.get('openai_model', 'gpt-3.5-turbo'),
            "messages": messages,
            "temperature": self.llm_config.get('temperature', 0.7),
            "max_tokens": self.llm_config.get('max_tokens', 2000)
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=self.llm_config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    def _query_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Query Anthropic API directly"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        content = prompt
        if system_prompt:
            content = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "model": self.llm_config.get('anthropic_model', 'claude-3-sonnet-20240229'),
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.llm_config.get('max_tokens', 2000)
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=self.llm_config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text'].strip()
        else:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
    
    def _query_local(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Query local LLM endpoint"""
        endpoint = self.llm_config.get('local_endpoint', 'http://0.0.0.0:11434/api/generate')
        
        data = {
            "model": self.llm_config.get('local_model', 'llama2'),
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False
        }
        
        response = requests.post(
            endpoint,
            json=data,
            timeout=self.llm_config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            raise Exception(f"Local LLM error: {response.status_code} - {response.text}")
    
    def _query_external_command(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Fallback to external llm command"""
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

CRITICAL: Return ONLY the raw Python code without any markdown formatting, code blocks, or explanations. 
Do not include ```python or ``` markers. Start directly with the Python code."""

        user_prompt = f"""Generate Python code for a CLI command with this functionality:
{description}

The code should be a complete function or class that can be dynamically loaded into a Click-based CLI application."""

        response = self.query(user_prompt, system_prompt)
        
        if response:
            # Clean up any markdown formatting that might be included
            response = self._clean_code_response(response)
        
        return response
    
    def _clean_code_response(self, response: str) -> str:
        """Clean up code response by removing markdown formatting"""
        # Remove any leading/trailing whitespace first
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith('```python'):
            response = response[9:]  # Remove ```python
        elif response.startswith('```'):
            response = response[3:]   # Remove ```
        
        if response.endswith('```'):
            response = response[:-3]  # Remove trailing ```
        
        # Remove any leading/trailing whitespace again
        response = response.strip()
        
        return response
    
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
        
        if response:
            response_upper = response.upper().strip()
            if response_upper == 'SAFE' or response_upper.startswith('SAFE '):
                return True
            else:
                logger.warning(f"LLM validation failed: {response}")
                return False
        else:
            logger.warning("LLM validation failed: No response")
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
