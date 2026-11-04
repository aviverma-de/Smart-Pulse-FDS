"""
SmartPulse Preprocessing Utilities
Strictly mirrors the training-time preprocessing from 01_classifier.py and 02_bayesian_regression.py.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from .models import AssessmentInput

FEATURE_COLUMNS = [
    "sleep_mid_hrs",
    "sleep_quality",
    "bedtime_code",
    "screen_mid_hrs",
    "phone_bed_code",
    "exercise_days_mid",
    "deadlines_code",
    "workload_code",
    "performance_code",
]

FEATURE_LABELS = {
    "sleep_mid_hrs": "Sleep Duration",
    "sleep_quality": "Sleep Quality",
    "bedtime_code": "Bedtime",
    "screen_mid_hrs": "Screen Time",
    "phone_bed_code": "Bedtime Phone Usage",
    "exercise_days_mid": "Exercise Frequency",
    "deadlines_code": "Upcoming Deadlines",
    "workload_code": "Perceived Workload",
    "performance_code": "Exam Performance",
    "performance_missing": "Missing Exam History Flag"
}

def assessment_to_dataframe(input_data: AssessmentInput) -> pd.DataFrame:
    """
    Converts AssessmentInput into the exact 10-feature DataFrame expected by pipelines.
    Includes the performance_missing indicator.
    """
    row = {
        "sleep_mid_hrs": float(input_data.sleep_mid_hrs),
        "sleep_quality": int(input_data.sleep_quality),
        "bedtime_code": int(input_data.bedtime_code),
        "screen_mid_hrs": float(input_data.screen_mid_hrs),
        "phone_bed_code": int(input_data.phone_bed_code),
        "exercise_days_mid": float(input_data.exercise_days_mid),
        "deadlines_code": int(input_data.deadlines_code),
        "workload_code": int(input_data.workload_code),
        "performance_code": float(input_data.performance_code) if input_data.performance_code is not None else np.nan,
        "performance_missing": 1.0 if input_data.performance_code is None else 0.0,
    }
    return pd.DataFrame([row])

def standardize_for_regression(
    df_features: pd.DataFrame,
    means: Dict[str, float],
    stds: Dict[str, float],
    perf_median: float
) -> np.ndarray:
    """
    Applies manual median imputation and manual z-scoring (matching 02_bayesian_regression.py).
    """
    df_copy = df_features.copy()
    df_copy["performance_code"] = df_copy["performance_code"].fillna(perf_median)

    cols = list(df_copy.columns)
    z_matrix = np.column_stack([
        (df_copy[col].values - means[col]) / stds[col] for col in cols
    ])
    return z_matrix

def compute_stress_total(input_data: AssessmentInput) -> int:
    """
    Computes PSS-4 stress total:
    stress_total = pss1 + (6 - pss2) + (6 - pss3) + pss4
    Range: 4 to 20
    """
    p1 = input_data.pss1_no_control or 3
    p2 = input_data.pss2_confident or 3
    p3 = input_data.pss3_going_my_way or 3
    p4 = input_data.pss4_piling_up or 3
    
    return int(p1 + (6 - p2) + (6 - p3) + p4)
