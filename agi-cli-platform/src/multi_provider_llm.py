"""
Multi-Provider LLM Integration with Fallback Support
Implements the multi-provider architecture from docs/02-self-evolution-engine.md
"""

import os
import json
import asyncio
import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import requests

from logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    tokens_used: int
    response_time: float
    success: bool
    error: Optional[str] = None

@dataclass
class ProviderConfig:
    name: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    timeout: int = 30
    max_tokens: int = 2000
    temperature: float = 0.7
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.model = config.model
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
    
    @abstractmethod
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send query to the LLM provider"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        avg_response_time = (self._total_response_time / self._request_count 
                           if self._request_count > 0 else 0)
        error_rate = (self._error_count / self._request_count 
                     if self._request_count > 0 else 0)
        
        return {
            'name': self.name,
            'model': self.model,
            'requests': self._request_count,
            'errors': self._error_count,
            'error_rate': error_rate,
            'avg_response_time': avg_response_time,
            'enabled': self.config.enabled
        }
    
    def _record_request(self, response_time: float, success: bool):
        """Record request statistics"""
        self._request_count += 1
        self._total_response_time += response_time
        if not success:
            self._error_count += 1

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            logger.warning("Gemini API key not found")
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.config.enabled)
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=0.0, success=False,
                error="Gemini provider not available"
            )
        
        start_time = time.time()
        
        try:
            headers = {'Content-Type': 'application/json'}
            
            # Build the content parts
            parts = []
            if system_prompt:
                parts.append({"text": f"System: {system_prompt}\n\nUser: {prompt}"})
            else:
                parts.append({"text": prompt})
            
            data = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens
                }
            }
            
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}'
            
            response = requests.post(
                url, headers=headers, json=data, timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        text = content['parts'][0]['text'].strip()
                        
                        # Estimate tokens (rough approximation)
                        tokens_used = len(text.split()) + len(prompt.split())
                        
                        self._record_request(response_time, True)
                        
                        return LLMResponse(
                            content=text, provider=self.name, model=self.model,
                            tokens_used=tokens_used, response_time=response_time,
                            success=True
                        )
                
                error_msg = "No valid response from Gemini API"
            else:
                error_msg = f"Gemini API error: {response.status_code} - {response.text}"
            
            self._record_request(response_time, False)
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=response_time, success=False,
                error=error_msg
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, False)
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=response_time, success=False,
                error=f"Gemini request failed: {str(e)}"
            )

class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OpenAI API key not found")
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.config.enabled)
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=0.0, success=False,
                error="OpenAI provider not available"
            )
        
        start_time = time.time()
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers, json=data, timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                tokens_used = result.get('usage', {}).get('total_tokens', 0)
                
                self._record_request(response_time, True)
                
                return LLMResponse(
                    content=content, provider=self.name, model=self.model,
                    tokens_used=tokens_used, response_time=response_time,
                    success=True
                )
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                self._record_request(response_time, False)
                return LLMResponse(
                    content="", provider=self.name, model=self.model,
                    tokens_used=0, response_time=response_time, success=False,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, False)
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=response_time, success=False,
                error=f"OpenAI request failed: {str(e)}"
            )

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("Anthropic API key not found")
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.config.enabled)
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=0.0, success=False,
                error="Anthropic provider not available"
            )
        
        start_time = time.time()
        
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            content = prompt
            if system_prompt:
                content = f"{system_prompt}\n\n{prompt}"
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers, json=data, timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text'].strip()
                tokens_used = result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0)
                
                self._record_request(response_time, True)
                
                return LLMResponse(
                    content=content, provider=self.name, model=self.model,
                    tokens_used=tokens_used, response_time=response_time,
                    success=True
                )
            else:
                error_msg = f"Anthropic API error: {response.status_code} - {response.text}"
                self._record_request(response_time, False)
                return LLMResponse(
                    content="", provider=self.name, model=self.model,
                    tokens_used=0, response_time=response_time, success=False,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, False)
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=response_time, success=False,
                error=f"Anthropic request failed: {str(e)}"
            )

class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider (Ollama, etc.)"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.endpoint = config.base_url or 'http://localhost:11434/api/generate'
    
    def is_available(self) -> bool:
        if not self.config.enabled:
            return False
        
        try:
            # Quick health check
            response = requests.get(
                self.endpoint.replace('/api/generate', '/api/tags'),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=0.0, success=False,
                error="Local LLM provider not available"
            )
        
        start_time = time.time()
        
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False
            }
            
            response = requests.post(
                self.endpoint, json=data, timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '').strip()
                
                # Estimate tokens
                tokens_used = len(content.split()) + len(prompt.split())
                
                self._record_request(response_time, True)
                
                return LLMResponse(
                    content=content, provider=self.name, model=self.model,
                    tokens_used=tokens_used, response_time=response_time,
                    success=True
                )
            else:
                error_msg = f"Local LLM error: {response.status_code} - {response.text}"
                self._record_request(response_time, False)
                return LLMResponse(
                    content="", provider=self.name, model=self.model,
                    tokens_used=0, response_time=response_time, success=False,
                    error=error_msg
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self._record_request(response_time, False)
            return LLMResponse(
                content="", provider=self.name, model=self.model,
                tokens_used=0, response_time=response_time, success=False,
                error=f"Local LLM request failed: {str(e)}"
            )

class MultiProviderLLM:
    """Multi-provider LLM integration with intelligent fallback"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.fallback_order: List[str] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        llm_config = self.config_manager.get('llm', {})
        
        # Default provider configurations
        default_configs = {
            'gemini': ProviderConfig(
                name='gemini',
                api_key='',
                model=llm_config.get('gemini_model', 'gemini-2.0-flash'),
                priority=1
            ),
            'openai': ProviderConfig(
                name='openai',
                api_key='',
                model=llm_config.get('openai_model', 'gpt-3.5-turbo'),
                priority=2
            ),
            'anthropic': ProviderConfig(
                name='anthropic',
                api_key='',
                model=llm_config.get('anthropic_model', 'claude-3-sonnet-20240229'),
                priority=3
            ),
            'local': ProviderConfig(
                name='local',
                api_key='',
                model=llm_config.get('local_model', 'llama2'),
                base_url=llm_config.get('local_endpoint', 'http://localhost:11434/api/generate'),
                priority=4
            )
        }
        
        # Override with user configuration
        provider_configs = llm_config.get('providers', {})
        for provider_name, config_data in provider_configs.items():
            if provider_name in default_configs:
                # Update default config with user settings
                for key, value in config_data.items():
                    if hasattr(default_configs[provider_name], key):
                        setattr(default_configs[provider_name], key, value)
        
        # Initialize providers
        provider_classes = {
            'gemini': GeminiProvider,
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'local': LocalLLMProvider
        }
        
        for provider_name, config in default_configs.items():
            if provider_name in provider_classes:
                try:
                    provider = provider_classes[provider_name](config)
                    self.providers[provider_name] = provider
                    logger.info(f"Initialized {provider_name} provider")
                except Exception as e:
                    logger.error(f"Failed to initialize {provider_name} provider: {e}")
        
        # Set fallback order based on priority and availability
        self.fallback_order = sorted(
            [name for name, provider in self.providers.items() if provider.is_available()],
            key=lambda name: self.providers[name].config.priority
        )
        
        logger.info(f"Provider fallback order: {self.fallback_order}")
    
    def query_with_fallback(self, prompt: str, system_prompt: Optional[str] = None, 
                           max_retries: int = 3) -> LLMResponse:
        """Query LLM with automatic fallback to other providers"""
        
        if not self.fallback_order:
            return LLMResponse(
                content="", provider="none", model="none",
                tokens_used=0, response_time=0.0, success=False,
                error="No LLM providers available"
            )
        
        last_error = "Unknown error"
        
        for provider_name in self.fallback_order:
            provider = self.providers[provider_name]
            
            if not provider.is_available():
                logger.debug(f"Skipping unavailable provider: {provider_name}")
                continue
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Trying {provider_name} (attempt {attempt + 1}/{max_retries})")
                    response = provider.query(prompt, system_prompt)
                    
                    if response.success:
                        logger.info(f"Successful response from {provider_name}")
                        return response
                    else:
                        last_error = response.error or "Unknown provider error"
                        logger.warning(f"{provider_name} failed: {last_error}")
                        
                        # Don't retry on certain errors
                        if "API key" in last_error or "authentication" in last_error.lower():
                            break
                        
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"{provider_name} exception: {last_error}")
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return LLMResponse(
            content="", provider="failed", model="none",
            tokens_used=0, response_time=0.0, success=False,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        return {
            name: provider.get_stats() 
            for name, provider in self.providers.items()
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of currently available providers"""
        return [
            name for name, provider in self.providers.items() 
            if provider.is_available()
        ]
    
    def refresh_availability(self):
        """Refresh provider availability and update fallback order"""
        available_providers = []
        
        for name, provider in self.providers.items():
            if provider.is_available():
                available_providers.append(name)
        
        self.fallback_order = sorted(
            available_providers,
            key=lambda name: self.providers[name].config.priority
        )
        
        logger.info(f"Updated provider fallback order: {self.fallback_order}")
    
    # Compatibility methods for existing LLMIntegration interface
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Compatibility method for existing interface"""
        response = self.query_with_fallback(prompt, system_prompt)
        return response.content if response.success else None
    
    def generate_code(self, description: str) -> Optional[str]:
        """Generate code with multi-provider fallback"""
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
        
        response = self.query_with_fallback(description, system_prompt)
        if response.success:
            return self._clean_code_response(response.content)
        return None
    
    def validate_code_with_llm(self, code: str) -> bool:
        """Validate code using LLM with multi-provider fallback"""
        system_prompt = """You are a code validator for a self-evolving CLI tool.
Analyze the provided Python code and respond with only 'SAFE' or 'UNSAFE'.

Check for:
1. Dangerous imports or operations (eval, exec, os.system, etc.)
2. File system operations outside allowed directories
3. Network operations without proper validation
4. Infinite loops or resource exhaustion
5. Code injection vulnerabilities

Respond with only 'SAFE' if the code is acceptable, or 'UNSAFE' if it poses any security risks."""
        
        response = self.query_with_fallback(code, system_prompt)
        if response.success:
            return response.content.strip().upper() == 'SAFE'
        return False
    
    def _clean_code_response(self, response: str) -> str:
        """Clean and extract code from LLM response"""
        # Remove markdown code blocks
        if '```python' in response:
            start = response.find('```python') + 9
            end = response.find('```', start)
            if end != -1:
                response = response[start:end]
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end != -1:
                response = response[start:end]
        
        return response.strip() 