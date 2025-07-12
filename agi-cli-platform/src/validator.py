"""
Code validation and safety checks
Enhanced with 5-layer validation system
"""

import ast
import re
import subprocess
import tempfile
import sys
import os
import signal
import resource
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import traceback
from contextlib import contextmanager

from logger import setup_logger

logger = setup_logger(__name__)

# Try to import enhanced validation components
try:
    from enhanced_validator import EnhancedValidator, ValidationResult
    from docker_sandbox import DockerSandbox
    ENHANCED_VALIDATION_AVAILABLE = True
    logger.info("Enhanced validation system available")
except ImportError as e:
    ENHANCED_VALIDATION_AVAILABLE = False
    logger.warning(f"Enhanced validation not available: {e}")

class CodeValidator:
    """Comprehensive code validation for security and correctness"""

    def __init__(self, config_manager, llm_integration=None):
        self.config_manager = config_manager
        self.llm_integration = llm_integration
        self.security_config = config_manager.get('security', {})
        self.validation_rules = self._load_validation_rules()
        
        # Initialize enhanced validator if available
        self.enhanced_validator = None
        if ENHANCED_VALIDATION_AVAILABLE and llm_integration:
            try:
                self.enhanced_validator = EnhancedValidator(config_manager, llm_integration)
                logger.info("Enhanced 5-layer validation system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize enhanced validator: {e}")

    def validate_code(self, code: str, user_input: str = "") -> Tuple[bool, List[str]]:
        """
        Comprehensive code validation
        Returns (is_valid, list_of_issues)
        """
        # Use enhanced validation if available
        if self.enhanced_validator:
            try:
                result = self.enhanced_validator.validate_code_comprehensive(code, user_input)
                logger.info(f"Enhanced validation complete: valid={result.is_valid}, score={result.security_score:.1f}")
                return result.is_valid, result.issues + result.warnings
            except Exception as e:
                logger.error(f"Enhanced validation failed, falling back to basic: {e}")
        
        # Fallback to basic validation
        issues = []

        try:
            # 1. Syntax validation
            syntax_issues = self._validate_syntax(code)
            issues.extend(syntax_issues)

            # 2. Security validation
            security_issues = self._validate_security(code)
            issues.extend(security_issues)

            # 3. AST-based validation
            ast_issues = self._validate_ast(code)
            issues.extend(ast_issues)

            # 4. Pattern-based validation
            pattern_issues = self._validate_patterns(code)
            issues.extend(pattern_issues)

            # 5. Import validation
            import_issues = self._validate_imports(code)
            issues.extend(import_issues)

            is_valid = len(issues) == 0

            if is_valid:
                logger.info("Code validation passed")
            else:
                logger.warning(f"Code validation failed with {len(issues)} issues")

            return is_valid, issues

        except Exception as e:
            logger.error(f"Validation error: {e}")
            issues.append(f"Validation error: {e}")
            return False, issues

    def _validate_syntax(self, code: str) -> List[str]:
        """Validate Python syntax"""
        issues = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        except Exception as e:
            issues.append(f"Parse error: {e}")

        return issues

    def _validate_security(self, code: str) -> List[str]:
        """Security-focused validation"""
        issues = []

        # Check for dangerous function calls
        dangerous_functions = [
            'eval', 'exec', 'compile', '__import__',
            'open', 'file', 'input', 'raw_input',
            'execfile', 'reload', 'vars', 'locals', 'globals'
        ]

        for func in dangerous_functions:
            if re.search(rf'\b{func}\s*\(', code):
                issues.append(f"Dangerous function call: {func}")

        # Check for dangerous modules
        dangerous_imports = [
            'os.system', 'subprocess.call', 'subprocess.run',
            'subprocess.Popen', 'commands.getoutput',
            'platform.system', 'ctypes', 'imp'
        ]

        for imp in dangerous_imports:
            if imp in code:
                issues.append(f"Dangerous import/usage: {imp}")

        # Check for file operations
        file_operations = [
            'open(', 'file(', 'with open', 'pathlib',
            'shutil.', 'glob.glob', 'os.walk', 'os.listdir'
        ]

        for op in file_operations:
            if op in code:
                issues.append(f"File operation detected: {op}")

        # Check for network operations
        network_operations = [
            'urllib', 'requests', 'http', 'socket',
            'ftplib', 'smtplib', 'telnetlib'
        ]

        for op in network_operations:
            if op in code:
                issues.append(f"Network operation detected: {op}")

        return issues

    def _validate_ast(self, code: str) -> List[str]:
        """AST-based validation"""
        issues = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Check for dangerous calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in ['eval', 'exec', 'compile']:
                            issues.append(f"AST: Dangerous function call: {func_name}")

                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            if (node.func.value.id == 'os' and 
                                node.func.attr in ['system', 'popen', 'execl']):
                                issues.append(f"AST: Dangerous os function: {node.func.attr}")

                # Check for dangerous attributes
                if isinstance(node, ast.Attribute):
                    dangerous_attrs = ['__class__', '__bases__', '__subclasses__']
                    if node.attr in dangerous_attrs:
                        issues.append(f"AST: Dangerous attribute access: {node.attr}")

                # Check for lambda functions (potential code injection)
                if isinstance(node, ast.Lambda):
                    issues.append("AST: Lambda function detected (potential security risk)")

        except Exception as e:
            issues.append(f"AST validation error: {e}")

        return issues

    def _validate_patterns(self, code: str) -> List[str]:
        """Pattern-based validation using regex"""
        issues = []

        dangerous_patterns = [
            (r'__.*__', "Dunder method usage"),
            (r'getattr\s*\(', "Dynamic attribute access"),
            (r'setattr\s*\(', "Dynamic attribute setting"),
            (r'hasattr\s*\(', "Attribute checking"),
            (r'delattr\s*\(', "Attribute deletion"),
            (r'dir\s*\(', "Object introspection"),
            (r'type\s*\(', "Type introspection"),
            (r'isinstance\s*\(.*,\s*str\s*\)', "String type checking"),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"Pattern: {description}")

        return issues

    def _validate_imports(self, code: str) -> List[str]:
        """Validate imports against allowed list"""
        issues = []

        allowed_imports = self.config_manager.get('plugins.allowed_imports', [])

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in allowed_imports:
                            issues.append(f"Import not in allowed list: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in allowed_imports:
                        issues.append(f"Import from not in allowed list: {node.module}")

        except Exception as e:
            issues.append(f"Import validation error: {e}")

        return issues

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration"""
        return {
            'max_code_length': self.config_manager.get('code_generation.max_code_length', 10000),
            'max_lines': 500,
            'max_functions': 20,
            'max_classes': 10,
            'max_imports': 20,
            'allow_file_operations': False,
            'allow_network_operations': False,
            'allow_subprocess': False,
            'allow_dynamic_execution': False
        }

    def validate_with_pylint(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code using pylint (if available)"""
        issues = []

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name

            try:
                result = subprocess.run(
                    ['pylint', '--errors-only', '--output-format=text', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.stdout:
                    issues.extend(result.stdout.strip().split('\n'))

            finally:
                Path(temp_path).unlink(missing_ok=True)

            return len(issues) == 0, issues

        except FileNotFoundError:
            # pylint not available
            return True, []
        except Exception as e:
            logger.error(f"Pylint validation error: {e}")
            return True, [f"Pylint error: {e}"]

    def get_validation_report(self, code: str) -> Dict[str, Any]:
        """Get comprehensive validation report"""
        is_valid, issues = self.validate_code(code)

        # Additional metrics
        lines = code.split('\n')
        tree = ast.parse(code) if is_valid else None

        report = {
            'is_valid': is_valid,
            'issues': issues,
            'metrics': {
                'total_lines': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'code_length': len(code),
                'function_count': 0,
                'class_count': 0,
                'import_count': 0
            },
            'validation_timestamp': str(Path().cwd())
        }

        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    report['metrics']['function_count'] += 1
                elif isinstance(node, ast.ClassDef):
                    report['metrics']['class_count'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    report['metrics']['import_count'] += 1

        return report