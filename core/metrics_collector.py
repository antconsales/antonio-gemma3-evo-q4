"""
Metrics Collector for Adaptive Prompting
Tracks performance differences between SIMPLE/MEDIUM/COMPLEX questions
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from core.question_classifier import Complexity

class MetricsCollector:
    def __init__(self, metrics_file: str = "/tmp/adaptive_metrics.jsonl"):
        self.metrics_file = Path(metrics_file)
        
    def log_request(
        self,
        question: str,
        complexity: Complexity,
        complexity_reason: str,
        response: str,
        tokens_generated: int,
        tokens_per_second: float,
        response_time_ms: float,
        confidence: float
    ):
        """Log a single request with all metrics"""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:100],  # Truncate for privacy
            "complexity": complexity.name,
            "complexity_reason": complexity_reason,
            "response_length": len(response),
            "tokens_generated": tokens_generated,
            "tokens_per_second": round(tokens_per_second, 2),
            "response_time_ms": round(response_time_ms, 2),
            "confidence": confidence,
        }
        
        # Append to JSONL file
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(metric) + "\n")
    
    def get_stats(self) -> Dict:
        """Get aggregated statistics"""
        if not self.metrics_file.exists():
            return {"error": "No metrics collected yet"}
        
        metrics_by_complexity = {
            "SIMPLE": [],
            "MEDIUM": [],
            "COMPLEX": []
        }
        
        with open(self.metrics_file, "r") as f:
            for line in f:
                metric = json.loads(line)
                complexity = metric["complexity"]
                if complexity in metrics_by_complexity:
                    metrics_by_complexity[complexity].append(metric)
        
        stats = {}
        for complexity, metrics in metrics_by_complexity.items():
            if not metrics:
                continue
                
            stats[complexity] = {
                "count": len(metrics),
                "avg_response_time_ms": round(sum(m["response_time_ms"] for m in metrics) / len(metrics), 2),
                "avg_tokens_per_second": round(sum(m["tokens_per_second"] for m in metrics) / len(metrics), 2),
                "avg_tokens_generated": round(sum(m["tokens_generated"] for m in metrics) / len(metrics), 1),
                "avg_confidence": round(sum(m["confidence"] for m in metrics) / len(metrics), 2),
            }
        
        # Calculate speedup
        if "SIMPLE" in stats and "COMPLEX" in stats:
            stats["speedup_simple_vs_complex"] = round(
                stats["COMPLEX"]["avg_response_time_ms"] / stats["SIMPLE"]["avg_response_time_ms"], 
                2
            )
        
        return stats
