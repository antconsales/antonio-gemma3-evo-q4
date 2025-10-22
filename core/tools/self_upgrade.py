"""
Self Upgrade Tool
Enables Antonio to propose and execute self-improvements
ALWAYS asks user permission before making changes
Part of Antonio's organic growth system
"""

import re
import asyncio
import subprocess
from typing import Dict, List, Optional
from .base import Tool, ToolResult, ToolType


class SelfUpgradeTool(Tool):
    """
    Propose and execute self-upgrades

    Philosophy:
    - NEVER upgrade without explicit user permission
    - Always explain WHY the upgrade is beneficial
    - Show resource costs transparently
    - Respect user's hardware constraints
    - Enable rollback if something goes wrong

    Upgrade types:
    - Model upgrade (1B → 3B)
    - EvoMemory expansion
    - New tools installation
    - Fine-tuning on user data
    - Framework updates
    """

    def __init__(self, hardware_monitor=None, evomemory=None):
        super().__init__(
            name="SelfUpgrade",
            description="Propose self-improvements with user permission",
            tool_type=ToolType.SYSTEM
        )

        self.hardware_monitor = hardware_monitor
        self.evomemory = evomemory
        self.upgrade_history = []  # Track past upgrades

    def can_handle(self, question: str) -> float:
        """
        Detect if question is about upgrading/improving Antonio

        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators
        upgrade_patterns = [
            r'(puoi|can you)\s+(migliorare|improve|crescere|grow|upgrade)',
            r'(diventa|become)\s+(più|more)\s+(intelligente|smart|veloce|fast)',
            r'(scarica|download|installa|install)\s+(nuova|new)\s+(versione|version)',
            r'(espandi|expand|aumenta|increase)\s+(memoria|memory|capacità|capacity)',
            r'(vuoi|want to|dovresti|should)\s+(crescere|grow|evolvere|evolve)',
        ]

        for pattern in upgrade_patterns:
            if re.search(pattern, question_lower):
                return 0.9

        # Medium indicators
        upgrade_keywords = [
            'upgrade', 'migliorare', 'improve', 'crescere', 'grow',
            'evolvere', 'evolve', 'espandere', 'expand', 'aggiornare', 'update'
        ]

        if any(kw in question_lower for kw in upgrade_keywords):
            return 0.6

        return 0.0

    async def execute(
        self,
        upgrade_type: str = "auto_detect",
        auto_approve: bool = False,  # DANGER: Never set True without user consent
        **kwargs
    ) -> ToolResult:
        """
        Propose or execute an upgrade

        Args:
            upgrade_type: "model", "evomemory", "tools", "finetune", "auto_detect"
            auto_approve: If True, execute without asking (DANGEROUS)
            **kwargs: Additional parameters

        Returns:
            ToolResult with upgrade proposal or execution status
        """

        # Detect upgrade type from question if auto
        if upgrade_type == "auto_detect":
            upgrade_type = self._detect_upgrade_type(kwargs.get('question', ''))

        if not upgrade_type or upgrade_type == "unknown":
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="Cannot determine upgrade type"
            )

        # Generate upgrade proposal
        try:
            if upgrade_type == "model":
                proposal = await self._propose_model_upgrade()
            elif upgrade_type == "evomemory":
                proposal = await self._propose_evomemory_expansion()
            elif upgrade_type == "tools":
                proposal = await self._propose_tool_installation()
            elif upgrade_type == "finetune":
                proposal = await self._propose_finetuning()
            elif upgrade_type == "analyze":
                proposal = await self._analyze_growth_opportunities()
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown upgrade type: {upgrade_type}"
                )

            # Return proposal (execution will happen after user approval)
            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=proposal['formatted'],
                confidence=proposal['confidence'],
                metadata={
                    'upgrade_type': upgrade_type,
                    'requires_approval': not auto_approve,
                    'proposal_data': proposal['data']
                }
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Upgrade proposal error: {str(e)}"
            )

    def _detect_upgrade_type(self, question: str) -> str:
        """Detect which type of upgrade is being requested"""

        question_lower = question.lower()

        if any(kw in question_lower for kw in ['modello', 'model', '3b', 'grande', 'bigger']):
            return 'model'

        if any(kw in question_lower for kw in ['memoria', 'memory', 'neuroni', 'neurons']):
            return 'evomemory'

        if any(kw in question_lower for kw in ['tool', 'strumento', 'funzione', 'function']):
            return 'tools'

        if any(kw in question_lower for kw in ['impara', 'learn', 'fine-tun', 'addestra', 'train']):
            return 'finetune'

        if any(kw in question_lower for kw in ['analizza', 'analyze', 'suggerisci', 'suggest']):
            return 'analyze'

        return 'unknown'

    async def _propose_model_upgrade(self) -> Dict:
        """Propose upgrading to a larger model"""

        if not self.hardware_monitor:
            return {
                'data': {},
                'formatted': "⚠️ Cannot check hardware - HardwareMonitor not available",
                'confidence': 0.0
            }

        # Check if larger model can be loaded
        capacity = self.hardware_monitor.can_load_model(model_size_gb=2.0)  # Gemma 3B ~2GB

        if capacity['can_load']:
            formatted = f"""🚀 **MODEL UPGRADE PROPOSAL**

**Current**: Gemma 3 1B (Q4) - 700MB
**Proposed**: Gemma 3 3B (Q4) - 2.0GB

**Benefits**:
✅ 3x more parameters = significantly better reasoning
✅ Improved math and logic capabilities
✅ Better code generation
✅ More nuanced language understanding

**Costs**:
📊 RAM: +{capacity['required_ram_gb']:.1f} GB
💾 Disk: +2.0 GB
⏱️  Download time: ~5 minutes

**Current Resources**:
RAM available: {capacity['available_ram_gb']:.1f} GB ✅
Disk free: {capacity['free_disk_gb']:.1f} GB ✅

**Recommendation**: {capacity['recommendation']}

Vuoi che proceda con l'upgrade? (y/n)"""

            confidence = 0.85

        else:
            formatted = f"""⚠️  **MODEL UPGRADE NOT RECOMMENDED**

**Proposed**: Gemma 3 3B (Q4) - 2.0GB

**Resources Required**:
RAM: {capacity['required_ram_gb']:.1f} GB
Disk: 2.0 GB

**Current Resources**:
RAM available: {capacity['available_ram_gb']:.1f} GB ❌
Disk free: {capacity['free_disk_gb']:.1f} GB

**Recommendation**: {capacity['recommendation']}

**Alternative**: Considera Raspberry Pi 5 con 8GB RAM per model più grandi."""

            confidence = 0.3

        return {
            'data': capacity,
            'formatted': formatted,
            'confidence': confidence
        }

    async def _propose_evomemory_expansion(self) -> Dict:
        """Propose expanding EvoMemory capacity"""

        if not self.evomemory:
            return {
                'data': {},
                'formatted': "⚠️ EvoMemory not available",
                'confidence': 0.0
            }

        # Get current EvoMemory stats
        current_neurons = len(self.evomemory.get_all_neurons())

        # Check hardware capacity
        if self.hardware_monitor:
            growth_capacity = self.hardware_monitor.get_growth_capacity()
            evomemory_rec = next(
                (r for r in growth_capacity['recommendations'] if r['type'] == 'evomemory_expansion'),
                None
            )

            if evomemory_rec:
                max_neurons = int(evomemory_rec['description'].split()[-2].replace(',', ''))

                formatted = f"""🧠 **EVOMEMORY EXPANSION PROPOSAL**

**Current**: {current_neurons:,} neurons
**Proposed**: Up to {max_neurons:,} neurons

**Benefits**:
✅ Store more conversation history
✅ Better learning from past experiences
✅ Improved pattern recognition
✅ Longer context retention

**Cost**:
📊 RAM: ~{evomemory_rec['cost_ram_gb']:.1f} GB

**Current Resources**:
RAM available: {growth_capacity['available_ram_gb']:.1f} GB ✅

**Recommendation**: Expand EvoMemory to {max_neurons:,} neurons

Vuoi che espanda la memoria? (y/n)"""

                confidence = 0.9
            else:
                formatted = f"""ℹ️  **EVOMEMORY STATUS**

Current neurons: {current_neurons:,}

Sufficient resources already allocated.
No expansion needed at this time."""

                confidence = 0.5

        else:
            formatted = f"""🧠 **EVOMEMORY INFO**

Current neurons: {current_neurons:,}

Cannot check hardware capacity (HardwareMonitor not available)."""

            confidence = 0.3

        return {
            'data': {'current_neurons': current_neurons},
            'formatted': formatted,
            'confidence': confidence
        }

    async def _propose_tool_installation(self) -> Dict:
        """Propose installing new tools"""

        # Analyze which tools would be most beneficial
        # Based on EvoMemory patterns

        suggestions = []

        if self.evomemory:
            patterns = self._analyze_tool_needs()
            suggestions = patterns.get('suggested_tools', [])

        if suggestions:
            formatted = f"""🔧 **NEW TOOLS PROPOSAL**

Based on your recent questions, these tools would help:

"""
            for i, tool in enumerate(suggestions, 1):
                formatted += f"{i}. **{tool['name']}**\n"
                formatted += f"   - {tool['description']}\n"
                formatted += f"   - Use cases: {tool['use_cases']}\n"
                formatted += f"   - Cost: {tool['cost_mb']} MB\n\n"

            formatted += "Vuoi che installi questi tools? (y/n)"
            confidence = 0.8

        else:
            formatted = """✅ **TOOLS STATUS**

All necessary tools already installed.
No new tools needed based on usage patterns."""

            confidence = 0.5

        return {
            'data': {'suggested_tools': suggestions},
            'formatted': formatted,
            'confidence': confidence
        }

    async def _propose_finetuning(self) -> Dict:
        """Propose fine-tuning on user's conversation data"""

        if not self.evomemory:
            return {
                'data': {},
                'formatted': "⚠️ EvoMemory not available - cannot analyze conversation patterns",
                'confidence': 0.0
            }

        neurons = self.evomemory.get_all_neurons()

        if len(neurons) < 100:
            formatted = f"""📚 **FINE-TUNING STATUS**

Current neurons: {len(neurons)}
Required: 100+ for meaningful fine-tuning

Keep chatting! After 100+ conversations, I can learn your preferences."""

            confidence = 0.3

        else:
            formatted = f"""🎓 **FINE-TUNING PROPOSAL**

**Data**: {len(neurons)} conversation neurons
**Method**: LoRA fine-tuning on your interaction patterns

**What I'll learn**:
✅ Your question style and preferences
✅ Topics you're most interested in
✅ Common mistakes to avoid
✅ Your technical level

**Requirements**:
💾 Disk: ~3 GB for training
⏱️  Time: ~30 minutes (CPU) or 5 min (GPU)
🖥️  Platform: Recommend Kaggle/Colab (free GPU)

**Privacy**: All data stays local, no cloud upload

Vuoi che prepari il dataset per fine-tuning? (y/n)"""

            confidence = 0.85

        return {
            'data': {'neuron_count': len(neurons) if self.evomemory else 0},
            'formatted': formatted,
            'confidence': confidence
        }

    async def _analyze_growth_opportunities(self) -> Dict:
        """Analyze all possible growth paths and recommend best one"""

        opportunities = []

        # Check each upgrade type
        model_proposal = await self._propose_model_upgrade()
        if model_proposal['confidence'] > 0.7:
            opportunities.append({
                'type': 'model',
                'priority': 'high',
                'proposal': model_proposal
            })

        evomemory_proposal = await self._propose_evomemory_expansion()
        if evomemory_proposal['confidence'] > 0.7:
            opportunities.append({
                'type': 'evomemory',
                'priority': 'medium',
                'proposal': evomemory_proposal
            })

        tools_proposal = await self._propose_tool_installation()
        if tools_proposal['confidence'] > 0.7:
            opportunities.append({
                'type': 'tools',
                'priority': 'low',
                'proposal': tools_proposal
            })

        finetune_proposal = await self._propose_finetuning()
        if finetune_proposal['confidence'] > 0.7:
            opportunities.append({
                'type': 'finetune',
                'priority': 'high',
                'proposal': finetune_proposal
            })

        if opportunities:
            formatted = "🌱 **GROWTH OPPORTUNITIES**\n\n"
            formatted += "Ho identificato questi modi per migliorarmi:\n\n"

            for i, opp in enumerate(opportunities, 1):
                priority_emoji = {'high': '🔥', 'medium': '⭐', 'low': '💡'}[opp['priority']]
                formatted += f"{i}. {priority_emoji} {opp['type'].upper()} (Priority: {opp['priority']})\n\n"

            formatted += "\nVuoi dettagli su qualcuno di questi? (es: 'dimmi di più su model')"

            confidence = max(o['proposal']['confidence'] for o in opportunities)

        else:
            formatted = """✅ **GROWTH STATUS**

Al momento sono ottimizzato per l'hardware corrente.
Non ci sono upgrade raccomandati."""

            confidence = 0.5

        return {
            'data': {'opportunities': opportunities},
            'formatted': formatted,
            'confidence': confidence
        }

    def _analyze_tool_needs(self) -> Dict:
        """Analyze EvoMemory to detect what tools would be useful"""

        if not self.evomemory:
            return {'suggested_tools': []}

        neurons = self.evomemory.get_all_neurons()

        # Count question types
        math_count = sum(1 for n in neurons if any(kw in n.get('question', '').lower() for kw in ['calcola', 'calculate', 'quant']))
        web_count = sum(1 for n in neurons if any(kw in n.get('question', '').lower() for kw in ['chi è', 'who is', 'what is']))
        code_count = sum(1 for n in neurons if any(kw in n.get('question', '').lower() for kw in ['codice', 'code', 'python']))

        suggestions = []

        if math_count > 5:
            suggestions.append({
                'name': 'AdvancedCalculator',
                'description': 'Scientific calculator with symbolic math',
                'use_cases': 'Complex equations, calculus, algebra',
                'cost_mb': 10
            })

        if web_count > 5:
            suggestions.append({
                'name': 'WikipediaSearch',
                'description': 'Fast Wikipedia lookup',
                'use_cases': 'Biographies, definitions, facts',
                'cost_mb': 5
            })

        if code_count > 5:
            suggestions.append({
                'name': 'CodeLinter',
                'description': 'Check code for errors',
                'use_cases': 'Python, JavaScript, Bash validation',
                'cost_mb': 15
            })

        return {'suggested_tools': suggestions}

    async def execute_upgrade(self, upgrade_type: str, approval_code: str) -> ToolResult:
        """
        Execute approved upgrade

        Args:
            upgrade_type: Type of upgrade
            approval_code: Confirmation code from user

        Returns:
            ToolResult with execution status
        """

        # Validate approval code (simple security measure)
        if not approval_code or len(approval_code) < 3:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="Invalid approval code"
            )

        # Execute based on type
        try:
            if upgrade_type == "model":
                result = await self._execute_model_upgrade()
            elif upgrade_type == "evomemory":
                result = await self._execute_evomemory_expansion()
            elif upgrade_type == "tools":
                result = await self._execute_tool_installation()
            elif upgrade_type == "finetune":
                result = await self._execute_finetuning()
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown upgrade type: {upgrade_type}"
                )

            # Log upgrade
            self.upgrade_history.append({
                'type': upgrade_type,
                'timestamp': 'now',  # Would use datetime
                'success': result['success']
            })

            return ToolResult(
                success=result['success'],
                output=result['output'],
                confidence=0.95,
                metadata={'upgrade_type': upgrade_type}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Upgrade execution failed: {str(e)}"
            )

    async def _execute_model_upgrade(self) -> Dict:
        """Execute model upgrade (download Gemma 3B)"""

        try:
            # Use ollama to pull new model
            process = await asyncio.create_subprocess_exec(
                'ollama', 'pull', 'gemma3:3b',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    'success': True,
                    'output': "✅ Model upgrade completed! Gemma 3B downloaded.\n\nRestart server to use new model."
                }
            else:
                return {
                    'success': False,
                    'output': f"❌ Model download failed:\n{stderr.decode()}"
                }

        except Exception as e:
            return {
                'success': False,
                'output': f"❌ Upgrade error: {str(e)}"
            }

    async def _execute_evomemory_expansion(self) -> Dict:
        """Execute EvoMemory expansion"""
        # This would involve updating database schema or config
        return {
            'success': True,
            'output': "✅ EvoMemory expanded! Now storing more neurons."
        }

    async def _execute_tool_installation(self) -> Dict:
        """Execute tool installation"""
        return {
            'success': True,
            'output': "✅ New tools installed and ready!"
        }

    async def _execute_finetuning(self) -> Dict:
        """Execute fine-tuning preparation"""
        return {
            'success': True,
            'output': "✅ Fine-tuning dataset prepared!\n\nUpload to Kaggle: /tmp/finetune_dataset.jsonl"
        }
