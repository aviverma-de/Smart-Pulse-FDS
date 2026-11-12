"""
SmartPulse Backend Configuration
"""

import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATASET_PATH = BASE_DIR.parent / "smartpulse_models" / "SmartPulse_Cleaned.xlsx"
FROZEN_TEST_PATH = BASE_DIR / "retraining" / "frozen_test_set.json"
RETRAINING_DIR = BASE_DIR / "retraining"
REPORTS_DIR = BASE_DIR.parent / "docs" / "retraining-reports"

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
MIN_VALIDATION_N = int(os.getenv("MIN_VALIDATION_N", "30"))
MIN_RETRAIN_OUTCOMES = int(os.getenv("MIN_RETRAIN_OUTCOMES", "10"))
MIN_F1_MARGIN = float(os.getenv("MIN_F1_MARGIN", "0.01"))
MIN_MAE_MARGIN = float(os.getenv("MIN_MAE_MARGIN", "0.05"))

DISCLAIMER_TEXT = (
    "Disclaimer: This assessment is an academic statistical estimate derived from a student survey model "
    "(N = 132), not a medical or psychological diagnosis. Model predictions reflect observed statistical "
    "associations and must not be used as clinical evaluation. Recommendations provided are supportive "
    "lifestyle suggestions. If you are experiencing distress, please reach out to campus counseling or a qualified healthcare professional."
)

WHATIF_CAUTION = (
    "Caution: These are hypothetical model scenarios illustrating how the statistical model responds to varied inputs. "
    "Because the study design is cross-sectional, these changes reflect statistical associations, not causal proof that altering "
    "a specific habit will mechanically reduce burnout."
)

SEED = 42
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"
]
