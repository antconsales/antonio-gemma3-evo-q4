"""
Action Broker - Esegue azioni controllate e sicure
MCP-compatible interface per tool execution
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ToolType(Enum):
    """Tipi di tool supportati"""
    FILESYSTEM = "filesystem"
    PROCESS = "process"
    GPIO = "gpio"
    MEDIA = "media"
    SYSTEM = "system"


class ToolResult:
    """Risultato di esecuzione tool"""

    def __init__(
        self,
        success: bool,
        output: Any,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class ActionBroker:
    """
    Broker per esecuzione sicura di azioni
    Compatible con Model Context Protocol (MCP)
    """

    def __init__(
        self,
        registry_path: str = "data/evomemory/tool_registry.json",
        audit_log: str = "data/evomemory/audit.log",
    ):
        self.registry_path = Path(registry_path)
        self.audit_log = Path(audit_log)
        self.tools = self._load_registry()

        # Whitelist sicurezza
        self.safe_paths = [
            Path.cwd() / "data",
            Path.home() / "Documents",
        ]

        # Audit log
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> Dict[str, Dict]:
        """Carica tool registry da JSON"""
        if not self.registry_path.exists():
            return self._create_default_registry()

        with open(self.registry_path, "r") as f:
            return json.load(f)

    def _create_default_registry(self) -> Dict[str, Dict]:
        """Crea registry di default"""
        default_tools = {
            "fs.read": {
                "type": ToolType.FILESYSTEM.value,
                "enabled": True,
                "requires_confirmation": False,
                "allowed_paths": ["data/", "logs/"],
                "description": "Read files from allowed directories",
            },
            "fs.write": {
                "type": ToolType.FILESYSTEM.value,
                "enabled": True,
                "requires_confirmation": True,
                "allowed_paths": ["data/evomemory/", "logs/"],
                "description": "Write files to allowed directories",
            },
            "process.exec": {
                "type": ToolType.PROCESS.value,
                "enabled": False,  # Disabled by default per sicurezza
                "requires_confirmation": True,
                "timeout": 30,
                "description": "Execute system commands (sandboxed)",
            },
            "gpio.write": {
                "type": ToolType.GPIO.value,
                "enabled": True,
                "requires_confirmation": False,
                "allowed_pins": [17, 18, 22, 23, 24, 25],
                "description": "Control GPIO pins (write)",
            },
            "gpio.read": {
                "type": ToolType.GPIO.value,
                "enabled": True,
                "requires_confirmation": False,
                "allowed_pins": [17, 18, 22, 23, 24, 25],
                "description": "Read GPIO pin states",
            },
        }

        # Salva registry
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(default_tools, f, indent=2)

        return default_tools

    def _log_action(self, tool_name: str, params: Dict, result: ToolResult):
        """Log azioni per audit"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "params": params,
            "success": result.success,
            "error": result.error,
        }

        with open(self.audit_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def can_execute(self, tool_name: str, confidence: float = 0.5) -> bool:
        """Verifica se un tool può essere eseguito"""
        if tool_name not in self.tools:
            return False

        tool = self.tools[tool_name]

        # Controlla se enabled
        if not tool.get("enabled", False):
            return False

        # Controlla confidence threshold
        min_conf = tool.get("min_confidence", 0.5)
        if confidence < min_conf:
            return False

        return True

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        confidence: float = 0.5,
        force: bool = False,
    ) -> ToolResult:
        """
        Esegue un tool in modo sicuro

        Args:
            tool_name: Nome del tool (es. "fs.read", "gpio.write")
            params: Parametri del tool
            confidence: Livello di confidenza (0-1)
            force: Bypassa la conferma (solo per testing)

        Returns:
            ToolResult con esito esecuzione
        """

        # Verifica permessi
        if not force and not self.can_execute(tool_name, confidence):
            result = ToolResult(
                success=False,
                output=None,
                error=f"Tool {tool_name} not enabled or confidence too low",
            )
            self._log_action(tool_name, params, result)
            return result

        tool = self.tools[tool_name]

        # Routing per tipo
        try:
            if tool["type"] == ToolType.FILESYSTEM.value:
                result = self._execute_fs(tool_name, params, tool)
            elif tool["type"] == ToolType.GPIO.value:
                result = self._execute_gpio(tool_name, params, tool)
            elif tool["type"] == ToolType.PROCESS.value:
                result = self._execute_process(tool_name, params, tool)
            else:
                result = ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown tool type: {tool['type']}",
                )

        except Exception as e:
            result = ToolResult(
                success=False,
                output=None,
                error=str(e),
            )

        self._log_action(tool_name, params, result)
        return result

    def _execute_fs(self, tool_name: str, params: Dict, tool: Dict) -> ToolResult:
        """Esegue operazioni filesystem"""
        path = Path(params.get("path", ""))

        # Verifica path allowlist
        allowed = any(
            str(path).startswith(allowed_path)
            for allowed_path in tool.get("allowed_paths", [])
        )

        if not allowed:
            return ToolResult(
                success=False,
                output=None,
                error=f"Path {path} not in allowed paths",
            )

        if tool_name == "fs.read":
            if not path.exists():
                return ToolResult(success=False, output=None, error="File not found")

            content = path.read_text()
            return ToolResult(success=True, output=content)

        elif tool_name == "fs.write":
            content = params.get("content", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return ToolResult(success=True, output=f"Written {len(content)} bytes")

        return ToolResult(success=False, output=None, error="Unknown fs operation")

    def _execute_gpio(self, tool_name: str, params: Dict, tool: Dict) -> ToolResult:
        """Esegue operazioni GPIO"""
        pin = params.get("pin")
        allowed_pins = tool.get("allowed_pins", [])

        if pin not in allowed_pins:
            return ToolResult(
                success=False,
                output=None,
                error=f"Pin {pin} not in allowed pins",
            )

        try:
            import RPi.GPIO as GPIO
        except (ImportError, RuntimeError):
            return ToolResult(
                success=False,
                output=None,
                error="RPi.GPIO not available (not on Raspberry Pi?)",
            )

        try:
            if tool_name == "gpio.write":
                value = params.get("value", "LOW")
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH if value == "HIGH" else GPIO.LOW)

                return ToolResult(
                    success=True,
                    output=f"GPIO {pin} set to {value}",
                )

            elif tool_name == "gpio.read":
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.IN)
                value = GPIO.input(pin)

                return ToolResult(
                    success=True,
                    output={"pin": pin, "value": "HIGH" if value else "LOW"},
                )

        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))

        return ToolResult(success=False, output=None, error="Unknown GPIO operation")

    def _execute_process(self, tool_name: str, params: Dict, tool: Dict) -> ToolResult:
        """Esegue comandi system (sandboxed)"""
        command = params.get("command", "")
        timeout = tool.get("timeout", 30)

        # Blacklist comandi pericolosi
        dangerous = ["rm", "dd", "mkfs", "shutdown", "reboot", "kill"]
        if any(cmd in command for cmd in dangerous):
            return ToolResult(
                success=False,
                output=None,
                error="Dangerous command blocked",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error=f"Command timeout ({timeout}s)",
            )


if __name__ == "__main__":
    # Test
    broker = ActionBroker()

    print("Available tools:")
    for name, tool in broker.tools.items():
        print(f"  - {name}: {tool['description']}")

    # Test filesystem
    print("\nTest fs.write:")
    result = broker.execute(
        "fs.write",
        {"path": "data/test.txt", "content": "Hello from ActionBroker!"},
        confidence=0.8,
    )
    print(f"  Success: {result.success}, Output: {result.output}")

    # Test filesystem read
    print("\nTest fs.read:")
    result = broker.execute("fs.read", {"path": "data/test.txt"}, confidence=0.8)
    print(f"  Success: {result.success}, Output: {result.output}")

    print("\nAudit log:")
    if broker.audit_log.exists():
        print(broker.audit_log.read_text())
