"""
Hardware Monitor Tool
Monitors Raspberry Pi hardware resources for adaptive growth decisions
Part of Antonio's self-aware resource management system
"""

import os
import re
import asyncio
import psutil
from typing import Dict, Optional
from .base import Tool, ToolResult, ToolType


class HardwareMonitorTool(Tool):
    """
    Monitor hardware resources and constraints

    Capabilities:
    - RAM usage and availability
    - Disk space
    - CPU load and cores
    - Temperature (Pi specific)
    - GPU memory (if available)

    Use cases:
    - Decide if can load larger model
    - Check if can expand EvoMemory
    - Detect thermal throttling
    - Adaptive performance mode
    """

    def __init__(self):
        super().__init__(
            name="HardwareMonitor",
            description="Monitor system resources for adaptive growth",
            tool_type=ToolType.SYSTEM
        )

        self.is_raspberry_pi = self._detect_raspberry_pi()

    def can_handle(self, question: str) -> float:
        """
        Detect hardware/resource related questions

        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators
        hardware_patterns = [
            r'(quanta|how much)\s+(ram|memoria|memory|disk|spazio)',
            r'(posso|can I)\s+(caricare|load|scaricare|download)',
            r'(risorse|resources)\s+(disponibili|available|libere|free)',
            r'(temperatura|temperature|cpu|load)',
            r'(ho abbastanza|enough)\s+(spazio|space|memoria|memory)',
        ]

        for pattern in hardware_patterns:
            if re.search(pattern, question_lower):
                return 0.9

        # Medium indicators
        resource_keywords = [
            'ram', 'memoria', 'memory', 'disk', 'cpu', 'gpu',
            'risorse', 'resources', 'spazio', 'space', 'performance'
        ]

        if any(kw in question_lower for kw in resource_keywords):
            return 0.6

        return 0.0

    async def execute(
        self,
        check_type: str = "all",
        **kwargs
    ) -> ToolResult:
        """
        Get hardware status

        Args:
            check_type: "all", "ram", "disk", "cpu", "temp", "summary"
            **kwargs: Additional parameters

        Returns:
            ToolResult with hardware info
        """

        try:
            if check_type == "ram":
                result = self._check_ram()
            elif check_type == "disk":
                result = self._check_disk()
            elif check_type == "cpu":
                result = self._check_cpu()
            elif check_type == "temp":
                result = self._check_temperature()
            elif check_type == "summary":
                result = self._get_summary()
            elif check_type == "all":
                result = self._get_detailed_report()
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown check type: {check_type}"
                )

            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=result['formatted'],
                confidence=0.99,  # Hardware stats are precise
                metadata=result['data']
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Hardware monitoring error: {str(e)}"
            )

    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except:
            return False

    def _check_ram(self) -> Dict:
        """Check RAM usage"""
        mem = psutil.virtual_memory()

        data = {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'used_gb': mem.used / (1024**3),
            'percent_used': mem.percent,
            'free_gb': mem.free / (1024**3)
        }

        formatted = f"""💾 **RAM Status**
Total: {data['total_gb']:.2f} GB
Used: {data['used_gb']:.2f} GB ({data['percent_used']:.1f}%)
Available: {data['available_gb']:.2f} GB
Free: {data['free_gb']:.2f} GB"""

        return {'data': data, 'formatted': formatted}

    def _check_disk(self) -> Dict:
        """Check disk space"""
        disk = psutil.disk_usage('/')

        data = {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent_used': disk.percent
        }

        formatted = f"""💿 **Disk Status**
Total: {data['total_gb']:.2f} GB
Used: {data['used_gb']:.2f} GB ({data['percent_used']:.1f}%)
Free: {data['free_gb']:.2f} GB"""

        return {'data': data, 'formatted': formatted}

    def _check_cpu(self) -> Dict:
        """Check CPU usage and cores"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        data = {
            'percent_used': cpu_percent,
            'cores': cpu_count,
            'current_freq_mhz': cpu_freq.current if cpu_freq else 0,
            'max_freq_mhz': cpu_freq.max if cpu_freq else 0,
        }

        formatted = f"""🔧 **CPU Status**
Cores: {data['cores']}
Usage: {data['percent_used']:.1f}%
Frequency: {data['current_freq_mhz']:.0f} MHz"""

        if cpu_freq and cpu_freq.max:
            formatted += f" / {data['max_freq_mhz']:.0f} MHz max"

        return {'data': data, 'formatted': formatted}

    def _check_temperature(self) -> Dict:
        """Check system temperature (Pi specific)"""

        if not self.is_raspberry_pi:
            return {
                'data': {'temp_celsius': None},
                'formatted': "🌡️  Temperature monitoring not available (not on Pi)"
            }

        try:
            # Read Pi temperature
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = int(f.read().strip())
                temp_celsius = temp_raw / 1000.0

            data = {
                'temp_celsius': temp_celsius,
                'temp_fahrenheit': (temp_celsius * 9/5) + 32,
                'status': self._get_temp_status(temp_celsius)
            }

            status_emoji = {
                'cool': '❄️',
                'normal': '🟢',
                'warm': '🟡',
                'hot': '🔥'
            }.get(data['status'], '🌡️')

            formatted = f"""{status_emoji} **Temperature**
Current: {data['temp_celsius']:.1f}°C ({data['temp_fahrenheit']:.1f}°F)
Status: {data['status'].upper()}"""

            return {'data': data, 'formatted': formatted}

        except Exception as e:
            return {
                'data': {'temp_celsius': None, 'error': str(e)},
                'formatted': f"🌡️  Temperature read failed: {str(e)}"
            }

    def _get_temp_status(self, temp_celsius: float) -> str:
        """Categorize temperature"""
        if temp_celsius < 50:
            return 'cool'
        elif temp_celsius < 65:
            return 'normal'
        elif temp_celsius < 75:
            return 'warm'
        else:
            return 'hot'

    def _get_summary(self) -> Dict:
        """Get quick summary of all resources"""

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.5)

        data = {
            'ram_available_gb': mem.available / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            'cpu_percent': cpu_percent,
            'overall_status': 'healthy'  # Simplified
        }

        # Determine status
        if mem.percent > 90 or disk.percent > 90 or cpu_percent > 90:
            data['overall_status'] = 'critical'
        elif mem.percent > 75 or disk.percent > 75 or cpu_percent > 75:
            data['overall_status'] = 'warning'

        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🚨'
        }.get(data['overall_status'], '❓')

        formatted = f"""{status_emoji} **Quick Summary**
RAM: {data['ram_available_gb']:.1f} GB available
Disk: {data['disk_free_gb']:.1f} GB free
CPU: {data['cpu_percent']:.0f}% load
Status: {data['overall_status'].upper()}"""

        return {'data': data, 'formatted': formatted}

    def _get_detailed_report(self) -> Dict:
        """Get complete hardware report"""

        ram_info = self._check_ram()
        disk_info = self._check_disk()
        cpu_info = self._check_cpu()
        temp_info = self._check_temperature()

        # Combine all data
        data = {
            'ram': ram_info['data'],
            'disk': disk_info['data'],
            'cpu': cpu_info['data'],
            'temperature': temp_info['data'],
            'is_raspberry_pi': self.is_raspberry_pi
        }

        formatted = f"""🖥️  **HARDWARE REPORT**

{ram_info['formatted']}

{disk_info['formatted']}

{cpu_info['formatted']}

{temp_info['formatted']}

Platform: {'Raspberry Pi' if self.is_raspberry_pi else 'Generic Linux'}"""

        return {'data': data, 'formatted': formatted}

    def can_load_model(self, model_size_gb: float) -> Dict:
        """
        Check if there's enough resources to load a model

        Args:
            model_size_gb: Size of model in GB

        Returns:
            Dict with recommendation
        """

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Need at least model_size + 500MB for loading overhead
        required_ram_gb = model_size_gb + 0.5
        available_ram_gb = mem.available / (1024**3)
        free_disk_gb = disk.free / (1024**3)

        can_load = (
            available_ram_gb >= required_ram_gb and
            free_disk_gb >= model_size_gb
        )

        return {
            'can_load': can_load,
            'model_size_gb': model_size_gb,
            'required_ram_gb': required_ram_gb,
            'available_ram_gb': available_ram_gb,
            'free_disk_gb': free_disk_gb,
            'recommendation': self._get_load_recommendation(
                can_load, available_ram_gb, required_ram_gb
            )
        }

    def _get_load_recommendation(
        self,
        can_load: bool,
        available_ram_gb: float,
        required_ram_gb: float
    ) -> str:
        """Generate recommendation for model loading"""

        if can_load:
            return f"✅ Sufficient resources. Proceed with loading."
        else:
            shortage = required_ram_gb - available_ram_gb
            return f"❌ Insufficient RAM. Need {shortage:.1f} GB more."

    def get_growth_capacity(self) -> Dict:
        """
        Analyze capacity for Antonio to grow/evolve

        Returns recommendations for:
        - Expanding EvoMemory
        - Loading larger model
        - Adding new tools
        - Fine-tuning
        """

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        available_ram_gb = mem.available / (1024**3)
        free_disk_gb = disk.free / (1024**3)

        recommendations = []

        # EvoMemory expansion
        if available_ram_gb > 0.5:
            max_neurons = int(available_ram_gb * 10000)  # ~100KB per neuron
            recommendations.append({
                'type': 'evomemory_expansion',
                'description': f'Expand EvoMemory up to {max_neurons:,} neurons',
                'cost_ram_gb': 0.5,
                'benefit': 'Better long-term memory and learning'
            })

        # Model upgrade
        if available_ram_gb > 2.0 and free_disk_gb > 3.0:
            recommendations.append({
                'type': 'model_upgrade',
                'description': 'Upgrade to Gemma 3B for better reasoning',
                'cost_ram_gb': 2.5,
                'cost_disk_gb': 2.0,
                'benefit': 'Significantly improved accuracy'
            })

        # Fine-tuning cache
        if free_disk_gb > 5.0:
            recommendations.append({
                'type': 'finetune_prep',
                'description': 'Prepare for local fine-tuning',
                'cost_disk_gb': 3.0,
                'benefit': 'Custom learning from user interactions'
            })

        return {
            'available_ram_gb': available_ram_gb,
            'free_disk_gb': free_disk_gb,
            'recommendations': recommendations,
            'can_grow': len(recommendations) > 0
        }
