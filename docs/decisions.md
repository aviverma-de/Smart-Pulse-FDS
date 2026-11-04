# SmartPulse — Architecture & Implementation Decisions

## 1. Context & Objectives
SmartPulse is a Student Stress & Burnout Monitoring Platform developed for a university Foundations of Data Science (FDS) course. The project analyzes survey data ($N = 132$) from students at a technical university to understand burnout patterns, evaluate risk through machine learning and Bayesian regression, and deliver supportive lifestyle recommendations.

---

## 2. Key Architecture Decisions

### Decision 1: Model Preservation & Serialization
- **Finding:** The original repository (`01_classifier.py` and `02_bayesian_regression.py`) trained models in memory without saving `.joblib` / `.pkl` artifacts.
- **Decision:** Rather than altering the original scripts, we created `backend/train_and_save.py` which runs the identical training pipeline (same seed = 42, same parameters, same preprocessing) and persists:
  1. `pipe_rf.joblib`: Random Forest classifier (500 trees, max_depth=4, min_samples_leaf=5).
  2. `pipe_lr.joblib`: L2-penalized Logistic Regression classifier.
  3. `reg_ols.joblib`: OLS Linear Regression model on standardized features.
  4. `bayes_params.json`: Posterior means and intercepts from PyMC NUTS sampling (`outputs/bayes_summary.csv`).
  5. `preprocessor_meta.json`: Standardized feature means, standard deviations (ddof=0), and median imputation value for `performance_code`.

### Decision 2: Feature Consistency Across Classifier & Regressor
- **Finding:** Both tasks in the repo use the exact same 9 lifestyle predictors + 1 missing indicator for exam performance:
  - `sleep_mid_hrs`, `sleep_quality`, `bedtime_code`, `screen_mid_hrs`, `phone_bed_code`, `exercise_days_mid`, `deadlines_code`, `workload_code`, `performance_code`, `performance_missing`.
- **Decision:** The assessment form directly collects these 9 questions and maps them into the exact 10 model features. An optional 4-item Perceived Stress Scale (PSS-4) is collected solely to compute `stress_total` for user context (not leaked to the models).

### Decision 3: Real Feature Attributions
- **Finding:** Rule 3 requires real feature attributions, not mocked contributions.
- **Decision:**
  - For Logistic Regression, we compute log-odds contributions: $\text{contrib}_j = \beta_j \cdot z_j$, where $z_j$ is the standardized value.
  - For Random Forest, we compute TreeSHAP (or TreeExplainer feature attributions using the `shap` package).
  - The UI explicitly states the attribution method used ("TreeSHAP Explainer" / "Logistic Regression Feature Contributions").

### Decision 4: Handling the Bayesian Linear Regression in the API
- **Finding:** Full PyMC sampling during HTTP request cycles is computationally heavy and unsuited for millisecond API response times. The README and `02_bayesian_regression.py` show that Bayesian posterior means mirror OLS with slight regularizing shrinkage toward zero.
- **Decision:** We implement score estimation using the exact Bayesian posterior means:
  $$\hat{y} = \mu_{\text{intercept}} + \sum_{j=1}^{10} \bar{\beta}_j \cdot z_j$$
  where $\mu_{\text{intercept}} = 14.9743$ and $\bar{\beta}_j$ are the exact posterior means from the 8,000 MCMC draws. We also compute credible intervals (94% HDI) based on posterior residual variance ($\sigma = 3.6934$).

### Decision 5: Non-Fabrication & Traceability
- **Decision:** Every displayed metric (sample size 132, mean burnout 14.98, mean stress 11.66, mean sleep 6.55, cross-validation metrics, p-values, odds ratios) is strictly loaded from the dataset, the exported artifacts, or the live model.

### Decision 6: Privacy by Design
- **Decision:** No user authentication or mandatory database storage is required. Predictions are processed in-memory. An optional SQLite table stores anonymous feedback only if the user explicitly opts in with consent.

### Decision 7: Design System
- **Theme:** Deep navy background (`#0B1220` to `#0F1B33`), subtle cyan/teal accents (`#14B8A6`, `#22D3EE`), glassmorphism cards (`bg-white/5` with `backdrop-blur-xl`), clear typography (Inter + Plus Jakarta Sans), WCAG AA contrast, and responsive mobile-first grid.
