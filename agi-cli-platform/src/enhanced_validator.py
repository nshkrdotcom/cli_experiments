"""
Enhanced 5-Layer Validation System
Implements the comprehensive validation pipeline from docs/03-security-validation.md
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
from dataclasses import dataclass

from logger import setup_logger
from docker_sandbox import DockerSandbox, ExecutionResult

logger = setup_logger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    security_score: float
    issues: List[str]
    warnings: List[str]
    layer_results: Dict[str, bool]
    execution_result: Optional[ExecutionResult] = None

class InputSanitizer:
    """Layer 1: Input Sanitization and Prompt Injection Prevention"""
    
    def __init__(self):
        self.dangerous_patterns = [
            # Prompt injection attempts
            r'ignore\s+previous\s+instructions',
            r'system\s*:\s*you\s+are\s+now',
            r'jailbreak|roleplay|pretend',
            
            # Code injection patterns
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
        ]
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input before sending to LLM"""
        
        # Remove dangerous patterns
        sanitized = user_input
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)
        
        # Limit input length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "... [TRUNCATED]"
        
        # Basic escaping
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized
    
    def validate_llm_response(self, response: str) -> Tuple[bool, List[str]]:
        """Validate LLM response for safety"""
        
        issues = []
        
        # Check for suspicious patterns in response
        suspicious_patterns = [
            (r'rm\s+-rf', 'Dangerous file deletion command'),
            (r'format\s+c:', 'Disk formatting command'),
            (r'del\s+/\w+', 'File deletion command'),
            (r'sudo\s+', 'Privilege escalation'),
            (r'chmod\s+777', 'Dangerous permission change'),
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(f"Suspicious pattern detected: {description}")
        
        return len(issues) == 0, issues

class ASTSecurityScanner(ast.NodeVisitor):
    """Layer 2: Abstract Syntax Tree (AST) Analysis"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.security_violations = []
        self.dangerous_functions = {
            'eval', 'exec', 'compile', '__import__',
            'open', 'file', 'input', 'raw_input'
        }
        self.dangerous_modules = {
            'os', 'sys', 'subprocess', 'shutil',
            'socket', 'urllib', 'requests', 'http'
        }
        self.allowed_imports = self.config_manager.get('plugins.allowed_imports', [
            'click', 'pathlib', 'typing', 'dataclasses', 'json', 'yaml',
            'datetime', 'time', 'math', 'random', 'string', 'collections'
        ])
    
    def scan_code(self, code: str) -> Tuple[bool, List[str]]:
        """Scan code for security violations"""
        self.security_violations = []
        
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return len(self.security_violations) == 0, self.security_violations
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
    
    def visit_Call(self, node):
        """Check function calls for dangerous operations"""
        if isinstance(node.func, ast.Name):
            if node.func.id in self.dangerous_functions:
                self.security_violations.append(
                    f"Dangerous function call: {node.func.id}"
                )
        
        elif isinstance(node.func, ast.Attribute):
            if hasattr(node.func.value, 'id'):
                module_name = node.func.value.id
                if module_name in self.dangerous_modules:
                    self.security_violations.append(
                        f"Dangerous module usage: {module_name}.{node.func.attr}"
                    )
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Check imports for dangerous modules"""
        for alias in node.names:
            if alias.name in self.dangerous_modules:
                self.security_violations.append(
                    f"Dangerous import: {alias.name}"
                )
            elif alias.name not in self.allowed_imports:
                self.security_violations.append(
                    f"Import not in allowed list: {alias.name}"
                )
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Check from imports for dangerous modules"""
        if node.module in self.dangerous_modules:
            self.security_violations.append(
                f"Dangerous from import: {node.module}"
            )
        elif node.module and node.module not in self.allowed_imports:
            self.security_violations.append(
                f"From import not in allowed list: {node.module}"
            )
        self.generic_visit(node)

class LLMSecurityValidator:
    """Layer 3: LLM-based Security Analysis"""
    
    def __init__(self, llm_integration):
        self.llm_integration = llm_integration
    
    def validate_with_llm(self, code: str) -> Tuple[bool, List[str]]:
        """Use LLM to validate code for security issues"""
        
        system_prompt = """You are a code security validator. Analyze the provided Python code and respond with only 'SAFE' or 'UNSAFE'.

Check for:
1. Dangerous imports or operations (eval, exec, os.system, etc.)
2. File system operations outside allowed directories
3. Network operations without proper validation
4. Infinite loops or resource exhaustion
5. Code injection vulnerabilities

Respond with only 'SAFE' if the code is acceptable, or 'UNSAFE' if it poses any security risks."""
        
        try:
            response = self.llm_integration.query(code, system_prompt)
            
            if not response:
                return False, ["LLM validation failed - no response"]
            
            response = response.strip().upper()
            
            if response == 'SAFE':
                return True, []
            elif response == 'UNSAFE':
                return False, ["LLM identified security risks in code"]
            else:
                # If response is not clear, ask for details
                detail_prompt = f"The code was flagged as potentially unsafe. Please explain the specific security issues:\n\n{code}"
                detail_response = self.llm_integration.query(detail_prompt, system_prompt)
                
                return False, [f"LLM security concern: {detail_response or 'Unknown security issue'}"]
                
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return False, [f"LLM validation failed: {str(e)}"]

class ComplexityAnalyzer:
    """Layer 4: Code Complexity and Resource Analysis"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.max_complexity = config_manager.get('validation.max_complexity', 10)
        self.max_lines = config_manager.get('validation.max_lines', 100)
        self.max_functions = config_manager.get('validation.max_functions', 5)
    
    def analyze_complexity(self, code: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Analyze code complexity and resource requirements"""
        
        issues = []
        warnings = []
        metrics = {}
        
        try:
            tree = ast.parse(code)
            
            # Count various code elements
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            loops = [node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))]
            conditionals = [node for node in ast.walk(tree) if isinstance(node, ast.If)]
            
            lines = len([line for line in code.split('\n') if line.strip()])
            
            metrics = {
                'lines': lines,
                'functions': len(functions),
                'classes': len(classes),
                'loops': len(loops),
                'conditionals': len(conditionals),
                'complexity_score': len(loops) + len(conditionals) + len(functions)
            }
            
            # Check limits
            if lines > self.max_lines:
                issues.append(f"Code too long: {lines} lines (max {self.max_lines})")
            
            if len(functions) > self.max_functions:
                issues.append(f"Too many functions: {len(functions)} (max {self.max_functions})")
            
            if metrics['complexity_score'] > self.max_complexity:
                issues.append(f"Code too complex: score {metrics['complexity_score']} (max {self.max_complexity})")
            
            # Check for potential infinite loops
            for loop in loops:
                if isinstance(loop, ast.While):
                    # Simple heuristic: while True without break
                    if (isinstance(loop.test, ast.Constant) and loop.test.value is True):
                        has_break = any(isinstance(node, ast.Break) for node in ast.walk(loop))
                        if not has_break:
                            warnings.append("Potential infinite loop detected")
            
            return len(issues) == 0, issues + warnings, metrics
            
        except SyntaxError as e:
            return False, [f"Syntax error in complexity analysis: {e}"], {}
        except Exception as e:
            logger.error(f"Complexity analysis error: {e}")
            return False, [f"Complexity analysis failed: {str(e)}"], {}

class EnhancedValidator:
    """Enhanced 5-Layer Validation System"""
    
    def __init__(self, config_manager, llm_integration):
        self.config_manager = config_manager
        self.llm_integration = llm_integration
        
        # Initialize validation layers
        self.input_sanitizer = InputSanitizer()
        self.ast_scanner = ASTSecurityScanner(config_manager)
        self.llm_validator = LLMSecurityValidator(llm_integration)
        self.complexity_analyzer = ComplexityAnalyzer(config_manager)
        self.docker_sandbox = DockerSandbox(config_manager)
        
        logger.info("Enhanced 5-layer validation system initialized")
    
    def validate_code_comprehensive(self, code: str, user_input: str = "") -> ValidationResult:
        """Run comprehensive 5-layer validation"""
        
        issues = []
        warnings = []
        layer_results = {}
        security_score = 100.0
        
        logger.info("Starting comprehensive code validation")
        
        # Layer 1: Input Sanitization
        try:
            if user_input:
                sanitized_input = self.input_sanitizer.sanitize_user_input(user_input)
                if sanitized_input != user_input:
                    warnings.append("User input was sanitized")
            
            llm_response_valid, llm_issues = self.input_sanitizer.validate_llm_response(code)
            layer_results['input_sanitization'] = llm_response_valid
            
            if not llm_response_valid:
                issues.extend(llm_issues)
                security_score -= 30
                
        except Exception as e:
            logger.error(f"Layer 1 validation failed: {e}")
            layer_results['input_sanitization'] = False
            issues.append(f"Input sanitization failed: {str(e)}")
            security_score -= 20
        
        # Layer 2: AST Security Analysis
        try:
            ast_valid, ast_issues = self.ast_scanner.scan_code(code)
            layer_results['ast_analysis'] = ast_valid
            
            if not ast_valid:
                issues.extend(ast_issues)
                security_score -= 25
                
        except Exception as e:
            logger.error(f"Layer 2 validation failed: {e}")
            layer_results['ast_analysis'] = False
            issues.append(f"AST analysis failed: {str(e)}")
            security_score -= 20
        
        # Layer 3: LLM Security Validation
        try:
            llm_valid, llm_sec_issues = self.llm_validator.validate_with_llm(code)
            layer_results['llm_validation'] = llm_valid
            
            if not llm_valid:
                issues.extend(llm_sec_issues)
                security_score -= 20
                
        except Exception as e:
            logger.error(f"Layer 3 validation failed: {e}")
            layer_results['llm_validation'] = False
            issues.append(f"LLM validation failed: {str(e)}")
            security_score -= 15
        
        # Layer 4: Complexity Analysis
        try:
            complexity_valid, complexity_issues, metrics = self.complexity_analyzer.analyze_complexity(code)
            layer_results['complexity_analysis'] = complexity_valid
            
            if not complexity_valid:
                # Separate issues from warnings
                for issue in complexity_issues:
                    if "Potential" in issue or "Warning" in issue:
                        warnings.append(issue)
                    else:
                        issues.append(issue)
                        security_score -= 10
                        
        except Exception as e:
            logger.error(f"Layer 4 validation failed: {e}")
            layer_results['complexity_analysis'] = False
            issues.append(f"Complexity analysis failed: {str(e)}")
            security_score -= 10
        
        # Layer 5: Sandbox Execution
        execution_result = None
        try:
            if self.docker_sandbox.is_available():
                execution_result = self.docker_sandbox.execute_code_safely(code)
                sandbox_valid = execution_result.success
                layer_results['sandbox_execution'] = sandbox_valid
                
                if not sandbox_valid:
                    issues.append(f"Sandbox execution failed: {execution_result.error}")
                    security_score -= 15
                else:
                    # Check execution time and resource usage
                    if execution_result.execution_time > 10:  # 10 seconds
                        warnings.append(f"Long execution time: {execution_result.execution_time:.2f}s")
                        
            else:
                layer_results['sandbox_execution'] = None
                warnings.append("Docker sandbox not available - skipping execution validation")
                
        except Exception as e:
            logger.error(f"Layer 5 validation failed: {e}")
            layer_results['sandbox_execution'] = False
            issues.append(f"Sandbox validation failed: {str(e)}")
            security_score -= 10
        
        # Calculate final validation result
        critical_layers = ['input_sanitization', 'ast_analysis', 'llm_validation']
        critical_failures = sum(1 for layer in critical_layers if not layer_results.get(layer, False))
        
        # Code is valid if no critical failures and security score is acceptable
        is_valid = (critical_failures == 0 and 
                   security_score >= self.config_manager.get('validation.min_security_score', 70))
        
        if security_score < 70:
            issues.append(f"Security score too low: {security_score:.1f}/100")
        
        logger.info(f"Validation complete: valid={is_valid}, score={security_score:.1f}, issues={len(issues)}")
        
        return ValidationResult(
            is_valid=is_valid,
            security_score=security_score,
            issues=issues,
            warnings=warnings,
            layer_results=layer_results,
            execution_result=execution_result
        )
    
    def cleanup(self):
        """Cleanup validation resources"""
        try:
            self.docker_sandbox.cleanup()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}") 