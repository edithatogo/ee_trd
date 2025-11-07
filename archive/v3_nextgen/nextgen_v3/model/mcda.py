# mcda.py
import pandas as pd
import os

PENALTIES = {'High': 1.00, 'Moderate': 0.9, 'Low': 0.75, 'VeryLow': 0.6}
VARIANCE_FACTORS = {'High': 1.0, 'Moderate': 1.2, 'Low': 1.5, 'VeryLow': 2.0}

def compute_mcda_scores(inputs, settings):
    """Compute MCDA scores with optional GRADE penalties."""
    weights_df = inputs.mcda_weights
    grade_certainty = inputs.grade_certainty.set_index('Criterion')['Certainty'].to_dict()
    
    # Stub performance data
    performance = {
        'ECT_std': {'Remission': 0.8, 'Relapse': 0.2, 'Serious_AE': 0.05, 'Cognition': 0.9},
        'IV_ketamine': {'Remission': 0.75, 'Relapse': 0.25, 'Serious_AE': 0.03, 'Cognition': 0.85}
    }
    
    results_no_penalty = []
    results_penalty = []
    
    for arm, perf in performance.items():
        scores_no_penalty = {}
        scores_penalty = {}
        for crit, val in perf.items():
            norm_score = val  # Assume already normalized 0-1, higher better
            scores_no_penalty[crit] = norm_score
            if settings.get('grade_penalty', False):
                certainty = grade_certainty.get(crit, 'High')
                penalty = PENALTIES[certainty]
                penalized_score = norm_score * penalty
                scores_penalty[crit] = penalized_score
            else:
                scores_penalty[crit] = norm_score
        
        # Aggregate with weights
        weights = weights_df.set_index('criterion')['weight'].to_dict()
        total_score_no_penalty = sum(scores_no_penalty[crit] * weights.get(crit, 0) for crit in scores_no_penalty)
        total_score_penalty = sum(scores_penalty[crit] * weights.get(crit, 0) for crit in scores_penalty)
        
        results_no_penalty.append({'arm': arm, 'mcda_score': total_score_no_penalty})
        results_penalty.append({'arm': arm, 'mcda_score': total_score_penalty})
    
    df_no_penalty = pd.DataFrame(results_no_penalty)
    df_penalty = pd.DataFrame(results_penalty)
    
    os.makedirs('nextgen_v3/out', exist_ok=True)
    df_no_penalty.to_csv('nextgen_v3/out/mcda_scores_v3.csv', index=False)
    df_penalty.to_csv('nextgen_v3/out/mcda_scores_grade_penalized_v3.csv', index=False)