"""
SmartPulse Model & Artifact Loader
Loads all serialized pipelines and JSON artifacts once at server startup.
"""

import json
import joblib
import pandas as pd
from typing import Dict, Any, Optional
from . import config

class ModelContainer:
    active_version: str = "v1.0"
    pipe_rf: Any = None
    pipe_lr: Any = None
    reg_ols: Any = None
    meta: Dict[str, Any] = {}
    bayes_params: Dict[str, Any] = {}
    overview_stats: Dict[str, Any] = {}
    hypothesis_tests: list = []
    model_performance: Dict[str, Any] = {}
    df_raw: Optional[pd.DataFrame] = None

container = ModelContainer()

def load_all_artifacts():
    print("Loading SmartPulse models and artifacts into memory...")
    from .db import init_db, SessionLocal, ModelVersion
    init_db()
    
    # Check active model version from database
    db = SessionLocal()
    try:
        active_ver = db.query(ModelVersion).filter_by(is_active=True).first()
        if active_ver:
            container.active_version = active_ver.version
    except Exception as e:
        print("Database model version check error:", e)
    finally:
        db.close()
    
    # 1. Load trained sklearn pipelines
    container.pipe_rf = joblib.load(config.SAVED_MODELS_DIR / "pipe_rf.joblib")
    container.pipe_lr = joblib.load(config.SAVED_MODELS_DIR / "pipe_lr.joblib")
    container.reg_ols = joblib.load(config.SAVED_MODELS_DIR / "reg_ols.joblib")

    # 2. Load preprocessor metadata
    with open(config.SAVED_MODELS_DIR / "preprocessor_meta.json", "r") as f:
        container.meta = json.load(f)

    # 3. Load Bayesian parameters
    with open(config.SAVED_MODELS_DIR / "bayes_params.json", "r") as f:
        container.bayes_params = json.load(f)

    # 4. Load JSON artifacts
    with open(config.ARTIFACTS_DIR / "overview_stats.json", "r") as f:
        container.overview_stats = json.load(f)

    with open(config.ARTIFACTS_DIR / "hypothesis_tests.json", "r") as f:
        container.hypothesis_tests = json.load(f)

    with open(config.ARTIFACTS_DIR / "model_performance.json", "r") as f:
        container.model_performance = json.load(f)

    # 5. Load raw dataset for live percentile computations
    if config.DATASET_PATH.exists():
        container.df_raw = pd.read_excel(config.DATASET_PATH, sheet_name="Cleaned_Data")
    else:
        print("Warning: Raw dataset path not found at:", config.DATASET_PATH)

    print("Successfully loaded all models, metadata, and artifacts!")
