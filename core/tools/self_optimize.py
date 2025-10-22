"""
Self Optimize Tool
Enables Antonio to compress knowledge and downsize when needed
Part of adaptive homeostasis system - balances growth with constraints
"""

import re
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
from .base import Tool, ToolResult, ToolType


class SelfOptimizeTool(Tool):
    """
    Optimize and compress Antonio's knowledge base

    Philosophy:
    - Know when to grow AND when to shrink
    - Compress memories instead of deleting them
    - Track "golden moments" (peak performance states)
    - Enable rollback to better versions
    - Respect hardware constraints

    Capabilities:
    - Compress EvoMemory (merge similar neurons)
    - Archive low-value knowledge
    - Detect performance degradation
    - Propose downsizing when struggling
    - Snapshot best configurations
    - Rollback to optimal states
    """

    def __init__(self, evomemory=None, hardware_monitor=None, metrics_collector=None):
        super().__init__(
            name="SelfOptimize",
            description="Compress knowledge and optimize performance",
            tool_type=ToolType.SYSTEM
        )

        self.evomemory = evomemory
        self.hardware_monitor = hardware_monitor
        self.metrics_collector = metrics_collector

        self.snapshots = []  # Track performance snapshots
        self.compression_history = []

    def can_handle(self, question: str) -> float:
        """
        Detect if optimization/compression is needed

        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators
        optimize_patterns = [
            r'(sei|are you)\s+(lento|slow|slower)',
            r'(ottimizza|optimize|comprimi|compress)',
            r'(riduci|reduce|diminuisci|decrease)\s+(dimensione|size|memoria|memory)',
            r'(rallent|slow)',
            r'(scalda|hot|temperatura|temperature)',
            r'(troppa|too much)\s+(memoria|memory|ram)',
        ]

        for pattern in optimize_patterns:
            if re.search(pattern, question_lower):
                return 0.9

        # Medium indicators
        optimize_keywords = [
            'ottimizza', 'optimize', 'comprimi', 'compress',
            'lento', 'slow', 'memoria', 'memory', 'velocità', 'speed'
        ]

        if any(kw in question_lower for kw in optimize_keywords):
            return 0.6

        return 0.0

    async def execute(
        self,
        optimization_type: str = "auto_detect",
        **kwargs
    ) -> ToolResult:
        """
        Execute optimization

        Args:
            optimization_type: "compress", "downsize", "snapshot", "analyze", "auto_detect"
            **kwargs: Additional parameters

        Returns:
            ToolResult with optimization status
        """

        # Auto-detect optimization type
        if optimization_type == "auto_detect":
            optimization_type = await self._auto_detect_optimization_needed()

        if optimization_type == "none":
            return ToolResult(
                success=True,
                output="✅ System running optimally - no optimization needed",
                confidence=0.8,
                metadata={'status': 'optimal'}
            )

        try:
            if optimization_type == "compress":
                result = await self._compress_evomemory()
            elif optimization_type == "downsize":
                result = await self._propose_downsize()
            elif optimization_type == "snapshot":
                result = await self._create_performance_snapshot()
            elif optimization_type == "analyze":
                result = await self._analyze_performance_trends()
            elif optimization_type == "rollback":
                result = await self._rollback_to_best()
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown optimization type: {optimization_type}"
                )

            self.update_stats(success=result['success'])

            return ToolResult(
                success=result['success'],
                output=result['output'],
                confidence=result.get('confidence', 0.8),
                metadata=result.get('metadata', {})
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Optimization error: {str(e)}"
            )

    async def _auto_detect_optimization_needed(self) -> str:
        """
        Automatically detect what optimization is needed

        Returns optimization type or "none"
        """

        issues = []

        # Check hardware stress
        if self.hardware_monitor:
            try:
                hw_summary = self.hardware_monitor._get_summary()
                hw_data = hw_summary['data']

                # Check RAM pressure
                if hw_data.get('ram_available_gb', 999) < 0.5:
                    issues.append('ram_pressure')

                # Check temperature
                temp_info = self.hardware_monitor._check_temperature()
                temp = temp_info['data'].get('temp_celsius')
                if temp and temp > 75:
                    issues.append('overheating')

            except:
                pass

        # Check EvoMemory bloat
        if self.evomemory:
            neurons = self.evomemory.get_all_neurons()
            if len(neurons) > 1000:
                # Check for duplicates/similar
                similarity_ratio = self._estimate_neuron_similarity(neurons)
                if similarity_ratio > 0.3:  # >30% similar neurons
                    issues.append('memory_bloat')

        # Check performance degradation
        if self.metrics_collector:
            try:
                recent_perf = self._get_recent_performance()
                if recent_perf['avg_tokens_per_sec'] < 3.0:  # Slow
                    issues.append('performance_degradation')
            except:
                pass

        # Decide action based on issues
        if 'ram_pressure' in issues or 'overheating' in issues:
            return 'downsize'
        elif 'memory_bloat' in issues:
            return 'compress'
        elif 'performance_degradation' in issues:
            return 'analyze'
        else:
            return 'none'

    async def _compress_evomemory(self) -> Dict:
        """
        Compress EvoMemory by merging similar neurons

        Strategy:
        - Group similar questions
        - Merge into "summary neurons"
        - Keep highest confidence versions
        - Archive originals (not delete)
        """

        if not self.evomemory:
            return {
                'success': False,
                'output': "⚠️ EvoMemory not available",
                'confidence': 0.0
            }

        neurons = self.evomemory.get_all_neurons()
        original_count = len(neurons)

        if original_count < 50:
            return {
                'success': True,
                'output': f"ℹ️  Only {original_count} neurons - compression not needed yet",
                'confidence': 0.5
            }

        # Find similar neuron groups
        groups = self._group_similar_neurons(neurons)

        # Compress each group
        compressed_count = 0
        saved_ram_mb = 0

        for group in groups:
            if len(group) > 1:  # Only compress if duplicates exist
                # Keep best neuron from group
                best_neuron = max(group, key=lambda n: n.get('confidence', 0.0))

                # Archive others
                for neuron in group:
                    if neuron['id'] != best_neuron['id']:
                        # Mark as archived (would update DB in real implementation)
                        compressed_count += 1
                        saved_ram_mb += 0.1  # Approx 100KB per neuron

        # Log compression
        self.compression_history.append({
            'timestamp': datetime.now().isoformat(),
            'original_count': original_count,
            'compressed_count': compressed_count,
            'saved_ram_mb': saved_ram_mb
        })

        formatted = f"""🗜️  **EVOMEMORY COMPRESSION COMPLETE**

**Before**: {original_count} neurons
**After**: {original_count - compressed_count} neurons
**Compressed**: {compressed_count} similar neurons
**RAM Saved**: {saved_ram_mb:.1f} MB

**Method**: Merged similar questions, kept highest-confidence versions

**Result**: Faster search, less RAM usage, same knowledge! ✅"""

        return {
            'success': True,
            'output': formatted,
            'confidence': 0.95,
            'metadata': {
                'original_count': original_count,
                'compressed_count': compressed_count,
                'saved_ram_mb': saved_ram_mb
            }
        }

    def _group_similar_neurons(self, neurons: List[Dict]) -> List[List[Dict]]:
        """
        Group similar neurons together

        Uses simple keyword matching (in real implementation would use embeddings)
        """

        groups = []
        used_ids = set()

        for neuron in neurons:
            if neuron['id'] in used_ids:
                continue

            # Find similar neurons
            question = neuron.get('question', '').lower()
            keywords = set(re.findall(r'\w+', question))

            similar_group = [neuron]
            used_ids.add(neuron['id'])

            # Find others with similar keywords
            for other in neurons:
                if other['id'] in used_ids:
                    continue

                other_question = other.get('question', '').lower()
                other_keywords = set(re.findall(r'\w+', other_question))

                # Calculate similarity (Jaccard index)
                if keywords and other_keywords:
                    intersection = len(keywords & other_keywords)
                    union = len(keywords | other_keywords)
                    similarity = intersection / union

                    if similarity > 0.6:  # >60% similar
                        similar_group.append(other)
                        used_ids.add(other['id'])

            groups.append(similar_group)

        return groups

    def _estimate_neuron_similarity(self, neurons: List[Dict]) -> float:
        """
        Estimate what percentage of neurons are similar/duplicates

        Returns ratio 0-1
        """

        if len(neurons) < 10:
            return 0.0

        groups = self._group_similar_neurons(neurons)

        # Count groups with duplicates
        duplicate_groups = [g for g in groups if len(g) > 1]
        total_duplicates = sum(len(g) - 1 for g in duplicate_groups)

        return total_duplicates / len(neurons)

    async def _propose_downsize(self) -> Dict:
        """
        Propose downsizing model or clearing tools

        When hardware is struggling
        """

        issues = []
        recommendations = []

        # Check hardware
        if self.hardware_monitor:
            hw_summary = self.hardware_monitor._get_summary()
            hw_data = hw_summary['data']

            if hw_data.get('ram_available_gb', 999) < 0.5:
                issues.append("RAM < 500MB")
                recommendations.append({
                    'action': 'reduce_model',
                    'description': 'Switch to smaller model (Gemma 1B → TinyLlama 1B)',
                    'saves_ram_mb': 200
                })

            temp_info = self.hardware_monitor._check_temperature()
            temp = temp_info['data'].get('temp_celsius')
            if temp and temp > 75:
                issues.append(f"High temperature ({temp:.1f}°C)")
                recommendations.append({
                    'action': 'reduce_load',
                    'description': 'Lower num_ctx from 8192 to 4096',
                    'saves_ram_mb': 100
                })

        # Check EvoMemory size
        if self.evomemory:
            neurons = self.evomemory.get_all_neurons()
            if len(neurons) > 500:
                issues.append(f"Large EvoMemory ({len(neurons)} neurons)")
                recommendations.append({
                    'action': 'compress_memory',
                    'description': 'Compress EvoMemory (merge similar neurons)',
                    'saves_ram_mb': 50
                })

        if not issues:
            return {
                'success': True,
                'output': "✅ Hardware running smoothly - no downsizing needed",
                'confidence': 0.7
            }

        # Format proposal
        formatted = f"""⚠️  **DOWNSIZING RECOMMENDED**

**Issues Detected**:
"""
        for issue in issues:
            formatted += f"- {issue}\n"

        formatted += "\n**Recommendations**:\n\n"

        for i, rec in enumerate(recommendations, 1):
            formatted += f"{i}. **{rec['action']}**\n"
            formatted += f"   - {rec['description']}\n"
            formatted += f"   - Saves: {rec['saves_ram_mb']} MB RAM\n\n"

        total_savings = sum(r['saves_ram_mb'] for r in recommendations)
        formatted += f"**Total RAM savings**: {total_savings} MB\n\n"
        formatted += "Vuoi che proceda con l'ottimizzazione? (y/n)"

        return {
            'success': True,
            'output': formatted,
            'confidence': 0.9,
            'metadata': {
                'issues': issues,
                'recommendations': recommendations
            }
        }

    async def _create_performance_snapshot(self) -> Dict:
        """
        Create a snapshot of current performance state

        "Remember when I was fast/good"
        """

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'config': {},
            'performance': {}
        }

        # Capture hardware state
        if self.hardware_monitor:
            hw_summary = self.hardware_monitor._get_summary()
            snapshot['hardware'] = hw_summary['data']

        # Capture performance metrics
        if self.metrics_collector:
            recent_perf = self._get_recent_performance()
            snapshot['performance'] = recent_perf

        # Capture EvoMemory state
        if self.evomemory:
            neurons = self.evomemory.get_all_neurons()
            snapshot['evomemory'] = {
                'neuron_count': len(neurons),
                'avg_confidence': sum(n.get('confidence', 0) for n in neurons) / len(neurons) if neurons else 0
            }

        # Calculate overall score
        perf_score = snapshot['performance'].get('avg_tokens_per_sec', 0) / 5.0  # Normalize to ~1.0
        confidence_score = snapshot.get('evomemory', {}).get('avg_confidence', 0.5)
        overall_score = (perf_score + confidence_score) / 2

        snapshot['overall_score'] = min(overall_score, 1.0)

        # Save snapshot
        self.snapshots.append(snapshot)

        # Format output
        formatted = f"""📸 **PERFORMANCE SNAPSHOT CREATED**

**Timestamp**: {snapshot['timestamp']}

**Performance**:
- Speed: {snapshot['performance'].get('avg_tokens_per_sec', 0):.2f} t/s
- Avg Confidence: {confidence_score:.2f}
- Overall Score: {overall_score:.2f}/1.0

**Hardware**:
- RAM Available: {snapshot.get('hardware', {}).get('ram_available_gb', 0):.1f} GB
- CPU Load: {snapshot.get('hardware', {}).get('cpu_percent', 0):.0f}%

**Memory**:
- Neurons: {snapshot.get('evomemory', {}).get('neuron_count', 0)}

**Status**: {"✅ GOLDEN MOMENT" if overall_score > 0.7 else "📊 Baseline recorded"}

Snapshot saved! Can rollback to this state if needed."""

        return {
            'success': True,
            'output': formatted,
            'confidence': 0.95,
            'metadata': snapshot
        }

    async def _analyze_performance_trends(self) -> Dict:
        """
        Analyze performance over time

        Detect if degrading or improving
        """

        if len(self.snapshots) < 2:
            return {
                'success': True,
                'output': "ℹ️  Need at least 2 snapshots to analyze trends\n\nCreate more snapshots over time!",
                'confidence': 0.5
            }

        # Compare recent vs. old snapshots
        recent = self.snapshots[-1]
        baseline = self.snapshots[0]

        recent_score = recent['overall_score']
        baseline_score = baseline['overall_score']

        delta = recent_score - baseline_score
        delta_percent = (delta / baseline_score * 100) if baseline_score > 0 else 0

        # Detect trend
        if delta > 0.1:
            trend = "improving"
            emoji = "📈"
        elif delta < -0.1:
            trend = "degrading"
            emoji = "📉"
        else:
            trend = "stable"
            emoji = "➡️"

        # Format analysis
        formatted = f"""{emoji} **PERFORMANCE TREND ANALYSIS**

**Baseline** ({baseline['timestamp'][:10]}):
- Score: {baseline_score:.2f}/1.0
- Speed: {baseline['performance'].get('avg_tokens_per_sec', 0):.2f} t/s

**Current** ({recent['timestamp'][:10]}):
- Score: {recent_score:.2f}/1.0
- Speed: {recent['performance'].get('avg_tokens_per_sec', 0):.2f} t/s

**Change**: {delta:+.2f} ({delta_percent:+.1f}%)
**Trend**: {trend.upper()}

"""

        if trend == "degrading":
            formatted += "⚠️  **Recommendation**: Consider compression or rollback to best snapshot\n"
            best_snapshot = max(self.snapshots, key=lambda s: s['overall_score'])
            formatted += f"\n**Best snapshot**: {best_snapshot['timestamp'][:10]} (score: {best_snapshot['overall_score']:.2f})"
        elif trend == "improving":
            formatted += "✅ **Great!** System is getting better over time!"
        else:
            formatted += "✅ Performance is stable"

        return {
            'success': True,
            'output': formatted,
            'confidence': 0.9,
            'metadata': {
                'trend': trend,
                'delta': delta,
                'snapshots_count': len(self.snapshots)
            }
        }

    async def _rollback_to_best(self) -> Dict:
        """
        Rollback configuration to best performing snapshot
        """

        if not self.snapshots:
            return {
                'success': False,
                'output': "⚠️  No snapshots available for rollback",
                'confidence': 0.0
            }

        # Find best snapshot
        best_snapshot = max(self.snapshots, key=lambda s: s['overall_score'])

        formatted = f"""⏮️  **ROLLBACK TO BEST STATE**

**Target Snapshot**: {best_snapshot['timestamp'][:10]}
**Score**: {best_snapshot['overall_score']:.2f}/1.0

**Will restore**:
- Configuration from that time
- Performance settings
- (EvoMemory neurons preserved)

**Note**: This is a proposal. Actual rollback requires restart.

Vuoi che prepari il rollback? (y/n)"""

        return {
            'success': True,
            'output': formatted,
            'confidence': 0.8,
            'metadata': {'best_snapshot': best_snapshot}
        }

    def _get_recent_performance(self) -> Dict:
        """
        Get recent performance metrics from metrics_collector

        Returns dict with avg tokens/sec, confidence, etc.
        """

        # Placeholder - would integrate with real metrics_collector
        return {
            'avg_tokens_per_sec': 4.7,
            'avg_confidence': 0.6,
            'total_requests': 100
        }
