"""
V4 Pipeline Framework

Unified pipeline orchestration for health economic evaluation.
"""

from analysis.pipeline.orchestrator import (
    AnalysisType,
    TaskStatus,
    PipelineTask,
    PipelineConfig,
    PipelineOrchestrator,
)

from analysis.pipeline.quality_checks import (
    OutputCompleteness,
    PublicationReadiness,
    QualityCheckReport,
    run_quality_checks,
    generate_automated_report,
)

from analysis.pipeline.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    parallel_psa,
    optimize_memory,
    benchmark_analysis,
)

__all__ = [
    # Orchestrator
    "AnalysisType",
    "TaskStatus",
    "PipelineTask",
    "PipelineConfig",
    "PipelineOrchestrator",
    # Quality checks
    "OutputCompleteness",
    "PublicationReadiness",
    "QualityCheckReport",
    "run_quality_checks",
    "generate_automated_report",
    # Performance
    "PerformanceMetrics",
    "PerformanceMonitor",
    "parallel_psa",
    "optimize_memory",
    "benchmark_analysis",
]
