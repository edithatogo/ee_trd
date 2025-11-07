"""
V4 Unified Pipeline Orchestrator

Main pipeline controller for coordinating all analysis types with progress tracking,
error recovery, and checkpointing.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


from trd_cea.core.io import PSAData
from trd_cea.core.validation import run_comprehensive_validation, ValidationReport

__all__ = [
    "AnalysisType",
    "TaskStatus",
    "PipelineTask",
    "PipelineConfig",
    "PipelineOrchestrator",
]


class AnalysisType(Enum):
    """Types of analyses supported by the pipeline."""
    CEA = "cost_effectiveness_analysis"
    DCEA = "distributional_cea"
    VOI = "value_of_information"
    VBP = "value_based_pricing"
    BIA = "budget_impact_analysis"
    SENSITIVITY = "sensitivity_analysis"
    SUBGROUP = "subgroup_analysis"
    SCENARIO = "scenario_analysis"


class TaskStatus(Enum):
    """Status of pipeline tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineTask:
    """Container for pipeline task information."""
    
    task_id: str
    analysis_type: AnalysisType
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output_paths: Optional[List[Path]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'analysis_type': self.analysis_type.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'output_paths': [str(p) for p in self.output_paths] if self.output_paths else None,
        }


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    
    # Input/output paths
    input_data_path: Path
    output_dir: Path
    figures_dir: Path
    
    # Analysis selection
    enabled_analyses: List[AnalysisType]
    
    # Execution settings
    parallel: bool = False
    max_workers: int = 4
    checkpoint_enabled: bool = True
    checkpoint_dir: Optional[Path] = None
    
    # Validation settings
    validate_inputs: bool = True
    validate_outputs: bool = True
    
    # Error handling
    continue_on_error: bool = False
    max_retries: int = 3
    
    # Progress tracking
    progress_callback: Optional[Callable[[str, float], None]] = None
    
    def __post_init__(self):
        """Initialize paths."""
        self.output_dir = Path(self.output_dir)
        self.figures_dir = Path(self.figures_dir)
        
        if self.checkpoint_dir is None:
            self.checkpoint_dir = self.output_dir / 'checkpoints'
        else:
            self.checkpoint_dir = Path(self.checkpoint_dir)


class PipelineOrchestrator:
    """
    Unified pipeline orchestrator for V4 health economic evaluation.
    
    Coordinates all analysis types with progress tracking, error recovery,
    and checkpointing capabilities.
    """
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline orchestrator.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.tasks: List[PipelineTask] = []
        
        # Create output directories FIRST
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.figures_dir.mkdir(parents=True, exist_ok=True)
        if self.config.checkpoint_enabled:
            self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Then setup logging (which needs output_dir to exist)
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for pipeline."""
        logger = logging.getLogger('V4Pipeline')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config.output_dir / 'pipeline.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _create_checkpoint(self, task: PipelineTask) -> None:
        """
        Create checkpoint for task.
        
        Args:
            task: Task to checkpoint
        """
        if not self.config.checkpoint_enabled:
            return
        
        checkpoint_file = self.config.checkpoint_dir / f'{task.task_id}.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)
        
        self.logger.debug(f"Created checkpoint for task {task.task_id}")
    
    def _load_checkpoint(self, task_id: str) -> Optional[PipelineTask]:
        """
        Load checkpoint for task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            PipelineTask if checkpoint exists, None otherwise
        """
        if not self.config.checkpoint_enabled:
            return None
        
        checkpoint_file = self.config.checkpoint_dir / f'{task_id}.json'
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct task
        task = PipelineTask(
            task_id=data['task_id'],
            analysis_type=AnalysisType(data['analysis_type']),
            status=TaskStatus(data['status']),
            start_time=datetime.fromisoformat(data['start_time']) if data['start_time'] else None,
            end_time=datetime.fromisoformat(data['end_time']) if data['end_time'] else None,
            error_message=data['error_message'],
            output_paths=[Path(p) for p in data['output_paths']] if data['output_paths'] else None,
        )
        
        self.logger.debug(f"Loaded checkpoint for task {task_id}")
        return task
    
    def _update_progress(self, message: str, progress: float) -> None:
        """
        Update progress.
        
        Args:
            message: Progress message
            progress: Progress value (0-1)
        """
        self.logger.info(f"Progress: {progress*100:.1f}% - {message}")
        
        if self.config.progress_callback:
            self.config.progress_callback(message, progress)
    
    def _validate_inputs(self) -> ValidationReport:
        """
        Validate input data.
        
        Returns:
            ValidationReport
        """
        self.logger.info("Validating input data...")
        
        # Load PSA data
        psa = PSAData.from_csv(self.config.input_data_path)
        
        # Run validation
        validation_report = run_comprehensive_validation(
            psa=psa,
            config_dict={'version': 'V4'}
        )
        
        if validation_report.overall_status == 'fail':
            self.logger.error(f"Input validation failed with {validation_report.n_errors} errors")
        elif validation_report.overall_status == 'warning':
            self.logger.warning(f"Input validation passed with {validation_report.n_warnings} warnings")
        else:
            self.logger.info("Input validation passed")
        
        return validation_report
    
    def _validate_outputs(self) -> ValidationReport:
        """
        Validate output data.
        
        Returns:
            ValidationReport
        """
        self.logger.info("Validating output data...")
        
        validation_report = run_comprehensive_validation(
            output_dir=self.config.output_dir,
            figures_dir=self.config.figures_dir
        )
        
        if validation_report.overall_status == 'fail':
            self.logger.error(f"Output validation failed with {validation_report.n_errors} errors")
        elif validation_report.overall_status == 'warning':
            self.logger.warning(f"Output validation passed with {validation_report.n_warnings} warnings")
        else:
            self.logger.info("Output validation passed")
        
        return validation_report
    
    def _execute_task(self, task: PipelineTask) -> None:
        """
        Execute a single pipeline task.
        
        Args:
            task: Task to execute
        """
        self.logger.info(f"Executing task: {task.task_id} ({task.analysis_type.value})")
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        self._create_checkpoint(task)
        
        try:
            # Execute analysis based on type
            if task.analysis_type == AnalysisType.CEA:
                self._execute_cea(task)
            elif task.analysis_type == AnalysisType.DCEA:
                self._execute_dcea(task)
            elif task.analysis_type == AnalysisType.VOI:
                self._execute_voi(task)
            elif task.analysis_type == AnalysisType.VBP:
                self._execute_vbp(task)
            elif task.analysis_type == AnalysisType.BIA:
                self._execute_bia(task)
            elif task.analysis_type == AnalysisType.SENSITIVITY:
                self._execute_sensitivity(task)
            elif task.analysis_type == AnalysisType.SUBGROUP:
                self._execute_subgroup(task)
            elif task.analysis_type == AnalysisType.SCENARIO:
                self._execute_scenario(task)
            else:
                raise ValueError(f"Unknown analysis type: {task.analysis_type}")
            
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            self.logger.info(f"Task completed: {task.task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            task.error_message = str(e)
            self.logger.error(f"Task failed: {task.task_id} - {str(e)}")
            
            if not self.config.continue_on_error:
                raise
        
        finally:
            self._create_checkpoint(task)
    
    def _execute_cea(self, task: PipelineTask) -> None:
        """Execute cost-effectiveness analysis."""
        self.logger.info("Running CEA engine...")
        # Placeholder - actual implementation would call CEA engine
        task.output_paths = [
            self.config.output_dir / 'cea_results.csv',
            self.config.figures_dir / 'ce_plane.png',
        ]
    
    def _execute_dcea(self, task: PipelineTask) -> None:
        """Execute distributional cost-effectiveness analysis."""
        self.logger.info("Running DCEA engine...")
        # Placeholder - actual implementation would call DCEA engine
        task.output_paths = [
            self.config.output_dir / 'dcea_results.csv',
            self.config.figures_dir / 'equity_impact_plane.png',
        ]
    
    def _execute_voi(self, task: PipelineTask) -> None:
        """Execute value of information analysis."""
        self.logger.info("Running VOI engine...")
        # Placeholder - actual implementation would call VOI engine
        task.output_paths = [
            self.config.output_dir / 'voi_results.csv',
            self.config.figures_dir / 'evpi_curve.png',
        ]
    
    def _execute_vbp(self, task: PipelineTask) -> None:
        """Execute value-based pricing analysis."""
        self.logger.info("Running VBP engine...")
        # Placeholder - actual implementation would call VBP engine
        task.output_paths = [
            self.config.output_dir / 'vbp_results.csv',
            self.config.figures_dir / 'vbp_curves.png',
        ]
    
    def _execute_bia(self, task: PipelineTask) -> None:
        """Execute budget impact analysis."""
        self.logger.info("Running BIA engine...")
        # Placeholder - actual implementation would call BIA engine
        task.output_paths = [
            self.config.output_dir / 'bia_results.csv',
            self.config.figures_dir / 'budget_impact.png',
        ]
    
    def _execute_sensitivity(self, task: PipelineTask) -> None:
        """Execute sensitivity analysis."""
        self.logger.info("Running sensitivity analysis...")
        # Placeholder - actual implementation would call sensitivity engine
        task.output_paths = [
            self.config.output_dir / 'sensitivity_results.csv',
            self.config.figures_dir / 'tornado_diagram.png',
        ]
    
    def _execute_subgroup(self, task: PipelineTask) -> None:
        """Execute subgroup analysis."""
        self.logger.info("Running subgroup analysis...")
        # Placeholder - actual implementation would call subgroup engine
        task.output_paths = [
            self.config.output_dir / 'subgroup_results.csv',
            self.config.figures_dir / 'subgroup_comparison.png',
        ]
    
    def _execute_scenario(self, task: PipelineTask) -> None:
        """Execute scenario analysis."""
        self.logger.info("Running scenario analysis...")
        # Placeholder - actual implementation would call scenario engine
        task.output_paths = [
            self.config.output_dir / 'scenario_results.csv',
            self.config.figures_dir / 'scenario_comparison.png',
        ]
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete pipeline.
        
        Returns:
            Dictionary with execution summary
        """
        self.logger.info("=" * 80)
        self.logger.info("V4 Pipeline Orchestrator - Starting Execution")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Validate inputs
        if self.config.validate_inputs:
            self._update_progress("Validating inputs", 0.0)
            input_validation = self._validate_inputs()
            
            if input_validation.overall_status == 'fail':
                self.logger.error("Input validation failed. Aborting pipeline.")
                return {
                    'status': 'failed',
                    'reason': 'input_validation_failed',
                    'validation_report': input_validation
                }
        
        # Create tasks for enabled analyses
        self.tasks = []
        for analysis_type in self.config.enabled_analyses:
            task_id = f"{analysis_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check for existing checkpoint
            existing_task = self._load_checkpoint(task_id)
            if existing_task and existing_task.status == TaskStatus.COMPLETED:
                self.logger.info(f"Skipping completed task: {task_id}")
                self.tasks.append(existing_task)
                continue
            
            task = PipelineTask(
                task_id=task_id,
                analysis_type=analysis_type,
                status=TaskStatus.PENDING
            )
            self.tasks.append(task)
        
        # Execute tasks
        total_tasks = len(self.tasks)
        for i, task in enumerate(self.tasks):
            if task.status == TaskStatus.COMPLETED:
                continue
            
            progress = (i + 1) / total_tasks
            self._update_progress(f"Executing {task.analysis_type.value}", progress)
            
            self._execute_task(task)
        
        # Validate outputs
        if self.config.validate_outputs:
            self._update_progress("Validating outputs", 1.0)
            output_validation = self._validate_outputs()
        else:
            output_validation = None
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        completed_tasks = [t for t in self.tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks if t.status == TaskStatus.FAILED]
        
        summary = {
            'status': 'completed' if len(failed_tasks) == 0 else 'partial',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_tasks': total_tasks,
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'tasks': [t.to_dict() for t in self.tasks],
            'output_validation': output_validation.overall_status if output_validation else None,
        }
        
        # Save summary
        summary_file = self.config.output_dir / 'pipeline_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info("=" * 80)
        self.logger.info("Pipeline Execution Complete")
        self.logger.info(f"Duration: {duration:.1f} seconds")
        self.logger.info(f"Completed: {len(completed_tasks)}/{total_tasks} tasks")
        if failed_tasks:
            self.logger.warning(f"Failed: {len(failed_tasks)} tasks")
        self.logger.info("=" * 80)
        
        return summary
    
    def resume(self) -> Dict[str, Any]:
        """
        Resume pipeline from last checkpoint.
        
        Returns:
            Dictionary with execution summary
        """
        self.logger.info("Resuming pipeline from checkpoints...")
        
        # Load all checkpoints
        if not self.config.checkpoint_dir.exists():
            self.logger.warning("No checkpoint directory found. Starting fresh.")
            return self.run()
        
        checkpoint_files = list(self.config.checkpoint_dir.glob('*.json'))
        if not checkpoint_files:
            self.logger.warning("No checkpoints found. Starting fresh.")
            return self.run()
        
        # Load tasks from checkpoints
        self.tasks = []
        for checkpoint_file in checkpoint_files:
            task_id = checkpoint_file.stem
            task = self._load_checkpoint(task_id)
            if task:
                self.tasks.append(task)
        
        self.logger.info(f"Loaded {len(self.tasks)} tasks from checkpoints")
        
        # Continue execution
        return self.run()
