"""
V4 Multi-Criteria Decision Analysis Engine

Implements MCDA for comprehensive treatment evaluation across multiple criteria
with customizable weighting for different stakeholder perspectives.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd

from trd_cea.core.io import PSAData


@dataclass
class MCDACriteria:
    """Definition of MCDA criteria with weights and directions."""
    
    name: str
    weight: float
    direction: str  # 'maximize' or 'minimize'
    description: str
    unit: str


@dataclass
class MCDAResult:
    """Container for MCDA results."""
    
    scores: pd.DataFrame           # Raw criteria scores for each strategy
    weighted_scores: pd.DataFrame  # Weighted scores
    rankings: pd.DataFrame         # Strategy rankings with confidence intervals
    criteria: List[MCDACriteria]
    perspective: str
    jurisdiction: Optional[str]


@dataclass
class MCDASensitivityResult:
    """Container for MCDA sensitivity analysis results."""
    
    weight_ranges: pd.DataFrame     # Weight sensitivity ranges
    ranking_stability: pd.DataFrame # Ranking stability analysis
    trade_offs: pd.DataFrame        # Criteria trade-off analysis
    perspective: str
    jurisdiction: Optional[str]


def create_default_criteria(perspective: str = "health_system") -> List[MCDACriteria]:
    """
    Create default MCDA criteria based on stakeholder perspective.
    
    Args:
        perspective: Stakeholder perspective ('health_system', 'societal', 'patient')
        
    Returns:
        List of MCDA criteria with default weights
    """
    if perspective == "health_system":
        return [
            MCDACriteria("clinical_effectiveness", 0.35, "maximize", 
                        "Health outcomes (QALYs gained)", "QALYs"),
            MCDACriteria("cost_impact", 0.25, "minimize", 
                        "Healthcare system costs", "AUD"),
            MCDACriteria("safety", 0.20, "maximize", 
                        "Safety profile (adverse events avoided)", "events"),
            MCDACriteria("equity", 0.10, "maximize", 
                        "Equity impact (distributional effects)", "index"),
            MCDACriteria("feasibility", 0.10, "maximize", 
                        "Implementation feasibility", "score")
        ]
    elif perspective == "societal":
        return [
            MCDACriteria("clinical_effectiveness", 0.30, "maximize", 
                        "Health outcomes (QALYs gained)", "QALYs"),
            MCDACriteria("cost_impact", 0.20, "minimize", 
                        "Societal costs (healthcare + productivity)", "AUD"),
            MCDACriteria("safety", 0.20, "maximize", 
                        "Safety profile (adverse events avoided)", "events"),
            MCDACriteria("equity", 0.20, "maximize", 
                        "Equity impact (distributional effects)", "index"),
            MCDACriteria("feasibility", 0.10, "maximize", 
                        "Implementation feasibility", "score")
        ]
    elif perspective == "patient":
        return [
            MCDACriteria("clinical_effectiveness", 0.40, "maximize", 
                        "Health outcomes (QALYs gained)", "QALYs"),
            MCDACriteria("safety", 0.30, "maximize", 
                        "Safety profile (adverse events avoided)", "events"),
            MCDACriteria("cost_impact", 0.15, "minimize", 
                        "Patient out-of-pocket costs", "AUD"),
            MCDACriteria("equity", 0.10, "maximize", 
                        "Access equity", "index"),
            MCDACriteria("feasibility", 0.05, "maximize", 
                        "Patient acceptability", "score")
        ]
    else:
        raise ValueError(f"Unknown perspective: {perspective}")


def normalize_scores(scores: np.ndarray, direction: str) -> np.ndarray:
    """
    Normalize scores to 0-1 scale based on direction.
    
    Args:
        scores: Raw scores array
        direction: 'maximize' or 'minimize'
        
    Returns:
        Normalized scores (0-1 scale)
    """
    if direction == "maximize":
        min_val, max_val = np.min(scores), np.max(scores)
        if max_val == min_val:
            return np.ones_like(scores)  # All equal
        return (scores - min_val) / (max_val - min_val)
    elif direction == "minimize":
        min_val, max_val = np.min(scores), np.max(scores)
        if max_val == min_val:
            return np.ones_like(scores)  # All equal
        return (max_val - scores) / (max_val - min_val)
    else:
        raise ValueError(f"Unknown direction: {direction}")


def calculate_mcda_scores(
    psa: PSAData,
    criteria: List[MCDACriteria],
    n_boot: int = 1000
) -> MCDAResult:
    """
    Calculate MCDA scores and rankings for all strategies.
    
    Args:
        psa: PSA data with strategy results
        criteria: List of MCDA criteria with weights
        n_boot: Number of bootstrap samples for confidence intervals
        
    Returns:
        MCDA results with scores, rankings, and confidence intervals
    """
    strategies = psa.strategies
    n_strategies = len(strategies)
    
    # Initialize results storage
    raw_scores = {}
    weighted_scores = np.zeros((n_boot, n_strategies))
    rankings = np.zeros((n_boot, n_strategies), dtype=int)
    
    # Extract criteria scores from PSA data
    for criterion in criteria:
        if criterion.name == "clinical_effectiveness":
            # Use QALYs from PSA data
            scores = psa.table.groupby("strategy")["effect"].mean().reindex(strategies).values
        elif criterion.name == "cost_impact":
            # Use costs from PSA data (minimize)
            scores = psa.table.groupby("strategy")["cost"].mean().reindex(strategies).values
        elif criterion.name == "safety":
            # Placeholder - would need adverse events data
            scores = np.random.uniform(0.5, 1.0, n_strategies)  # Mock data
        elif criterion.name == "equity":
            # Placeholder - would need equity metrics
            scores = np.random.uniform(0.3, 0.9, n_strategies)  # Mock data
        elif criterion.name == "feasibility":
            # Placeholder - would need feasibility scores
            scores = np.random.uniform(0.4, 0.95, n_strategies)  # Mock data
        else:
            raise ValueError(f"Unknown criterion: {criterion.name}")
            
        raw_scores[criterion.name] = scores
        
        # Normalize scores
        _normalized = normalize_scores(scores, criterion.direction)
        
        # Bootstrap for uncertainty
        for i in range(n_boot):
            # Sample with replacement from PSA data
            sample_indices = np.random.choice(len(psa.table), size=len(psa.table), replace=True)
            sample_data = psa.table.iloc[sample_indices]
            
            if criterion.name == "clinical_effectiveness":
                sample_scores = sample_data.groupby("strategy")["effect"].mean().reindex(strategies).values
            elif criterion.name == "cost_impact":
                sample_scores = sample_data.groupby("strategy")["cost"].mean().reindex(strategies).values
            else:
                # For other criteria, add some noise to mock data
                sample_scores = scores + np.random.normal(0, 0.1, n_strategies)
            
            sample_normalized = normalize_scores(sample_scores, criterion.direction)
            weighted_scores[i] += criterion.weight * sample_normalized
    
    # Calculate rankings from weighted scores
    for i in range(n_boot):
        rankings[i] = np.argsort(-weighted_scores[i])  # Sort in descending order
    
    # Create results DataFrames
    scores_df = pd.DataFrame(raw_scores, index=strategies)
    scores_df.index.name = "strategy"
    
    # Calculate mean weighted scores and rankings
    mean_weighted_scores = np.mean(weighted_scores, axis=0)
    mean_rankings = np.mean(rankings, axis=0)
    
    # Calculate confidence intervals
    weighted_scores_ci_lower = np.percentile(weighted_scores, 2.5, axis=0)
    weighted_scores_ci_upper = np.percentile(weighted_scores, 97.5, axis=0)
    
    rankings_df = pd.DataFrame({
        "strategy": strategies,
        "mean_score": mean_weighted_scores,
        "score_ci_lower": weighted_scores_ci_lower,
        "score_ci_upper": weighted_scores_ci_upper,
        "mean_rank": mean_rankings + 1,  # 1-based ranking
        "rank_ci_lower": np.percentile(rankings, 2.5, axis=0) + 1,
        "rank_ci_upper": np.percentile(rankings, 97.5, axis=0) + 1
    })
    
    weighted_scores_df = pd.DataFrame(
        mean_weighted_scores.reshape(1, -1),
        columns=strategies
    )
    
    return MCDAResult(
        scores=scores_df,
        weighted_scores=weighted_scores_df,
        rankings=rankings_df,
        criteria=criteria,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def perform_weight_sensitivity_analysis(
    psa: PSAData,
    criteria: List[MCDACriteria],
    weight_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    n_scenarios: int = 100
) -> MCDASensitivityResult:
    """
    Perform sensitivity analysis on MCDA weights.
    
    Args:
        psa: PSA data
        criteria: MCDA criteria
        weight_ranges: Optional custom weight ranges for sensitivity
        n_scenarios: Number of weight scenarios to test
        
    Returns:
        Sensitivity analysis results
    """
    if weight_ranges is None:
        # Default ±20% variation on each weight
        weight_ranges = {}
        for criterion in criteria:
            base_weight = criterion.weight
            weight_ranges[criterion.name] = (max(0, base_weight - 0.2), min(1, base_weight + 0.2))
    
    strategies = psa.strategies
    n_strategies = len(strategies)
    
    # Generate weight scenarios
    weight_scenarios = []
    for _ in range(n_scenarios):
        scenario = {}
        total_weight = 0
        for criterion in criteria[:-1]:  # Leave last criterion to balance
            min_w, max_w = weight_ranges[criterion.name]
            weight = np.random.uniform(min_w, max_w)
            scenario[criterion.name] = weight
            total_weight += weight
        
        # Balance last criterion
        last_criterion = criteria[-1]
        min_w, max_w = weight_ranges[last_criterion.name]
        remaining = 1 - total_weight
        scenario[last_criterion.name] = np.clip(remaining, min_w, max_w)
        
        weight_scenarios.append(scenario)
    
    # Calculate rankings for each scenario
    rankings_matrix = np.zeros((n_scenarios, n_strategies))
    
    for i, weights in enumerate(weight_scenarios):
        # Calculate weighted scores
        weighted_scores = np.zeros(n_strategies)
        
        for j, strategy in enumerate(strategies):
            for criterion in criteria:
                if criterion.name == "clinical_effectiveness":
                    score = psa.table[psa.table["strategy"] == strategy]["effect"].mean()
                elif criterion.name == "cost_impact":
                    score = -psa.table[psa.table["strategy"] == strategy]["cost"].mean()  # Negative for minimization
                else:
                    score = np.random.uniform(0.5, 1.0)  # Mock data
                
                _normalized = normalize_scores(np.array([score]), criterion.direction)[0]
                weighted_scores[j] += weights[criterion.name] * _normalized
        
        rankings_matrix[i] = np.argsort(-weighted_scores) + 1  # 1-based ranking
    
    # Analyze ranking stability
    ranking_stability = []
    for j, strategy in enumerate(strategies):
        ranks = rankings_matrix[:, j]
        stability_data = {
            "strategy": strategy,
            "mean_rank": np.mean(ranks),
            "rank_std": np.std(ranks),
            "rank_range": np.max(ranks) - np.min(ranks),
            "top_3_percent": np.mean(ranks <= 3) * 100
        }
        ranking_stability.append(stability_data)
    
    stability_df = pd.DataFrame(ranking_stability)
    
    # Weight ranges summary
    weight_ranges_df = pd.DataFrame([
        {"criterion": c.name, "min_weight": r[0], "max_weight": r[1], "base_weight": c.weight}
        for c, r in zip(criteria, [weight_ranges[c.name] for c in criteria])
    ])
    
    # Trade-off analysis (simplified)
    trade_offs_df = pd.DataFrame({
        "criterion_1": [c.name for c in criteria],
        "criterion_2": [criteria[(i+1) % len(criteria)].name for i, c in enumerate(criteria)],
        "correlation": np.random.uniform(-0.3, 0.3, len(criteria))  # Mock correlations
    })
    
    return MCDASensitivityResult(
        weight_ranges=weight_ranges_df,
        ranking_stability=stability_df,
        trade_offs=trade_offs_df,
        perspective=psa.perspective,
        jurisdiction=psa.jurisdiction
    )


def create_custom_criteria(
    base_criteria: List[MCDACriteria],
    custom_weights: Dict[str, float]
) -> List[MCDACriteria]:
    """
    Create MCDA criteria with custom weights.
    
    Args:
        base_criteria: Base criteria to modify
        custom_weights: Dictionary mapping criterion names to new weights
        
    Returns:
        Modified criteria with custom weights
        
    Raises:
        ValueError: If weights don't sum to 1 or contain invalid values
    """
    # Validate weights
    total_weight = sum(custom_weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    for name, weight in custom_weights.items():
        if not 0 <= weight <= 1:
            raise ValueError(f"Weight for {name} must be between 0 and 1, got {weight}")
    
    # Check all criteria are covered
    base_names = {c.name for c in base_criteria}
    custom_names = set(custom_weights.keys())
    if base_names != custom_names:
        missing = base_names - custom_names
        extra = custom_names - base_names
        error_msg = "Custom weights must match all base criteria."
        if missing:
            error_msg += f" Missing: {missing}"
        if extra:
            error_msg += f" Extra: {extra}"
        raise ValueError(error_msg)
    
    # Create modified criteria
    return [
        MCDACriteria(
            name=c.name,
            weight=custom_weights[c.name],
            direction=c.direction,
            description=c.description,
            unit=c.unit
        )
        for c in base_criteria
    ]


def validate_mcda_criteria(criteria: List[MCDACriteria]) -> None:
    """
    Validate MCDA criteria configuration.
    
    Args:
        criteria: List of criteria to validate
        
    Raises:
        ValueError: If criteria are invalid
    """
    if not criteria:
        raise ValueError("At least one criterion required")
    
    total_weight = sum(c.weight for c in criteria)
    if not np.isclose(total_weight, 1.0, atol=1e-6):
        raise ValueError(f"Criteria weights must sum to 1.0, got {total_weight}")
    
    names = [c.name for c in criteria]
    if len(names) != len(set(names)):
        duplicates = [name for name in names if names.count(name) > 1]
        raise ValueError(f"Duplicate criterion names: {duplicates}")
    
    for criterion in criteria:
        if not 0 <= criterion.weight <= 1:
            raise ValueError(f"Weight for {criterion.name} must be between 0 and 1, got {criterion.weight}")
        
        if criterion.direction not in ["maximize", "minimize"]:
            raise ValueError(f"Direction for {criterion.name} must be 'maximize' or 'minimize', got {criterion.direction}")


def get_weight_presets() -> Dict[str, Dict[str, float]]:
    """
    Get predefined weight presets for different scenarios.
    
    Returns:
        Dictionary of preset names to weight dictionaries
    """
    return {
        "health_system_focused": {
            "clinical_effectiveness": 0.40,
            "cost_impact": 0.30,
            "safety": 0.15,
            "equity": 0.10,
            "feasibility": 0.05
        },
        "patient_centered": {
            "clinical_effectiveness": 0.35,
            "safety": 0.30,
            "cost_impact": 0.15,
            "equity": 0.15,
            "feasibility": 0.05
        },
        "equity_focused": {
            "equity": 0.30,
            "clinical_effectiveness": 0.25,
            "safety": 0.20,
            "cost_impact": 0.15,
            "feasibility": 0.10
        },
        "cost_containment": {
            "cost_impact": 0.40,
            "clinical_effectiveness": 0.25,
            "safety": 0.20,
            "feasibility": 0.10,
            "equity": 0.05
        },
        "balanced": {
            "clinical_effectiveness": 0.25,
            "cost_impact": 0.25,
            "safety": 0.20,
            "equity": 0.15,
            "feasibility": 0.15
        }
    }


def integrate_mcda_cea(
    mcda_result: MCDAResult,
    cea_result: Any  # Would be CEAResult from cea_engine
) -> pd.DataFrame:
    """
    Integrate MCDA and CEA results for comparative analysis.
    
    Args:
        mcda_result: MCDA analysis results
        cea_result: CEA analysis results (CEAResult)
        
    Returns:
        Integrated results DataFrame with rankings comparison
    """
    # Extract CEA rankings (assuming cea_result has similar structure)
    # This would need to be adapted based on actual CEAResult structure
    _cea_rankings = {}  # Placeholder
    
    # For now, create mock CEA rankings
    strategies = mcda_result.rankings["strategy"].tolist()
    mock_cea_ranks = {strategy: i+1 for i, strategy in enumerate(
        sorted(strategies, key=lambda x: np.random.random())
    )}
    
    # Create integrated comparison
    comparison_data = []
    for _, row in mcda_result.rankings.iterrows():
        strategy = row["strategy"]
        mcda_rank = row["mean_rank"]
        cea_rank = mock_cea_ranks.get(strategy, len(strategies))
        
        comparison_data.append({
            "strategy": strategy,
            "mcda_rank": mcda_rank,
            "cea_rank": cea_rank,
            "rank_difference": mcda_rank - cea_rank,
            "mcda_score": row["mean_score"],
            "agreement": "High" if abs(mcda_rank - cea_rank) <= 1 else 
                       "Medium" if abs(mcda_rank - cea_rank) <= 2 else "Low"
        })
    
    return pd.DataFrame(comparison_data)


def create_criteria_trade_off_data(
    mcda_result: MCDAResult,
    criteria_pairs: Optional[List[tuple[str, str]]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Create data for criteria trade-off visualizations.
    
    Args:
        mcda_result: MCDA results
        criteria_pairs: Pairs of criteria to analyze trade-offs for
        
    Returns:
        Dictionary mapping pair names to trade-off DataFrames
    """
    if criteria_pairs is None:
        criteria_names = [c.name for c in mcda_result.criteria]
        criteria_pairs = []
        for i in range(len(criteria_names)):
            for j in range(i+1, len(criteria_names)):
                criteria_pairs.append((criteria_names[i], criteria_names[j]))
    
    trade_off_data = {}
    
    for crit1, crit2 in criteria_pairs:
        if crit1 not in mcda_result.scores.columns or crit2 not in mcda_result.scores.columns:
            continue
            
        scores1 = mcda_result.scores[crit1]
        scores2 = mcda_result.scores[crit2]
        
        # Normalize scores for plotting
        scores1_norm = (scores1 - scores1.min()) / (scores1.max() - scores1.min())
        scores2_norm = (scores2 - scores2.min()) / (scores2.max() - scores2.min())
        
        pair_data = pd.DataFrame({
            "strategy": mcda_result.scores.index,
            f"{crit1}_score": scores1,
            f"{crit2}_score": scores2,
            f"{crit1}_normalized": scores1_norm,
            f"{crit2}_normalized": scores2_norm,
            "mcda_weighted_score": mcda_result.weighted_scores.iloc[0].values
        })
        
        trade_off_data[f"{crit1}_vs_{crit2}"] = pair_data
    
    return trade_off_data


def calculate_mcda_robustness(
    mcda_result: MCDAResult,
    sensitivity_result: MCDASensitivityResult
) -> pd.DataFrame:
    """
    Calculate robustness metrics for MCDA rankings.
    
    Args:
        mcda_result: Base MCDA results
        sensitivity_result: Sensitivity analysis results
        
    Returns:
        Robustness metrics DataFrame
    """
    robustness_data = []
    
    for _, row in sensitivity_result.ranking_stability.iterrows():
        strategy = row["strategy"]
        base_rank = mcda_result.rankings[
            mcda_result.rankings["strategy"] == strategy
        ]["mean_rank"].iloc[0]
        
        robustness_data.append({
            "strategy": strategy,
            "base_rank": base_rank,
            "rank_stability": 1 / (1 + row["rank_std"]),  # Higher is more stable
            "rank_range": row["rank_range"],
            "top_3_consistency": row["top_3_percent"] / 100,
            "robustness_score": (
                (1 / (1 + row["rank_std"])) * 
                (1 - row["rank_range"] / len(mcda_result.rankings)) *
                (row["top_3_percent"] / 100)
            )
        })
    
    robustness_df = pd.DataFrame(robustness_data)
    robustness_df = robustness_df.sort_values("robustness_score", ascending=False)
    
    return robustness_df


def generate_mcda_summary_report(
    mcda_result: MCDAResult,
    sensitivity_result: Optional[MCDASensitivityResult] = None,
    cea_comparison: Optional[pd.DataFrame] = None
) -> str:
    """
    Generate a comprehensive MCDA summary report.
    
    Args:
        mcda_result: MCDA results
        sensitivity_result: Optional sensitivity analysis results
        cea_comparison: Optional CEA comparison data
        
    Returns:
        Formatted summary report as string
    """
    report_lines = []
    report_lines.append("# MCDA Analysis Summary Report")
    report_lines.append(f"**Perspective:** {mcda_result.perspective}")
    if mcda_result.jurisdiction:
        report_lines.append(f"**Jurisdiction:** {mcda_result.jurisdiction}")
    report_lines.append("")
    
    # Criteria summary
    report_lines.append("## Criteria Configuration")
    for criterion in mcda_result.criteria:
        report_lines.append(f"- **{criterion.name}** (weight: {criterion.weight:.2f}): {criterion.description}")
    report_lines.append("")
    
    # Rankings summary
    report_lines.append("## Strategy Rankings")
    top_3 = mcda_result.rankings.nsmallest(3, "mean_rank")
    for _, row in top_3.iterrows():
        report_lines.append(f"{int(row['mean_rank'])}. {row['strategy']} "
                          f"(score: {row['mean_score']:.3f})")
    report_lines.append("")
    
    # Sensitivity analysis
    if sensitivity_result is not None:
        report_lines.append("## Sensitivity Analysis")
        stable_strategies = sensitivity_result.ranking_stability.nlargest(3, "top_3_percent")
        report_lines.append("Most stable strategies (top-3 consistency):")
        for _, row in stable_strategies.iterrows():
            report_lines.append(f"- {row['strategy']}: {row['top_3_percent']:.1f}%")
        report_lines.append("")
    
    # CEA comparison
    if cea_comparison is not None:
        report_lines.append("## CEA-MCDA Comparison")
        high_agreement = cea_comparison[cea_comparison["agreement"] == "High"]
        report_lines.append(f"High agreement strategies: {len(high_agreement)}/{len(cea_comparison)}")
        if len(high_agreement) > 0:
            report_lines.append("High agreement strategies:")
            for _, row in high_agreement.iterrows():
                report_lines.append(f"- {row['strategy']}: MCDA rank {row['mcda_rank']:.1f}, "
                                  f"CEA rank {row['cea_rank']}")
        report_lines.append("")
    
    report_lines.append("## Recommendations")
    best_strategy = mcda_result.rankings.iloc[0]["strategy"]
    report_lines.append(f"**Top-ranked strategy:** {best_strategy}")
    
    if sensitivity_result is not None:
        robustness = calculate_mcda_robustness(mcda_result, sensitivity_result)
        most_robust = robustness.iloc[0]["strategy"]
        if most_robust != best_strategy:
            report_lines.append(f"**Most robust strategy:** {most_robust}")
    
    return "\n".join(report_lines)