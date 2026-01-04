from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import defaultdict, deque
import time

from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    """指标基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.description = description
        self.labels = labels or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "labels": self.labels,
            "created_at": self.created_at.isoformat()
        }


class Counter(Metric):
    """计数器"""
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, description, labels)
        self.value = 0.0
    
    def inc(self, value: float = 1.0):
        """增加计数"""
        if value < 0:
            raise ValueError("Counter can only be incremented")
        self.value += value
    
    def get(self) -> float:
        """获取当前值"""
        return self.value
    
    def reset(self):
        """重置计数器"""
        self.value = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["type"] = "counter"
        base["value"] = self.value
        return base


class Gauge(Metric):
    """仪表"""
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, description, labels)
        self.value = 0.0
    
    def set(self, value: float):
        """设置值"""
        self.value = value
    
    def inc(self, value: float = 1.0):
        """增加值"""
        self.value += value
    
    def dec(self, value: float = 1.0):
        """减少值"""
        self.value -= value
    
    def get(self) -> float:
        """获取当前值"""
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["type"] = "gauge"
        base["value"] = self.value
        return base


class Histogram(Metric):
    """直方图"""
    
    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, description, labels)
        self.buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self.bucket_counts = defaultdict(int)
        self.sum = 0.0
        self.count = 0
    
    def observe(self, value: float):
        """观察值"""
        self.count += 1
        self.sum += value
        
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1
    
    def get_bucket_counts(self) -> Dict[str, int]:
        """获取桶计数"""
        return {str(k): v for k, v in self.bucket_counts.items()}
    
    def get_sum(self) -> float:
        """获取总和"""
        return self.sum
    
    def get_count(self) -> int:
        """获取计数"""
        return self.count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["type"] = "histogram"
        base["buckets"] = self.buckets
        base["bucket_counts"] = self.get_bucket_counts()
        base["sum"] = self.sum
        base["count"] = self.count
        return base


class Summary(Metric):
    """摘要"""
    
    def __init__(
        self,
        name: str,
        description: str,
        quantiles: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, description, labels)
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self.values: List[float] = []
        self.sum = 0.0
        self.count = 0
        self.max_values = 1000
    
    def observe(self, value: float):
        """观察值"""
        self.count += 1
        self.sum += value
        self.values.append(value)
        
        if len(self.values) > self.max_values:
            self.values.pop(0)
    
    def get_quantile(self, q: float) -> float:
        """获取分位数"""
        if not self.values:
            return 0.0
        
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * q)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_quantiles(self) -> Dict[str, float]:
        """获取所有分位数"""
        return {str(q): self.get_quantile(q) for q in self.quantiles}
    
    def get_sum(self) -> float:
        """获取总和"""
        return self.sum
    
    def get_count(self) -> int:
        """获取计数"""
        return self.count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base["type"] = "summary"
        base["quantiles"] = self.get_quantiles()
        base["sum"] = self.sum
        base["count"] = self.count
        return base


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.summaries: Dict[str, Summary] = {}
        self.lock = asyncio.Lock()
    
    def counter(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """创建或获取计数器"""
        key = self._make_key(name, labels)
        
        if key not in self.counters:
            self.counters[key] = Counter(name, description, labels)
            logger.debug(f"Created counter: {name}")
        
        return self.counters[key]
    
    def gauge(
        self,
        name: str,
        description: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """创建或获取仪表"""
        key = self._make_key(name, labels)
        
        if key not in self.gauges:
            self.gauges[key] = Gauge(name, description, labels)
            logger.debug(f"Created gauge: {name}")
        
        return self.gauges[key]
    
    def histogram(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Histogram:
        """创建或获取直方图"""
        key = self._make_key(name, labels)
        
        if key not in self.histograms:
            self.histograms[key] = Histogram(name, description, buckets, labels)
            logger.debug(f"Created histogram: {name}")
        
        return self.histograms[key]
    
    def summary(
        self,
        name: str,
        description: str,
        quantiles: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Summary:
        """创建或获取摘要"""
        key = self._make_key(name, labels)
        
        if key not in self.summaries:
            self.summaries[key] = Summary(name, description, quantiles, labels)
            logger.debug(f"Created summary: {name}")
        
        return self.summaries[key]
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """生成键"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有指标"""
        return {
            "counters": [m.to_dict() for m in self.counters.values()],
            "gauges": [m.to_dict() for m in self.gauges.values()],
            "histograms": [m.to_dict() for m in self.histograms.values()],
            "summaries": [m.to_dict() for m in self.summaries.values()]
        }
    
    def reset_all(self):
        """重置所有指标"""
        for counter in self.counters.values():
            counter.reset()
        for gauge in self.gauges.values():
            gauge.set(0)
        for histogram in self.histograms.values():
            histogram.bucket_counts.clear()
            histogram.sum = 0.0
            histogram.count = 0
        for summary in self.summaries.values():
            summary.values.clear()
            summary.sum = 0.0
            summary.count = 0
        
        logger.info("All metrics reset")
    
    def export_prometheus(self) -> str:
        """导出为Prometheus格式"""
        lines = []
        
        for counter in self.counters.values():
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            if counter.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in counter.labels.items())
                lines.append(f'{counter.name}{{{label_str}}} {counter.value}')
            else:
                lines.append(f"{counter.name} {counter.value}")
        
        for gauge in self.gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            if gauge.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in gauge.labels.items())
                lines.append(f'{gauge.name}{{{label_str}}} {gauge.value}')
            else:
                lines.append(f"{gauge.name} {gauge.value}")
        
        for histogram in self.histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.description}")
            lines.append(f"# TYPE {histogram.name} histogram")
            if histogram.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in histogram.labels.items())
                lines.append(f'{histogram.name}_sum{{{label_str}}} {histogram.sum}')
                lines.append(f'{histogram.name}_count{{{label_str}}} {histogram.count}')
                for bucket, count in histogram.bucket_counts.items():
                    lines.append(f'{histogram.name}_bucket{{{label_str},le="{bucket}"}} {count}')
            else:
                lines.append(f"{histogram.name}_sum {histogram.sum}")
                lines.append(f"{histogram.name}_count {histogram.count}")
                for bucket, count in histogram.bucket_counts.items():
                    lines.append(f'{histogram.name}_bucket{{le="{bucket}"}} {count}')
        
        for summary in self.summaries.values():
            lines.append(f"# HELP {summary.name} {summary.description}")
            lines.append(f"# TYPE {summary.name} summary")
            if summary.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in summary.labels.items())
                lines.append(f'{summary.name}_sum{{{label_str}}} {summary.sum}')
                lines.append(f'{summary.name}_count{{{label_str}}} {summary.count}')
                for quantile, value in summary.get_quantiles().items():
                    lines.append(f'{summary.name}{{{label_str},quantile="{quantile}"}} {value}')
            else:
                lines.append(f"{summary.name}_sum {summary.sum}")
                lines.append(f"{summary.name}_count {summary.count}")
                for quantile, value in summary.get_quantiles().items():
                    lines.append(f'{summary.name}{{quantile="{quantile}"}} {value}')
        
        return "\n".join(lines)
