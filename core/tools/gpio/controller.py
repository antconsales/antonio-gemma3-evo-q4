"""
GPIO Controller - Controllo GPIO Raspberry Pi
Supporta LED, sensori, PWM, servo, etc.
"""

import time
from typing import Optional, Dict, List
from enum import Enum


class PinMode(Enum):
    """Modalità pin"""
    INPUT = "input"
    OUTPUT = "output"
    PWM = "pwm"


class PullMode(Enum):
    """Pull resistor mode"""
    UP = "up"
    DOWN = "down"
    NONE = "none"


class GPIOController:
    """Controller GPIO con supporto PWM"""

    def __init__(self, mode: str = "BCM"):
        """
        Args:
            mode: "BCM" (GPIO numbering) o "BOARD" (physical pin numbering)
        """
        self.mode = mode
        self.gpio_available = False
        self.pwm_instances = {}

        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            self.GPIO.setmode(getattr(GPIO, mode))
            self.GPIO.setwarnings(False)
            self.gpio_available = True
        except (ImportError, RuntimeError) as e:
            print(f"⚠️  GPIO not available: {e}")
            self.gpio_available = False

    def setup_pin(
        self,
        pin: int,
        mode: PinMode,
        pull_mode: PullMode = PullMode.NONE,
        initial: Optional[bool] = None,
    ):
        """Setup pin mode"""
        if not self.gpio_available:
            raise RuntimeError("GPIO not available")

        if mode == PinMode.OUTPUT:
            self.GPIO.setup(
                pin,
                self.GPIO.OUT,
                initial=self.GPIO.HIGH if initial else self.GPIO.LOW,
            )
        elif mode == PinMode.INPUT:
            pull = {
                PullMode.UP: self.GPIO.PUD_UP,
                PullMode.DOWN: self.GPIO.PUD_DOWN,
                PullMode.NONE: self.GPIO.PUD_OFF,
            }[pull_mode]

            self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=pull)

    def write(self, pin: int, value: bool):
        """Scrivi valore su pin (HIGH/LOW)"""
        if not self.gpio_available:
            print(f"[MOCK] GPIO {pin} -> {'HIGH' if value else 'LOW'}")
            return

        self.GPIO.output(pin, self.GPIO.HIGH if value else self.GPIO.LOW)

    def read(self, pin: int) -> bool:
        """Leggi valore da pin"""
        if not self.gpio_available:
            return False

        return bool(self.GPIO.input(pin))

    def toggle(self, pin: int):
        """Inverte stato del pin"""
        current = self.read(pin)
        self.write(pin, not current)

    def pwm_start(self, pin: int, frequency: float, duty_cycle: float):
        """
        Avvia PWM su pin

        Args:
            pin: Numero pin
            frequency: Frequenza in Hz (es. 1000 per LED, 50 per servo)
            duty_cycle: Duty cycle 0-100%
        """
        if not self.gpio_available:
            print(f"[MOCK] PWM start on {pin}: {frequency}Hz @ {duty_cycle}%")
            return

        if pin in self.pwm_instances:
            self.pwm_instances[pin].stop()

        pwm = self.GPIO.PWM(pin, frequency)
        pwm.start(duty_cycle)
        self.pwm_instances[pin] = pwm

    def pwm_set_duty_cycle(self, pin: int, duty_cycle: float):
        """Cambia duty cycle PWM"""
        if pin not in self.pwm_instances:
            raise ValueError(f"PWM not started on pin {pin}")

        self.pwm_instances[pin].ChangeDutyCycle(duty_cycle)

    def pwm_stop(self, pin: int):
        """Ferma PWM"""
        if pin in self.pwm_instances:
            self.pwm_instances[pin].stop()
            del self.pwm_instances[pin]

    def cleanup(self):
        """Cleanup GPIO (chiama a fine programma)"""
        if self.gpio_available:
            for pwm in self.pwm_instances.values():
                pwm.stop()
            self.GPIO.cleanup()

    # ======== HIGH-LEVEL HELPERS ========

    def led_on(self, pin: int):
        """Accendi LED"""
        self.setup_pin(pin, PinMode.OUTPUT)
        self.write(pin, True)

    def led_off(self, pin: int):
        """Spegni LED"""
        self.setup_pin(pin, PinMode.OUTPUT)
        self.write(pin, False)

    def led_blink(self, pin: int, times: int = 3, interval: float = 0.5):
        """Blink LED N volte"""
        self.setup_pin(pin, PinMode.OUTPUT)
        for _ in range(times):
            self.write(pin, True)
            time.sleep(interval)
            self.write(pin, False)
            time.sleep(interval)

    def led_fade(self, pin: int, duration: float = 2.0):
        """Fade LED (in e out)"""
        self.setup_pin(pin, PinMode.OUTPUT)
        self.pwm_start(pin, 1000, 0)

        steps = 100
        delay = duration / (2 * steps)

        # Fade in
        for i in range(steps):
            self.pwm_set_duty_cycle(pin, i)
            time.sleep(delay)

        # Fade out
        for i in range(steps, -1, -1):
            self.pwm_set_duty_cycle(pin, i)
            time.sleep(delay)

        self.pwm_stop(pin)

    def read_button(self, pin: int, pull_mode: PullMode = PullMode.UP) -> bool:
        """Leggi stato button (con debounce)"""
        self.setup_pin(pin, PinMode.INPUT, pull_mode=pull_mode)

        # Debounce
        reading1 = self.read(pin)
        time.sleep(0.01)
        reading2 = self.read(pin)

        return reading1 and reading2

    def servo_set_angle(self, pin: int, angle: float):
        """
        Muovi servo ad angolo (0-180°)

        Args:
            pin: Pin PWM
            angle: Angolo 0-180°
        """
        # Servo standard: 50Hz, duty cycle 2.5-12.5% per 0-180°
        duty_cycle = 2.5 + (angle / 180.0) * 10.0

        if pin not in self.pwm_instances:
            self.setup_pin(pin, PinMode.OUTPUT)
            self.pwm_start(pin, 50, duty_cycle)
        else:
            self.pwm_set_duty_cycle(pin, duty_cycle)


if __name__ == "__main__":
    # Test (safe anche senza GPIO hardware)
    gpio = GPIOController(mode="BCM")

    if gpio.gpio_available:
        print("✓ GPIO available")

        # Test LED
        LED_PIN = 17
        print(f"\nTest LED on pin {LED_PIN}...")
        gpio.led_blink(LED_PIN, times=3, interval=0.3)

        # Test PWM fade
        print("\nTest LED fade...")
        gpio.led_fade(LED_PIN, duration=2.0)

        gpio.cleanup()
    else:
        print("⚠️  GPIO not available (running in mock mode)")

        # Mock test
        gpio.led_on(17)
        gpio.led_off(17)
        gpio.pwm_start(18, 1000, 50)
        gpio.servo_set_angle(22, 90)
