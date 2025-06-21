"""
Unit tests for LLM integration
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import requests

from llm_integration import LLMIntegration


class TestLLMIntegration:
    """Test cases for LLM integration"""

    def test_init(self, config_manager):
        """Test LLM integration initialization"""
        llm = LLMIntegration(config_manager)
        
        assert llm.config_manager == config_manager
        assert 'gemini' in llm.api_providers
        assert llm.use_direct_api is True

    def test_query_gemini_success(self, llm_integration):
        """Test successful Gemini API query"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'Test response'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            response = llm_integration.query("Hello, world!")
            
            assert response == "Test response"
            mock_post.assert_called_once()

    def test_query_gemini_with_system_prompt(self, llm_integration):
        """Test Gemini API query with system prompt"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'Test response'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            prompt = "Create a function"
            system_prompt = "You are a helpful assistant"
            
            response = llm_integration.query(prompt, system_prompt)
            
            assert response == "Test response"
            # Check that system prompt was included in the request
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            content_text = request_data['contents'][0]['parts'][0]['text']
            assert "System:" in content_text
            assert system_prompt in content_text

    def test_query_gemini_api_error(self, llm_integration):
        """Test Gemini API error handling"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            response = llm_integration.query("test prompt")
            
            assert response is None

    def test_query_gemini_no_api_key(self, config_manager):
        """Test Gemini API without API key"""
        with patch.dict(os.environ, {}, clear=True):
            llm = LLMIntegration(config_manager)
            response = llm.query("test prompt")
            assert response is None

    def test_query_gemini_malformed_response(self, llm_integration):
        """Test Gemini API with malformed response"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalid": "response"}
            mock_post.return_value = mock_response
            
            response = llm_integration.query("test prompt")
            
            assert response is None

    def test_generate_code(self, llm_integration):
        """Test code generation"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'def hello_world():\n    print("Hello")'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            description = "Create a hello world function"
            
            response = llm_integration.generate_code(description)
            
            assert response is not None
            assert "def hello_world()" in response
            # Verify the system prompt for code generation was used
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            content_text = request_data['contents'][0]['parts'][0]['text']
            assert "Python code generator" in content_text

    def test_generate_code_with_markdown_cleanup(self, llm_integration):
        """Test code generation with markdown cleanup"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{
                            'text': '```python\ndef hello():\n    print("Hello")\n```'
                        }]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            response = llm_integration.generate_code("Create a function")
            
            assert response == 'def hello():\n    print("Hello")'
            assert not response.startswith('```')
            assert not response.endswith('```')

    def test_clean_code_response(self, llm_integration):
        """Test code response cleaning"""
        # Test various markdown formats
        test_cases = [
            ('```python\ncode here\n```', 'code here'),
            ('```\ncode here\n```', 'code here'),
            ('code here', 'code here'),
            ('  ```python\ncode here\n```  ', 'code here'),
        ]
        
        for input_code, expected in test_cases:
            result = llm_integration._clean_code_response(input_code)
            assert result == expected

    def test_validate_code_with_llm(self, llm_integration):
        """Test LLM code validation"""
        # Test SAFE response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'SAFE'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            result = llm_integration.validate_code_with_llm("def hello(): pass")
            assert result is True
            
        # Test UNSAFE response in separate context
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'UNSAFE - contains dangerous code'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            result = llm_integration.validate_code_with_llm("import os; os.system('rm -rf /')")
            assert result is False

    def test_improve_code(self, llm_integration):
        """Test code improvement"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'candidates': [{
                    'content': {
                        'parts': [{'text': 'def func():\n    return "fixed"'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            code = "def broken_function():\n    return undefined_variable"
            error_message = "NameError: name 'undefined_variable' is not defined"
            
            response = llm_integration.improve_code(code, error_message)
            
            assert response is not None
            assert "fixed" in response
            # Verify the system prompt for code improvement was used
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            content_text = request_data['contents'][0]['parts'][0]['text']
            assert "code improver" in content_text
            assert error_message in content_text

    def test_gemini_api_timeout(self, llm_integration):
        """Test Gemini API timeout handling"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            response = llm_integration.query("test prompt")
            
            assert response is None

    def test_gemini_api_connection_error(self, llm_integration):
        """Test Gemini API connection error handling"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            response = llm_integration.query("test prompt")
            
            assert response is None

    @pytest.mark.parametrize("api_key_env", ["GEMINI_API_KEY", "GOOGLE_API_KEY"])
    def test_api_key_detection(self, config_manager, api_key_env):
        """Test that both GEMINI_API_KEY and GOOGLE_API_KEY are detected"""
        with patch.dict(os.environ, {api_key_env: 'test-key'}, clear=True):
            llm = LLMIntegration(config_manager)
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'candidates': [{
                        'content': {'parts': [{'text': 'response'}]}
                    }]
                }
                mock_post.return_value = mock_response
                
                response = llm.query("test")
                assert response == "response"


class TestLLMIntegrationLive:
    """Live API tests (only run with --live flag)"""
    
    @pytest.mark.live
    def test_live_gemini_api(self):
        """Test live Gemini API call"""
        # Only run if GEMINI_API_KEY or GOOGLE_API_KEY is set
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("No Gemini API key found for live testing")
        
        from config import ConfigManager
        config_manager = ConfigManager()
        config_manager.load_default_config()
        
        llm = LLMIntegration(config_manager)
        
        response = llm.query("Say 'Hello from Gemini API test'")
        
        assert response is not None
        assert len(response) > 0
        assert "Hello" in response or "hello" in response

    @pytest.mark.live
    def test_live_code_generation(self):
        """Test live code generation"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("No Gemini API key found for live testing")
        
        from config import ConfigManager
        config_manager = ConfigManager()
        config_manager.load_default_config()
        
        llm = LLMIntegration(config_manager)
        
        response = llm.generate_code("Create a function that adds two numbers")
        
        assert response is not None
        assert "def" in response
        assert "add" in response.lower() or "sum" in response.lower() 