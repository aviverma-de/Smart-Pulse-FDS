"""
Frozen Held-Out Test Set Management
Ensures that the 20% held-out test set (n=27, stratified on burnout_high, seed=42)
is completely locked and NEVER contaminated by training, tuning, or retraining.
"""

import json
import pathlib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
try:
    from app import config
except ImportError:
    try:
        from backend.app import config
    except ImportError:
        from ..app import config

FEATURES = [
    "sleep_mid_hrs", "sleep_quality", "bedtime_code",
    "screen_mid_hrs", "phone_bed_code",
    "exercise_days_mid", "deadlines_code",
    "workload_code", "performance_code"
]

def find_dataset():
    candidates = [
        config.DATASET_PATH,
        config.BASE_DIR.parent / "CleanedData" / "SmartPulse_Cleaned (1).xlsx",
        pathlib.Path("smartpulse_models/SmartPulse_Cleaned.xlsx"),
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise FileNotFoundError("SmartPulse_Cleaned.xlsx not found.")

def init_frozen_test_set():
    config.RETRAINING_DIR.mkdir(parents=True, exist_ok=True)
    frozen_path = config.FROZEN_TEST_PATH
    if frozen_path.exists():
        with open(frozen_path, "r") as f:
            return json.load(f)

    data_path = find_dataset()
    df = pd.read_excel(data_path, sheet_name="Cleaned_Data")
    
    # 80/20 train/test split with stratification on burnout_high and seed=42
    train_df, test_df = train_test_split(
        df,
        test_size=0.20,
        random_state=config.SEED,
        stratify=df["burnout_high"]
    )

    test_records = test_df.to_dict(orient="records")
    train_records = train_df.to_dict(orient="records")

    payload = {
        "seed": config.SEED,
        "n_total": len(df),
        "n_train": len(train_df),
        "n_test": len(test_df),
        "test_indices": test_df.index.tolist(),
        "train_indices": train_df.index.tolist(),
        "test_data": test_records,
        "train_data": train_records
    }

    # Custom serializer for numpy types
    def default_serializer(o):
        if isinstance(o, (np.integer, np.int64)):
            return int(o)
        if isinstance(o, (np.floating, np.float64)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if pd.isna(o):
            return None
        return str(o)

    with open(frozen_path, "w") as f:
        json.dump(payload, f, default=default_serializer, indent=2)

    return payload

def load_frozen_test_df() -> pd.DataFrame:
    data = init_frozen_test_set()
    return pd.DataFrame(data["test_data"])

def load_initial_train_df() -> pd.DataFrame:
    data = init_frozen_test_set()
    return pd.DataFrame(data["train_data"])

if __name__ == "__main__":
    payload = init_frozen_test_set()
    print(f"Frozen test set created: {payload['n_test']} test rows, {payload['n_train']} train rows.")
