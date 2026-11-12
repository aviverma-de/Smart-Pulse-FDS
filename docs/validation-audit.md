# SmartPulse Validation & Retraining Audit (v1.0)
- Target Definition: Continuous `burnout_total` is sum of 5 items (`bo1_phys_exhausted` .. `bo5_less_interest`), each scored 1-5 (Never=1 to Always=5, range 5-25).
- Category Thresholds: Binary `burnout_high` = High if `burnout_total >= 15` (sample median), else Low (< 15).
- Model Inputs (10): `sleep_mid_hrs`, `sleep_quality`, `bedtime_code`, `screen_mid_hrs`, `phone_bed_code`, `exercise_days_mid`, `deadlines_code`, `workload_code`, `performance_code`, `performance_missing`. PSS-4 items are excluded from inputs.
- Target Leakage Check: Verified clean. Explicit assertion in training scripts excludes all outcome items (`bo1`-`bo5`, `burnout_*`) and `pss*` from input features. Zero leakage risk.
- Baseline Model Registration: v1.0 registered for `pipe_rf` (RF 500 trees classifier), `pipe_lr` (L2 Logistic Regression), `reg_ols` (Linear Regression), and Bayesian regression parameters.
- Train/Test Split: Baseline used RepeatedStratifiedKFold (5 folds x 10 repeats, random_state=42). A frozen held-out test set (20%, n=27, stratified on `burnout_high`, random_state=42) is locked from original N=132 and never trained on.
- Outcome Instrument Reuse: Verified-outcome form reuses the exact 5-item burnout battery (`bo1`-`bo5`), identical 1-5 scale, identical sum (5-25), and threshold (>=15 is High, <15 is Low). No new scale invented.