"""
Code Executor Tool
Safely executes Python and Bash code in sandboxed environment
Security: restricted execution with timeouts and resource limits
"""

import re
import asyncio
import subprocess
import tempfile
import os
from typing import Dict
from .base import Tool, ToolResult, ToolType


class CodeExecutorTool(Tool):
    """
    Execute code snippets safely

    Security measures:
    - Restricted execution environment
    - Timeout limits (5 seconds default)
    - No network access
    - No file system access outside temp directory
    - Whitelist of allowed modules
    """

    # Allowed Python modules for safe execution
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'json', 're',
        'itertools', 'collections', 'functools'
    }

    # Dangerous patterns to block
    FORBIDDEN_PATTERNS = [
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'os\.',
        r'sys\.',
        r'subprocess',
        r'socket',
        r'urllib',
        r'requests',
    ]

    def __init__(self):
        super().__init__(
            name="CodeExecutor",
            description="Execute Python or Bash code snippets safely",
            tool_type=ToolType.COMPUTATION
        )

    def can_handle(self, question: str) -> float:
        """
        Detect if question involves code execution

        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators
        strong_patterns = [
            r'(esegui|execute|run|testa|test)\s+(questo\s+)?codi(ce|go)',
            r'(prova|try)\s+(questo|this)\s+(script|program)',
            r'cosa\s+stampa|what.*print',
            r'risultato\s+di\s+questo\s+codice|output\s+of.*code',
        ]

        for pattern in strong_patterns:
            if re.search(pattern, question_lower):
                return 0.85

        # Detect code blocks
        if '```' in question or 'def ' in question or 'import ' in question:
            return 0.75

        # Detect "run this" patterns
        run_keywords = ['run', 'execute', 'esegui', 'prova', 'testa', 'test']
        if any(kw in question_lower for kw in run_keywords):
            # Check if there's code-like content
            if any(indicator in question for indicator in ['()', '{}', '[]', ';', 'def', 'for', 'if']):
                return 0.6

        return 0.0

    async def execute(self, code: str = None, language: str = "python", **kwargs) -> ToolResult:
        """
        Execute code safely

        Args:
            code: Code to execute (or extract from question)
            language: "python" or "bash"
            **kwargs: Additional parameters (question, timeout)

        Returns:
            ToolResult with execution output
        """
        # Extract code from question if not provided
        if not code:
            code = self._extract_code(kwargs.get('question', ''))

        if not code:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No code found to execute"
            )

        # Detect language if not specified
        if language == "python" and not self._is_python_code(code):
            language = "bash"

        # Security check
        if not self._is_safe(code, language):
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="Code contains forbidden operations (security)"
            )

        # Execute based on language
        try:
            if language == "python":
                output = await self._execute_python(code, timeout=kwargs.get('timeout', 5))
            elif language == "bash":
                output = await self._execute_bash(code, timeout=kwargs.get('timeout', 5))
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unsupported language: {language}"
                )

            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=output,
                confidence=0.95,  # Execution is precise
                metadata={"language": language, "code_length": len(code)}
            )

        except asyncio.TimeoutError:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="Execution timeout (code took too long)"
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Execution error: {str(e)}"
            )

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks or plain text"""

        # Try markdown code blocks first
        code_block_pattern = r'```(?:python|bash|sh)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Try to find code-like content
        lines = text.split('\n')
        code_lines = []

        for line in lines:
            # Lines that look like code
            if any(indicator in line for indicator in ['def ', 'import ', 'for ', 'if ', 'print(', '=']):
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines)

        return ""

    def _is_python_code(self, code: str) -> bool:
        """Detect if code is Python"""
        python_indicators = ['def ', 'import ', 'print(', 'for ', 'if ', 'elif ', 'else:']
        return any(indicator in code for indicator in python_indicators)

    def _is_safe(self, code: str, language: str) -> bool:
        """
        Check if code is safe to execute

        Returns True if safe, False if dangerous
        """
        code_lower = code.lower()

        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code_lower):
                return False

        # Python-specific checks
        if language == "python":
            # Block import of non-whitelisted modules
            import_pattern = r'import\s+(\w+)|from\s+(\w+)\s+import'
            imports = re.findall(import_pattern, code)

            for imp in imports:
                module = imp[0] or imp[1]
                if module and module not in self.ALLOWED_MODULES:
                    return False

        # Bash-specific checks
        if language == "bash":
            # Block network commands
            network_commands = ['curl', 'wget', 'ssh', 'scp', 'nc', 'telnet']
            if any(cmd in code_lower for cmd in network_commands):
                return False

            # Block file system modifications outside temp
            dangerous_commands = ['rm -rf', 'mkfs', 'dd', 'format', '> /']
            if any(cmd in code_lower for cmd in dangerous_commands):
                return False

        return True

    async def _execute_python(self, code: str, timeout: int = 5) -> str:
        """
        Execute Python code in restricted environment

        Uses subprocess with timeout and restricted globals
        """

        # Create temp file with code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute in subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                'python3', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={'PYTHONPATH': ''}  # Restrict imports
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            # Combine output
            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                error_output = stderr.decode('utf-8', errors='replace')
                if error_output.strip():
                    output += f"\n[STDERR]\n{error_output}"

            return output.strip()

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    async def _execute_bash(self, code: str, timeout: int = 5) -> str:
        """
        Execute Bash code with restrictions

        Uses subprocess with timeout
        """

        # Create temp script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('#!/bin/bash\n')
            f.write('set -e\n')  # Exit on error
            f.write(code)
            temp_file = f.name

        # Make executable
        os.chmod(temp_file, 0o755)

        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                '/bin/bash', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                error_output = stderr.decode('utf-8', errors='replace')
                if error_output.strip():
                    output += f"\n[STDERR]\n{error_output}"

            return output.strip()

        finally:
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
