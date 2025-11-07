"""
V4 Adverse Events and Monitoring Engine

Implements comprehensive AE modeling with costs and disutilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class AdverseEvent:
    """Definition of an adverse event."""
    
    name: str
    probability: float
    cost: float
    disutility: float  # QALY decrement
    duration_days: int


@dataclass
class MonitoringProtocol:
    """Monitoring requirements for a therapy."""
    
    therapy: str
    vitals_frequency: str  # e.g., "weekly", "monthly"
    lab_tests: List[str]
    lab_frequency: str
    specialist_visits: int
    monitoring_cost_per_cycle: float


@dataclass
class AEResult:
    """Container for adverse event analysis results."""
    
    ae_costs: pd.DataFrame           # AE costs by therapy
    ae_qaly_loss: pd.DataFrame       # QALY loss from AEs
    monitoring_costs: pd.DataFrame   # Monitoring costs
    total_ae_burden: pd.DataFrame    # Combined AE burden


# Define adverse events by therapy
THERAPY_ADVERSE_EVENTS = {
    'ECT': [
        AdverseEvent('Cognitive impairment', 0.30, 500, 0.05, 90),
        AdverseEvent('Headache', 0.50, 50, 0.01, 7),
        AdverseEvent('Muscle aches', 0.40, 30, 0.005, 3),
        AdverseEvent('Confusion', 0.20, 200, 0.02, 14)
    ],
    'KA-ECT': [
        AdverseEvent('Cognitive impairment', 0.22, 500, 0.037, 90),  # Reduced vs ECT
        AdverseEvent('Headache', 0.45, 50, 0.01, 7),
        AdverseEvent('Dissociation', 0.15, 100, 0.01, 1),
        AdverseEvent('Nausea', 0.25, 50, 0.005, 2)
    ],
    'IV-KA': [
        AdverseEvent('Dissociation', 0.40, 100, 0.015, 1),
        AdverseEvent('Blood pressure elevation', 0.30, 150, 0.01, 1),
        AdverseEvent('Nausea', 0.35, 50, 0.005, 2),
        AdverseEvent('Dizziness', 0.25, 30, 0.005, 1)
    ],
    'IN-EKA': [
        AdverseEvent('Dissociation', 0.35, 100, 0.015, 1),
        AdverseEvent('Nasal discomfort', 0.40, 20, 0.002, 1),
        AdverseEvent('Nausea', 0.30, 50, 0.005, 2),
        AdverseEvent('Dizziness', 0.28, 30, 0.005, 1)
    ],
    'PO-PSI': [
        AdverseEvent('Anxiety during session', 0.25, 200, 0.01, 1),
        AdverseEvent('Nausea', 0.40, 50, 0.005, 1),
        AdverseEvent('Headache', 0.30, 50, 0.005, 2),
        AdverseEvent('Fatigue', 0.35, 30, 0.005, 3)
    ],
    'PO-KA': [
        AdverseEvent('Dissociation', 0.25, 100, 0.01, 1),
        AdverseEvent('Nausea', 0.30, 50, 0.005, 2),
        AdverseEvent('Dizziness', 0.20, 30, 0.005, 1),
        AdverseEvent('Sedation', 0.25, 20, 0.003, 1)
    ],
    'rTMS': [
        AdverseEvent('Headache', 0.35, 50, 0.005, 2),
        AdverseEvent('Scalp discomfort', 0.40, 20, 0.002, 1),
        AdverseEvent('Tinnitus', 0.10, 100, 0.01, 7)
    ],
    'UC+Li': [
        AdverseEvent('Tremor', 0.30, 100, 0.01, 30),
        AdverseEvent('Weight gain', 0.25, 50, 0.015, 90),
        AdverseEvent('Polyuria', 0.20, 50, 0.005, 30),
        AdverseEvent('Cognitive dulling', 0.15, 100, 0.01, 60)
    ],
    'UC+AA': [
        AdverseEvent('Weight gain', 0.40, 50, 0.02, 90),
        AdverseEvent('Sedation', 0.35, 30, 0.01, 30),
        AdverseEvent('Metabolic syndrome', 0.15, 500, 0.03, 180),
        AdverseEvent('Akathisia', 0.20, 100, 0.015, 30)
    ],
    'Usual Care': [
        AdverseEvent('GI upset', 0.25, 50, 0.005, 7),
        AdverseEvent('Sexual dysfunction', 0.30, 100, 0.02, 90),
        AdverseEvent('Weight changes', 0.20, 50, 0.01, 60)
    ]
}


# Define monitoring protocols
MONITORING_PROTOCOLS = {
    'ECT': MonitoringProtocol(
        therapy='ECT',
        vitals_frequency='per session',
        lab_tests=['CBC', 'metabolic panel'],
        lab_frequency='baseline and as needed',
        specialist_visits=8,  # Psychiatrist + anesthesiologist
        monitoring_cost_per_cycle=200
    ),
    'KA-ECT': MonitoringProtocol(
        therapy='KA-ECT',
        vitals_frequency='per session',
        lab_tests=['CBC', 'metabolic panel', 'LFTs'],
        lab_frequency='baseline and monthly',
        specialist_visits=8,
        monitoring_cost_per_cycle=250
    ),
    'IV-KA': MonitoringProtocol(
        therapy='IV-KA',
        vitals_frequency='per infusion',
        lab_tests=['LFTs', 'urinalysis'],
        lab_frequency='baseline and monthly',
        specialist_visits=6,
        monitoring_cost_per_cycle=180
    ),
    'IN-EKA': MonitoringProtocol(
        therapy='IN-EKA',
        vitals_frequency='per dose',
        lab_tests=['LFTs'],
        lab_frequency='baseline and quarterly',
        specialist_visits=12,  # Supervised administration
        monitoring_cost_per_cycle=150
    ),
    'PO-PSI': MonitoringProtocol(
        therapy='PO-PSI',
        vitals_frequency='per session',
        lab_tests=['CBC', 'metabolic panel'],
        lab_frequency='baseline',
        specialist_visits=2,  # Therapist supervision
        monitoring_cost_per_cycle=300  # Includes therapy time
    ),
    'PO-KA': MonitoringProtocol(
        therapy='PO-KA',
        vitals_frequency='monthly',
        lab_tests=['LFTs', 'urinalysis'],
        lab_frequency='quarterly',
        specialist_visits=4,
        monitoring_cost_per_cycle=100
    ),
    'rTMS': MonitoringProtocol(
        therapy='rTMS',
        vitals_frequency='baseline',
        lab_tests=[],
        lab_frequency='none',
        specialist_visits=20,  # Daily sessions
        monitoring_cost_per_cycle=150
    ),
    'UC+Li': MonitoringProtocol(
        therapy='UC+Li',
        vitals_frequency='quarterly',
        lab_tests=['lithium level', 'TSH', 'creatinine'],
        lab_frequency='quarterly',
        specialist_visits=4,
        monitoring_cost_per_cycle=120
    ),
    'UC+AA': MonitoringProtocol(
        therapy='UC+AA',
        vitals_frequency='quarterly',
        lab_tests=['metabolic panel', 'lipids', 'HbA1c'],
        lab_frequency='quarterly',
        specialist_visits=4,
        monitoring_cost_per_cycle=100
    ),
    'Usual Care': MonitoringProtocol(
        therapy='Usual Care',
        vitals_frequency='annually',
        lab_tests=[],
        lab_frequency='as needed',
        specialist_visits=4,
        monitoring_cost_per_cycle=80
    )
}


def calculate_ae_burden(
    therapy: str,
    n_patients: int = 1000,
    time_horizon_days: int = 365
) -> Dict[str, float]:
    """
    Calculate adverse event burden for a therapy.
    
    Args:
        therapy: Therapy name
        n_patients: Number of patients
        time_horizon_days: Time horizon in days
    
    Returns:
        Dictionary with AE costs and QALY loss
    """
    adverse_events = THERAPY_ADVERSE_EVENTS.get(therapy, [])
    
    total_ae_cost = 0.0
    total_qaly_loss = 0.0
    
    for ae in adverse_events:
        # Expected number of events
        n_events = n_patients * ae.probability
        
        # Total cost
        total_ae_cost += n_events * ae.cost
        
        # QALY loss (duration in years × disutility)
        qaly_loss_per_event = (ae.duration_days / 365) * ae.disutility
        total_qaly_loss += n_events * qaly_loss_per_event
    
    return {
        'total_ae_cost': total_ae_cost,
        'ae_cost_per_patient': total_ae_cost / n_patients,
        'total_qaly_loss': total_qaly_loss,
        'qaly_loss_per_patient': total_qaly_loss / n_patients
    }


def run_ae_analysis(
    therapies: List[str],
    n_patients: int = 1000,
    time_horizon_days: int = 365
) -> AEResult:
    """
    Run comprehensive adverse event analysis.
    
    Args:
        therapies: List of therapies to analyze
        n_patients: Number of patients
        time_horizon_days: Time horizon in days
    
    Returns:
        AEResult with complete AE analysis
    """
    ae_cost_rows = []
    ae_qaly_rows = []
    monitoring_rows = []
    
    for therapy in therapies:
        # Calculate AE burden
        ae_burden = calculate_ae_burden(therapy, n_patients, time_horizon_days)
        
        ae_cost_rows.append({
            'therapy': therapy,
            'total_ae_cost': ae_burden['total_ae_cost'],
            'ae_cost_per_patient': ae_burden['ae_cost_per_patient']
        })
        
        ae_qaly_rows.append({
            'therapy': therapy,
            'total_qaly_loss': ae_burden['total_qaly_loss'],
            'qaly_loss_per_patient': ae_burden['qaly_loss_per_patient']
        })
        
        # Get monitoring costs
        protocol = MONITORING_PROTOCOLS.get(therapy)
        if protocol:
            # Assume monthly cycles
            n_cycles = time_horizon_days / 30
            total_monitoring_cost = protocol.monitoring_cost_per_cycle * n_cycles * n_patients
            
            monitoring_rows.append({
                'therapy': therapy,
                'monitoring_cost_per_cycle': protocol.monitoring_cost_per_cycle,
                'total_monitoring_cost': total_monitoring_cost,
                'monitoring_cost_per_patient': total_monitoring_cost / n_patients
            })
    
    ae_costs_df = pd.DataFrame(ae_cost_rows)
    ae_qaly_df = pd.DataFrame(ae_qaly_rows)
    monitoring_df = pd.DataFrame(monitoring_rows)
    
    # Combine for total AE burden
    total_burden = ae_costs_df.merge(ae_qaly_df, on='therapy').merge(monitoring_df, on='therapy')
    total_burden['total_cost_per_patient'] = (
        total_burden['ae_cost_per_patient'] + 
        total_burden['monitoring_cost_per_patient']
    )
    
    return AEResult(
        ae_costs=ae_costs_df,
        ae_qaly_loss=ae_qaly_df,
        monitoring_costs=monitoring_df,
        total_ae_burden=total_burden
    )
