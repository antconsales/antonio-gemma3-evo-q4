"""
GPIO Controller Tool
Control Raspberry Pi hardware (LEDs, sensors, motors)
Requires: RPi.GPIO library (installed on Raspberry Pi)
"""

import re
import asyncio
from typing import Dict, Optional
from .base import Tool, ToolResult, ToolType


class GPIOControllerTool(Tool):
    """
    Control Raspberry Pi GPIO pins

    Capabilities:
    - Turn LEDs on/off
    - Read sensor values
    - Control motors/servos
    - Read button states

    Safety:
    - Pin validation
    - State tracking
    - Safe cleanup
    """

    # Pin mapping for common uses
    DEFAULT_PINS = {
        'led_red': 17,
        'led_green': 27,
        'led_blue': 22,
        'button': 23,
        'sensor': 24
    }

    def __init__(self, enable_gpio: bool = True):
        super().__init__(
            name="GPIOController",
            description="Control Raspberry Pi hardware (LEDs, sensors)",
            tool_type=ToolType.SYSTEM
        )

        self.gpio_available = False
        self.pin_states = {}  # Track pin states

        # Try to import GPIO library
        if enable_gpio:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                self.GPIO.setmode(GPIO.BCM)
                self.GPIO.setwarnings(False)
                self.gpio_available = True
            except ImportError:
                print("⚠️  RPi.GPIO not available (not on Raspberry Pi?)")
                self.GPIO = None
            except Exception as e:
                print(f"⚠️  GPIO initialization failed: {e}")
                self.GPIO = None

    def can_handle(self, question: str) -> float:
        """
        Detect GPIO-related questions

        Returns confidence 0-1
        """
        if not self.gpio_available:
            return 0.0  # Cannot handle if GPIO not available

        question_lower = question.lower()

        # Strong indicators
        gpio_patterns = [
            r'(accendi|turn on|light up)\s+(il\s+)?(led|light)',
            r'(spegni|turn off)\s+(il\s+)?(led|light)',
            r'(leggi|read)\s+(il\s+)?(sensore|sensor|button)',
            r'(attiva|activate|controlla|control)\s+gpio',
            r'pin\s+\d+',
        ]

        for pattern in gpio_patterns:
            if re.search(pattern, question_lower):
                return 0.9

        # Medium indicators
        gpio_keywords = [
            'led', 'light', 'gpio', 'pin', 'sensor', 'button',
            'accendi', 'spegni', 'hardware', 'raspberry'
        ]

        keyword_count = sum(1 for kw in gpio_keywords if kw in question_lower)

        if keyword_count >= 2:
            return 0.7
        elif keyword_count == 1:
            return 0.4

        return 0.0

    async def execute(
        self,
        action: str = None,
        pin: int = None,
        value: Optional[bool] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute GPIO operation

        Args:
            action: "set", "get", "toggle", "cleanup"
            pin: GPIO pin number (BCM mode) or pin name
            value: True/False for set operations
            **kwargs: Additional parameters (question for parsing)

        Returns:
            ToolResult with operation status
        """

        if not self.gpio_available:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="GPIO not available (not on Raspberry Pi)"
            )

        # Parse action from question if not provided
        if not action or not pin:
            parsed = self._parse_gpio_command(kwargs.get('question', ''))
            action = action or parsed.get('action')
            pin = pin or parsed.get('pin')
            value = value if value is not None else parsed.get('value')

        if not action:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No GPIO action specified"
            )

        # Convert pin name to number
        if isinstance(pin, str):
            pin = self.DEFAULT_PINS.get(pin.lower())

        if not pin or not self._is_valid_pin(pin):
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Invalid GPIO pin: {pin}"
            )

        # Execute action
        try:
            if action == "set":
                result = await self._set_pin(pin, value)
            elif action == "get":
                result = await self._get_pin(pin)
            elif action == "toggle":
                result = await self._toggle_pin(pin)
            elif action == "cleanup":
                result = await self._cleanup()
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown action: {action}"
                )

            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=result,
                confidence=0.95,
                metadata={"pin": pin, "action": action}
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"GPIO error: {str(e)}"
            )

    def _parse_gpio_command(self, question: str) -> Dict:
        """
        Parse GPIO action from natural language

        Returns dict with action, pin, value
        """
        question_lower = question.lower()

        # Detect action
        action = None
        value = None

        if any(kw in question_lower for kw in ['accendi', 'turn on', 'light up', 'attiva', 'activate']):
            action = "set"
            value = True
        elif any(kw in question_lower for kw in ['spegni', 'turn off', 'disattiva', 'deactivate']):
            action = "set"
            value = False
        elif any(kw in question_lower for kw in ['toggle', 'switch', 'inverti']):
            action = "toggle"
        elif any(kw in question_lower for kw in ['leggi', 'read', 'controlla', 'check']):
            action = "get"

        # Detect pin
        pin = None

        # Try to find pin number
        pin_match = re.search(r'pin\s+(\d+)', question_lower)
        if pin_match:
            pin = int(pin_match.group(1))
        else:
            # Try to find named pins
            for pin_name, pin_num in self.DEFAULT_PINS.items():
                if pin_name.replace('_', ' ') in question_lower or pin_name in question_lower:
                    pin = pin_num
                    break

            # Try color names for LEDs
            if not pin:
                if 'rosso' in question_lower or 'red' in question_lower:
                    pin = self.DEFAULT_PINS.get('led_red')
                elif 'verde' in question_lower or 'green' in question_lower:
                    pin = self.DEFAULT_PINS.get('led_green')
                elif 'blu' in question_lower or 'blue' in question_lower:
                    pin = self.DEFAULT_PINS.get('led_blue')

        return {
            'action': action,
            'pin': pin,
            'value': value
        }

    def _is_valid_pin(self, pin: int) -> bool:
        """Check if pin number is valid for Raspberry Pi"""
        # Valid BCM GPIO pins on Raspberry Pi
        valid_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]
        return pin in valid_pins

    async def _set_pin(self, pin: int, value: bool) -> str:
        """Set GPIO pin to HIGH or LOW"""

        # Setup pin if not already setup
        if pin not in self.pin_states:
            self.GPIO.setup(pin, self.GPIO.OUT)

        # Set value
        self.GPIO.output(pin, self.GPIO.HIGH if value else self.GPIO.LOW)
        self.pin_states[pin] = value

        state_str = "ON (HIGH)" if value else "OFF (LOW)"
        return f"Pin {pin} set to {state_str}"

    async def _get_pin(self, pin: int) -> str:
        """Read GPIO pin value"""

        # Setup pin as input if not already setup
        if pin not in self.pin_states:
            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_DOWN)

        # Read value
        value = self.GPIO.input(pin)
        state_str = "HIGH" if value else "LOW"

        return f"Pin {pin} is {state_str}"

    async def _toggle_pin(self, pin: int) -> str:
        """Toggle GPIO pin state"""

        # Get current state
        current = self.pin_states.get(pin, False)

        # Toggle
        new_value = not current

        # Set
        return await self._set_pin(pin, new_value)

    async def _cleanup(self) -> str:
        """Clean up GPIO resources"""
        self.GPIO.cleanup()
        self.pin_states = {}
        return "GPIO cleanup completed"

    def __del__(self):
        """Cleanup on object destruction"""
        if self.gpio_available and self.GPIO:
            try:
                self.GPIO.cleanup()
            except:
                pass
