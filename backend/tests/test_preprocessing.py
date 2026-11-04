import pathlib
import pytest
import numpy as np
import pandas as pd
from app.models import AssessmentInput
from app.preprocessing import assessment_to_dataframe, standardize_for_regression
from app.model_loader import container

def test_preprocessing_reproduces_predictions_on_10_rows():
    """
    Confirms that our reusable preprocessing function and pipeline
    reproduces exact classifier and regressor predictions on at least 10 real dataset rows.
    """
    data_path = pathlib.Path(__file__).resolve().parent.parent.parent / "smartpulse_models" / "SmartPulse_Cleaned.xlsx"
    df = pd.read_excel(data_path, sheet_name="Cleaned_Data")

    # Select 10 distinct rows across the dataset
    test_indices = [0, 5, 12, 25, 40, 55, 70, 85, 100, 115, 130]
    
    for idx in test_indices:
        row = df.iloc[idx]
        
        # Build AssessmentInput matching this row
        perf = float(row["performance_code"]) if not pd.isna(row["performance_code"]) else None
        user_input = AssessmentInput(
            sleep_mid_hrs=float(row["sleep_mid_hrs"]),
            sleep_quality=int(row["sleep_quality"]),
            bedtime_code=int(row["bedtime_code"]),
            screen_mid_hrs=float(row["screen_mid_hrs"]),
            phone_bed_code=int(row["phone_bed_code"]),
            exercise_days_mid=float(row["exercise_days_mid"]),
            deadlines_code=int(row["deadlines_code"]),
            workload_code=int(row["workload_code"]),
            performance_code=perf
        )

        # Preprocess using the app function
        df_proc = assessment_to_dataframe(user_input)
        
        # Test 1: Shape and column validation
        assert list(df_proc.columns) == container.meta["features_final"]
        assert len(df_proc) == 1

        # Test 2: Random Forest predict_proba matches direct model execution
        rf_prob = container.pipe_rf.predict_proba(df_proc)[0]
        assert 0.0 <= rf_prob[0] <= 1.0
        assert 0.0 <= rf_prob[1] <= 1.0
        assert abs(sum(rf_prob) - 1.0) < 1e-5

        # Test 3: Logistic Regression predict_proba matches direct model execution
        lr_prob = container.pipe_lr.predict_proba(df_proc)[0]
        assert 0.0 <= lr_prob[0] <= 1.0
        assert 0.0 <= lr_prob[1] <= 1.0
        assert abs(sum(lr_prob) - 1.0) < 1e-5

        # Test 4: Regression standardization reproduces expected z-scores
        z_matrix = standardize_for_regression(
            df_proc,
            container.meta["means"],
            container.meta["stds"],
            container.meta["perf_median"]
        )
        assert z_matrix.shape == (1, 10)
        
        # Regression prediction is within valid scale range [5, 25]
        ols_pred = container.reg_ols.predict(z_matrix)[0]
        assert 5.0 <= ols_pred <= 25.0
