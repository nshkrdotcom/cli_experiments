"""
Pytest configuration and fixtures
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from config import ConfigManager
from llm_integration import LLMIntegration
from code_generator import CodeGenerator


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'version': '0.1.0',
        'verbose': False,
        'llm': {
            'use_direct_api': True,
            'providers': ['gemini'],
            'timeout': 30,
            'temperature': 0.7,
            'max_tokens': 2000,
            'gemini_model': 'gemini-2.0-flash'
        },
        'code_generation': {
            'validation_enabled': True,
            'safe_execution': True,
            'max_code_length': 10000
        },
        'security': {
            'validation_enabled': True,
            'sandbox_enabled': True,
            'max_execution_time': 60,
            'restricted_modules': ['os', 'sys', 'subprocess']
        }
    }


@pytest.fixture
def config_manager(mock_config):
    """Mock config manager"""
    manager = Mock(spec=ConfigManager)
    manager.config = mock_config
    manager.get.side_effect = lambda key, default=None: mock_config.get(key, default)
    return manager


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': 'def hello_world():\n    """Simple hello world function"""\n    print("Hello, World!")\n    return "Hello, World!"'
                }]
            }
        }]
    }


@pytest.fixture
def mock_requests_post(mock_gemini_response):
    """Mock requests.post for API calls"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_gemini_response
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def llm_integration(config_manager):
    """LLM integration instance for testing"""
    return LLMIntegration(config_manager)


@pytest.fixture
def code_generator(config_manager, llm_integration):
    """Code generator instance for testing"""
    return CodeGenerator(config_manager, llm_integration)


@pytest.fixture
def temp_dir():
    """Temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test-gemini-key',
        'GOOGLE_API_KEY': 'test-google-key'
    }):
        yield


# Removed auto-mock to allow specific test control 