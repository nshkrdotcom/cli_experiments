"""
Simplified CLI tests that don't require complex mocking
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from cli import cli


class TestCLIBasic:
    """Basic CLI tests without complex mocking"""

    def setup_method(self):
        """Setup for each test"""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Self-Evolving CLI Tool" in result.output
        assert "evolve" in result.output
        assert "status" in result.output

    def test_cli_no_args(self):
        """Test CLI with no arguments shows help"""
        result = self.runner.invoke(cli, [])
        
        # Click returns exit code 2 for missing required arguments, which is expected
        assert result.exit_code in [0, 2]  # 0 for help shown, 2 for missing args
        assert "Usage:" in result.output or "Commands:" in result.output

    def test_evolve_help(self):
        """Test evolve command help"""
        result = self.runner.invoke(cli, ['evolve', '--help'])
        
        assert result.exit_code == 0
        assert "Generate and integrate new functionality" in result.output
        assert "--execute" in result.output
        assert "--save" in result.output

    def test_status_help(self):
        """Test status command help"""
        result = self.runner.invoke(cli, ['status', '--help'])
        
        assert result.exit_code == 0
        assert "Show current tool status" in result.output

    def test_history_help(self):
        """Test history command help"""
        result = self.runner.invoke(cli, ['history', '--help'])
        
        assert result.exit_code == 0
        assert "Show command generation history" in result.output

    def test_rollback_help(self):
        """Test rollback command help"""
        result = self.runner.invoke(cli, ['rollback', '--help'])
        
        assert result.exit_code == 0
        assert "Rollback a command by ID" in result.output

    def test_install_plugin_help(self):
        """Test install-plugin command help"""
        result = self.runner.invoke(cli, ['install-plugin', '--help'])
        
        assert result.exit_code == 0
        assert "Install a new plugin" in result.output

    def test_list_plugins_help(self):
        """Test list-plugins command help"""
        result = self.runner.invoke(cli, ['list-plugins', '--help'])
        
        assert result.exit_code == 0
        assert "List all available and loaded plugins" in result.output

    def test_llm_query_help(self):
        """Test llm-query command help"""
        result = self.runner.invoke(cli, ['llm-query', '--help'])
        
        assert result.exit_code == 0
        assert "Direct LLM query" in result.output

    def test_invalid_command(self):
        """Test invalid command"""
        result = self.runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert "No such command" in result.output 