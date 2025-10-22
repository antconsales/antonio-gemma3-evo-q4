"""
Platform Detector - OS and Hardware Detection
Enables Antonio to adapt behavior based on platform

Detects:
- OS (Linux, macOS, Windows)
- Device type (Raspberry Pi, generic server, desktop, etc.)
- Architecture (ARM, x86, etc.)
- Available features (GPIO, GPU, etc.)
"""

import os
import platform
import subprocess
from typing import Dict, Optional


class PlatformInfo:
    """Platform information container"""

    def __init__(self):
        self.os_name = None  # "linux", "darwin", "windows"
        self.os_version = None
        self.device_type = None  # "raspberry_pi", "mac", "pc", "server"
        self.architecture = None  # "arm", "x86_64", "aarch64"
        self.cpu_model = None
        self.total_ram_gb = 0.0
        self.features = set()  # "gpio", "gpu", "nvme", etc.

    def is_raspberry_pi(self) -> bool:
        return self.device_type == "raspberry_pi"

    def is_mac(self) -> bool:
        return self.os_name == "darwin"

    def is_linux(self) -> bool:
        return self.os_name == "linux"

    def is_windows(self) -> bool:
        return self.os_name == "windows"

    def has_gpio(self) -> bool:
        return "gpio" in self.features

    def has_gpu(self) -> bool:
        return "gpu" in self.features

    def to_dict(self) -> Dict:
        return {
            'os_name': self.os_name,
            'os_version': self.os_version,
            'device_type': self.device_type,
            'architecture': self.architecture,
            'cpu_model': self.cpu_model,
            'total_ram_gb': self.total_ram_gb,
            'features': list(self.features)
        }


class PlatformDetector:
    """
    Detect and cache platform information

    Usage:
    ```python
    detector = PlatformDetector()
    info = detector.detect()

    if info.is_raspberry_pi():
        # Use Pi-specific commands
    elif info.is_mac():
        # Use macOS commands (brew, etc.)
    ```
    """

    def __init__(self):
        self._cached_info: Optional[PlatformInfo] = None

    def detect(self, force_refresh: bool = False) -> PlatformInfo:
        """
        Detect platform information

        Args:
            force_refresh: Re-detect even if cached

        Returns:
            PlatformInfo object
        """

        # Return cached if available
        if self._cached_info and not force_refresh:
            return self._cached_info

        info = PlatformInfo()

        # Detect OS
        info.os_name = platform.system().lower()

        # Detect version
        info.os_version = platform.release()

        # Detect architecture
        info.architecture = platform.machine().lower()

        # Detect RAM
        try:
            import psutil
            info.total_ram_gb = psutil.virtual_memory().total / (1024**3)
        except:
            info.total_ram_gb = 0.0

        # Platform-specific detection
        if info.os_name == "linux":
            self._detect_linux_specifics(info)
        elif info.os_name == "darwin":
            self._detect_macos_specifics(info)
        elif info.os_name == "windows":
            self._detect_windows_specifics(info)

        # Cache result
        self._cached_info = info

        return info

    def _detect_linux_specifics(self, info: PlatformInfo):
        """Detect Linux-specific information"""

        # Check if Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

                if 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    info.device_type = "raspberry_pi"

                    # Detect Pi model
                    if 'Raspberry Pi 5' in cpuinfo:
                        info.cpu_model = "Raspberry Pi 5"
                    elif 'Raspberry Pi 4' in cpuinfo:
                        info.cpu_model = "Raspberry Pi 4"
                    elif 'Raspberry Pi 3' in cpuinfo:
                        info.cpu_model = "Raspberry Pi 3"
                    else:
                        info.cpu_model = "Raspberry Pi (unknown model)"

                    # Pi has GPIO
                    info.features.add("gpio")

                else:
                    # Generic Linux
                    info.device_type = "linux_pc"

                    # Extract CPU model
                    for line in cpuinfo.split('\n'):
                        if 'model name' in line.lower():
                            info.cpu_model = line.split(':')[1].strip()
                            break

        except FileNotFoundError:
            info.device_type = "linux_unknown"

        # Check for GPU (NVIDIA)
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                info.features.add("gpu")
                info.features.add("nvidia_gpu")
        except:
            pass

        # Check for GPIO library (confirms GPIO availability)
        try:
            import RPi.GPIO
            info.features.add("gpio")
        except ImportError:
            pass

    def _detect_macos_specifics(self, info: PlatformInfo):
        """Detect macOS-specific information"""

        info.device_type = "mac"

        # Detect Mac model
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                info.cpu_model = result.stdout.strip()

                # Detect Apple Silicon
                if 'Apple' in info.cpu_model or info.architecture == 'arm64':
                    info.features.add("apple_silicon")
                    info.features.add("gpu")  # Apple Silicon has integrated GPU

        except:
            pass

        # Check for AMD/NVIDIA GPU
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                if 'AMD' in result.stdout or 'NVIDIA' in result.stdout:
                    info.features.add("gpu")
                    if 'AMD' in result.stdout:
                        info.features.add("amd_gpu")
                    if 'NVIDIA' in result.stdout:
                        info.features.add("nvidia_gpu")
        except:
            pass

    def _detect_windows_specifics(self, info: PlatformInfo):
        """Detect Windows-specific information"""

        info.device_type = "windows_pc"

        # Detect CPU
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    info.cpu_model = lines[1].strip()
        except:
            pass

        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                info.features.add("gpu")
                info.features.add("nvidia_gpu")
        except:
            pass

    def get_package_manager(self) -> Optional[str]:
        """
        Get the appropriate package manager for this platform

        Returns:
            "apt", "brew", "choco", "yum", etc. or None
        """

        info = self.detect()

        if info.is_linux():
            # Check which package manager is available
            managers = [
                ('apt-get', 'apt'),
                ('yum', 'yum'),
                ('dnf', 'dnf'),
                ('pacman', 'pacman'),
                ('zypper', 'zypper'),
            ]

            for cmd, name in managers:
                try:
                    result = subprocess.run(
                        ['which', cmd],
                        capture_output=True,
                        timeout=1
                    )
                    if result.returncode == 0:
                        return name
                except:
                    pass

        elif info.is_mac():
            return 'brew'

        elif info.is_windows():
            # Check for chocolatey
            try:
                result = subprocess.run(
                    ['choco', '--version'],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return 'choco'
            except:
                pass

        return None

    def get_install_command(self, package: str) -> Optional[str]:
        """
        Get the appropriate install command for a package

        Args:
            package: Package name

        Returns:
            Full install command string or None
        """

        pkg_manager = self.get_package_manager()

        if not pkg_manager:
            return None

        commands = {
            'apt': f'sudo apt-get install -y {package}',
            'yum': f'sudo yum install -y {package}',
            'dnf': f'sudo dnf install -y {package}',
            'pacman': f'sudo pacman -S --noconfirm {package}',
            'brew': f'brew install {package}',
            'choco': f'choco install {package} -y',
        }

        return commands.get(pkg_manager)

    def get_service_command(self, service: str, action: str) -> Optional[str]:
        """
        Get platform-specific service management command

        Args:
            service: Service name
            action: "start", "stop", "restart", "status"

        Returns:
            Command string or None
        """

        info = self.detect()

        if info.is_linux():
            # Most modern Linux uses systemctl
            return f'sudo systemctl {action} {service}'

        elif info.is_mac():
            # macOS uses launchctl
            if action == "start":
                return f'sudo launchctl start {service}'
            elif action == "stop":
                return f'sudo launchctl stop {service}'
            elif action == "restart":
                return f'sudo launchctl restart {service}'
            elif action == "status":
                return f'sudo launchctl list | grep {service}'

        elif info.is_windows():
            # Windows uses sc or net
            if action == "start":
                return f'net start {service}'
            elif action == "stop":
                return f'net stop {service}'
            elif action == "restart":
                return f'net stop {service} && net start {service}'

        return None

    def format_info(self) -> str:
        """
        Get formatted platform information for display

        Returns:
            Formatted string
        """

        info = self.detect()

        formatted = f"""🖥️  **PLATFORM INFORMATION**

**OS**: {info.os_name.capitalize()} {info.os_version}
**Device**: {info.device_type.replace('_', ' ').title()}
**Architecture**: {info.architecture}
**CPU**: {info.cpu_model or 'Unknown'}
**RAM**: {info.total_ram_gb:.1f} GB

**Features**:"""

        if info.features:
            for feature in sorted(info.features):
                formatted += f"\n  ✅ {feature.replace('_', ' ').title()}"
        else:
            formatted += "\n  (No special features detected)"

        # Add package manager info
        pkg_manager = self.get_package_manager()
        if pkg_manager:
            formatted += f"\n\n**Package Manager**: {pkg_manager}"

        return formatted


# Global singleton instance
_detector = None


def get_platform_detector() -> PlatformDetector:
    """
    Get global PlatformDetector instance (singleton)

    Returns:
        PlatformDetector instance
    """

    global _detector

    if _detector is None:
        _detector = PlatformDetector()

    return _detector


def get_platform_info() -> PlatformInfo:
    """
    Quick access to platform info

    Returns:
        PlatformInfo object
    """

    detector = get_platform_detector()
    return detector.detect()


# Convenience functions
def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi"""
    return get_platform_info().is_raspberry_pi()


def is_mac() -> bool:
    """Check if running on macOS"""
    return get_platform_info().is_mac()


def is_linux() -> bool:
    """Check if running on Linux"""
    return get_platform_info().is_linux()


def is_windows() -> bool:
    """Check if running on Windows"""
    return get_platform_info().is_windows()
