"""
Unit tests for code generator
"""

import pytest
import ast
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from code_generator import CodeGenerator


class TestCodeGenerator:
    """Test cases for code generator"""

    def test_init(self, config_manager, llm_integration):
        """Test code generator initialization"""
        generator = CodeGenerator(config_manager, llm_integration)
        
        assert generator.config_manager == config_manager
        assert generator.llm_integration == llm_integration

    def test_generate_command_success(self, code_generator):
        """Test successful command generation"""
        with patch.object(code_generator.llm_integration, 'generate_code') as mock_generate:
            mock_generate.return_value = "def hello():\n    print('Hello')"
            
            result = code_generator.generate_command("Create a hello function")
            
            assert result is not None
            assert "def hello()" in result
            mock_generate.assert_called_once_with("Create a hello function")

    def test_generate_command_failure(self, code_generator):
        """Test command generation failure"""
        with patch.object(code_generator.llm_integration, 'generate_code') as mock_generate:
            mock_generate.return_value = None
            
            result = code_generator.generate_command("Invalid request")
            
            assert result is None

    def test_generate_command_too_long(self, code_generator):
        """Test command generation with code too long"""
        long_code = "def hello():\n    pass\n" * 1000  # Very long code
        
        with patch.object(code_generator.llm_integration, 'generate_code') as mock_generate:
            mock_generate.return_value = long_code
            
            result = code_generator.generate_command("Create a function")
            
            assert result is None  # Should be rejected for being too long

    def test_validate_code_success(self, code_generator):
        """Test successful code validation"""
        valid_code = """
def hello_world():
    '''Simple hello world function'''
    print("Hello, World!")
    return "Hello, World!"
"""
        
        with patch.object(code_generator, '_validate_with_llm') as mock_llm_validate:
            mock_llm_validate.return_value = True
            
            result = code_generator.validate_code(valid_code)
            
            assert result is True

    def test_validate_code_syntax_error(self, code_generator):
        """Test code validation with syntax error"""
        invalid_code = "def hello(\n    print('missing closing paren')"
        
        result = code_generator.validate_code(invalid_code)
        
        assert result is False

    def test_validate_code_security_violation(self, code_generator):
        """Test code validation with security violation"""
        dangerous_code = """
import os
def dangerous_function():
    os.system('rm -rf /')
"""
        
        result = code_generator.validate_code(dangerous_code)
        
        assert result is False

    def test_validate_code_disabled(self, code_generator):
        """Test code validation when disabled"""
        code_generator.generation_config['validation_enabled'] = False
        
        # Even invalid code should pass when validation is disabled
        result = code_generator.validate_code("invalid syntax here")
        
        assert result is True

    def test_validate_ast_success(self, code_generator):
        """Test AST validation success"""
        valid_code = "def hello(): return 'Hello'"
        
        result = code_generator._validate_ast(valid_code)
        
        assert result is True

    def test_validate_ast_dangerous_functions(self, code_generator):
        """Test AST validation catches dangerous functions"""
        dangerous_codes = [
            "eval('malicious code')",
            "exec('dangerous code')",
            "compile('code', 'file', 'exec')"
        ]
        
        for code in dangerous_codes:
            result = code_generator._validate_ast(code)
            assert result is False

    def test_validate_ast_restricted_imports(self, code_generator):
        """Test AST validation catches restricted imports"""
        restricted_codes = [
            "import os",
            "import sys", 
            "from subprocess import call"
        ]
        
        for code in restricted_codes:
            result = code_generator._validate_ast(code)
            assert result is False

    def test_validate_security_success(self, code_generator):
        """Test security validation success"""
        safe_code = """
def calculate_sum(a, b):
    return a + b
"""
        
        result = code_generator._validate_security(safe_code)
        
        assert result is True

    def test_validate_security_dangerous_patterns(self, code_generator):
        """Test security validation catches dangerous patterns"""
        dangerous_patterns = [
            "os.system('command')",
            "subprocess.call(['cmd'])",
            "eval(user_input)",
            "exec(malicious_code)",
            "open('/etc/passwd')"
        ]
        
        for pattern in dangerous_patterns:
            code = f"def func():\n    {pattern}"
            result = code_generator._validate_security(code)
            assert result is False

    def test_validate_with_llm_success(self, code_generator):
        """Test LLM validation success"""
        with patch.object(code_generator.llm_integration, 'validate_code_with_llm') as mock_validate:
            mock_validate.return_value = True
            
            result = code_generator._validate_with_llm("safe code")
            
            assert result is True
            mock_validate.assert_called_once_with("safe code")

    def test_validate_with_llm_failure(self, code_generator):
        """Test LLM validation failure"""
        with patch.object(code_generator.llm_integration, 'validate_code_with_llm') as mock_validate:
            mock_validate.return_value = False
            
            result = code_generator._validate_with_llm("unsafe code")
            
            assert result is False

    def test_validate_with_llm_error(self, code_generator):
        """Test LLM validation error handling"""
        with patch.object(code_generator.llm_integration, 'validate_code_with_llm') as mock_validate:
            mock_validate.side_effect = Exception("LLM error")
            
            # Should return True when LLM validation fails (don't block execution)
            result = code_generator._validate_with_llm("code")
            
            assert result is True

    def test_execute_code_success(self, code_generator, temp_dir):
        """Test successful code execution"""
        simple_code = "print('Hello, World!')"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Hello, World!\n"
            mock_run.return_value.stderr = ""
            
            result = code_generator.execute_code(simple_code)
            
            assert result is True

    def test_execute_code_failure(self, code_generator):
        """Test code execution failure"""
        failing_code = "raise Exception('Test error')"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Exception: Test error"
            
            result = code_generator.execute_code(failing_code)
            
            assert result is False

    def test_execute_code_timeout(self, code_generator):
        """Test code execution timeout"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("python", 30)
            
            result = code_generator.execute_code("while True: pass")
            
            assert result is False

    def test_execute_code_sandbox_disabled(self, code_generator):
        """Test code execution with sandbox disabled"""
        code_generator.security_config['sandbox_enabled'] = False
        
        with patch.object(code_generator, '_execute_direct') as mock_direct:
            mock_direct.return_value = True
            
            result = code_generator.execute_code("print('test')")
            
            assert result is True
            mock_direct.assert_called_once()

    def test_execute_direct_success(self, code_generator):
        """Test direct code execution"""
        safe_code = "result = 2 + 2"
        
        result = code_generator._execute_direct(safe_code)
        
        # Direct execution should work for safe code
        assert result is True

    def test_execute_direct_error(self, code_generator):
        """Test direct code execution with error"""
        error_code = "undefined_variable + 1"
        
        result = code_generator._execute_direct(error_code)
        
        assert result is False

    def test_improve_code(self, code_generator):
        """Test code improvement"""
        broken_code = "def func():\n    return undefined_var"
        error_msg = "NameError: name 'undefined_var' is not defined"
        
        with patch.object(code_generator.llm_integration, 'improve_code') as mock_improve:
            with patch.object(code_generator, 'validate_code') as mock_validate:
                mock_improve.return_value = "def func():\n    return 'fixed'"
                mock_validate.return_value = True
                
                result = code_generator.improve_code(broken_code, error_msg)
                
                assert result is not None
                assert "fixed" in result
                mock_improve.assert_called_once_with(broken_code, error_msg)
                mock_validate.assert_called_once_with("def func():\n    return 'fixed'")

    def test_improve_code_failure(self, code_generator):
        """Test code improvement failure"""
        with patch.object(code_generator.llm_integration, 'improve_code') as mock_improve:
            mock_improve.return_value = None
            
            result = code_generator.improve_code("broken code", "error")
            
            assert result is None


class TestCodeGeneratorIntegration:
    """Integration tests for code generator"""

    def test_full_workflow_success(self, code_generator):
        """Test full code generation workflow"""
        description = "Create a function that adds two numbers"
        expected_code = """
def add_numbers(a, b):
    '''Add two numbers and return the result'''
    return a + b
"""
        
        with patch.object(code_generator.llm_integration, 'generate_code') as mock_generate:
            with patch.object(code_generator.llm_integration, 'validate_code_with_llm') as mock_validate:
                mock_generate.return_value = expected_code
                mock_validate.return_value = True
                
                # Generate code
                generated_code = code_generator.generate_command(description)
                assert generated_code is not None
                
                # Validate code
                is_valid = code_generator.validate_code(generated_code)
                assert is_valid is True
                
                # Execute code (mocked)
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = ""
                    
                    executed = code_generator.execute_code(generated_code)
                    assert executed is True

    def test_full_workflow_validation_failure(self, code_generator):
        """Test workflow with validation failure"""
        dangerous_code = "import os; os.system('rm -rf /')"
        
        with patch.object(code_generator.llm_integration, 'generate_code') as mock_generate:
            mock_generate.return_value = dangerous_code
            
            # Generate code
            generated_code = code_generator.generate_command("Delete all files")
            assert generated_code is not None
            
            # Validation should fail
            is_valid = code_generator.validate_code(generated_code)
            assert is_valid is False 