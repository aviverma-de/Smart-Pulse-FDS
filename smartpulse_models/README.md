# SmartPulse Models — Burnout Classifier & Bayesian Regression

> **Course:** Foundations of Data Science  
> **Project:** SmartPulse: Student Lifestyle, Sleep Dynamics, and Academic Burnout Forecasting System  
> **Dataset:** `SmartPulse_Cleaned.xlsx` (Sheet: `Cleaned_Data`, $N = 132$ respondents, 51 columns)

---

## Executive Summary

This repository contains two focused statistical learning models analyzing how student lifestyle habits relate to academic burnout:
1. **Task 1 — Burnout Risk Classifier (`01_classifier.py`):** Predicts binary high burnout (`burnout_high`, sample median cutoff $\ge 15$) using L2-penalized Logistic Regression and Random Forest, benchmarked against a Dummy baseline.
2. **Task 2 — Bayesian Linear Regression (`02_bayesian_regression.py`):** Models continuous burnout (`burnout_total`, 5–25 scale) using PyMC (version 6.4.0) with NUTS sampling, weakly informative vs. literature-informed prior sensitivity analysis, and OLS validation.

No demographic or leakage columns were used as predictors. Preprocessing (median imputation for exam performance and standard scaling) is strictly self-contained within cross-validation folds.

---

## Environment & Library Compatibility

- **Python Version:** 3.12+ (tested on Python 3.12.9)
- **PyMC Version:** 6.4.0
- **PyTensor Version:** 3.3.7
- **ArviZ Version:** 1.3.0
- **scikit-learn:** 1.6+
- **Core dependencies:** `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `openpyxl`

### Key PyMC 6.4.0 & ArviZ 1.3.0 Compatibility Updates Applied:
1. **Prior Predictive API:** Switched `pm.sample_prior_predictive(samples=500)` to `pm.sample_prior_predictive(draws=500)`.
2. **DataTree Integration:** Adapted posterior and prior predictive value extraction to xarray `DataTree` structures (`.prior_predictive["y"].values` and `.posterior_predictive["y"].values`).
3. **ArviZ CI Parameter Updates:** Replaced legacy `hdi_prob=0.94` with `ci_prob=0.94, ci_kind="hdi"` in `az.summary()` and `prob=0.94` in `az.hdi()`.
4. **PyTensor Windows Cache Configuration:** Configured `PYTENSOR_FLAGS="base_compiledir=..."` to avoid sandbox and permission issues on Windows.
5. **Console Encoding Safety:** Handled Windows `cp1252` terminal encoding and disabled interactive Rich progress bars during automated sampling to eliminate unicode character map crashes (`\u2009`).

---

## How to Run

Both scripts are self-contained and runnable top to bottom with fixed random seeds (`42`):

```bash
# Navigate to the models directory
cd smartpulse_models

# Run Task 1: Classifier (takes ~15-20 seconds)
python 01_classifier.py

# Run Task 2: Bayesian Regression (takes ~45-60 seconds)
python 02_bayesian_regression.py
```

All figures (PNG, 150 DPI), metric summaries, and prediction outputs are written to `smartpulse_models/outputs/`.

---

## Feature Set & Leakage Prevention

The model uses **only** the 9 specified lifestyle habit predictors, plus an indicator flag for students who had not taken an exam yet:

| Feature | Description | Scale / Type | Handling |
| :--- | :--- | :--- | :--- |
| `sleep_mid_hrs` | Sleep duration range midpoint | Hours (continuous) | Scaled inside pipeline |
| `sleep_quality` | Self-rated sleep quality | 1 to 5 | Scaled inside pipeline |
| `bedtime_code` | Typical bedtime (higher = later) | 1 to 4 | Scaled inside pipeline |
| `screen_mid_hrs` | Daily screen time midpoint | Hours (continuous) | Scaled inside pipeline |
| `phone_bed_code` | Phone use before sleep | 1 to 4 | Scaled inside pipeline |
| `exercise_days_mid` | Exercise days per week midpoint | Days (continuous) | Scaled inside pipeline |
| `deadlines_code` | Academic deadline density | 1 to 4 | Scaled inside pipeline |
| `workload_code` | Perceived workload pressure | 1 to 4 | Scaled inside pipeline |
| `performance_code` | Recent exam vs expectation | 1 to 5 (12 missing) | Median imputed inside pipeline |
| `performance_missing` | Flag for respondents with no exam yet | 0 or 1 | Scaled inside pipeline |

**Strict Exclusion Checklist:**
- Excluded outcomes: `burnout_total`, `burnout_high`, `burnout_group`, and item scores `bo1`–`bo5`.
- Excluded related stress measures: `stress_total`, `stress_start`, `stress_mid`, `stress_now`, `pss1`–`pss4`.
- Excluded group demographics: `gender_analysis`, `year_group`, `stream_group`, `residence_group` (retained in `oof_predictions.csv` for downstream auditing only).

---

## Task 1: Classifier Results (`burnout_high`)

Evaluated via **RepeatedStratifiedKFold (5 folds × 10 repeats = 50 folds)**. Class balance: 71 High (53.8%) vs 61 Low (46.2%).

### Performance Summary (Mean ± Standard Deviation Across 50 Folds)

| Model | Accuracy | Precision | Recall (High) | F1 Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dummy (Most Frequent)** | $0.538 \pm 0.012$ | $0.538 \pm 0.012$ | $1.000 \pm 0.000$ | $0.699 \pm 0.010$ | $0.500 \pm 0.000$ |
| **Logistic Regression (L2)** | $0.570 \pm 0.086$ | $0.595 \pm 0.076$ | $0.636 \pm 0.131$ | $0.610 \pm 0.089$ | $0.616 \pm 0.093$ |
| **Random Forest (500 trees)** | **$0.607 \pm 0.084$** | **$0.627 \pm 0.083$** | **$0.690 \pm 0.147$** | **$0.649 \pm 0.089$** | **$0.635 \pm 0.094$** |

*Note: In screening student burnout, Recall (High) is the primary operational objective (minimizing missed at-risk students).*

### Logistic Regression Odds Ratios (Standardized Features, 94% CI)

| Feature | Standardized $\beta$ | SE | Odds Ratio | 94% CI Lower | 94% CI Upper |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `workload_code` | +0.5321 | 0.2093 | **1.7025** | 1.1484 | 2.5240 |
| `bedtime_code` | +0.3669 | 0.2314 | **1.4433** | 0.9340 | 2.2304 |
| `phone_bed_code` | +0.3496 | 0.2109 | **1.4186** | 0.9542 | 2.1090 |
| `exercise_days_mid` | +0.3290 | 0.2111 | **1.3896** | 0.9343 | 2.0669 |
| `sleep_mid_hrs` | +0.1479 | 0.2061 | **1.1594** | 0.7869 | 1.7084 |
| `sleep_quality` | +0.1422 | 0.2219 | **1.1528** | 0.7595 | 1.7498 |
| `deadlines_code` | +0.0809 | 0.2017 | **1.0843** | 0.7419 | 1.5845 |
| `screen_mid_hrs` | -0.1452 | 0.2104 | **0.8649** | 0.5822 | 1.2848 |
| `performance_missing` | -0.1886 | 0.2062 | **0.8281** | 0.5619 | 1.2206 |
| `performance_code` | -0.2885 | 0.1980 | **0.7494** | 0.5164 | 1.0875 |

---

## Task 2: Bayesian Linear Regression Results (`burnout_total`)

- **Prior Specification:** $\text{Intercept} \sim \text{Normal}(15, 5)$, each $\beta_j \sim \text{Normal}(0, 2)$, $\sigma \sim \text{HalfNormal}(5)$.
- **Sampling:** NUTS (4 chains, 1,000 warmup/tune draws, 2,000 posterior draws per chain = 8,000 draws total, target accept = 0.90, seed = 42).
- **MCMC Convergence Diagnostics:**
  - Max $\hat{R} = 1.0018$ (All parameters $\le 1.01$).
  - Divergent Transitions = 0 (No divergences).
  - Effective Sample Size: Bulk ESS $\ge 9,255$, Tail ESS $\ge 5,609$.
  - Diagnostics **PASSED**.

### Posterior Parameter Summary (Standardized Predictors, 94% HDI)

| Parameter | Posterior Mean | Posterior SD | 94% HDI [3%, 97%] |
| :--- | :---: | :---: | :---: |
| `intercept` | 14.9743 | 0.3193 | [14.3681, 15.5574] |
| `workload_code` | **+1.1783** | 0.3341 | [0.5680, 1.8139] |
| `phone_bed_code` | **+0.9138** | 0.3514 | [0.2544, 1.5698] |
| `performance_code` | **-0.7073** | 0.3265 | [-1.3289, -0.0880] |
| `exercise_days_mid` | +0.5376 | 0.3501 | [-0.1178, 1.1967] |
| `bedtime_code` | +0.5101 | 0.3801 | [-0.1880, 1.2499] |
| `sleep_quality` | +0.3209 | 0.3735 | [-0.4058, 0.9975] |
| `performance_missing` | +0.2222 | 0.3430 | [-0.4247, 0.8579] |
| `deadlines_code` | +0.1582 | 0.3330 | [-0.4745, 0.7655] |
| `sleep_mid_hrs` | +0.1457 | 0.3522 | [-0.4960, 0.8137] |
| `screen_mid_hrs` | -0.1331 | 0.3503 | [-0.8165, 0.5031] |
| $\sigma$ (residual SD) | 3.6934 | 0.2396 | [3.2628, 4.1562] |

### Sleep Coefficient Analysis & Original Units Interpretation

- **Posterior probability $P(\beta_{\text{sleep}} < 0)$:** **$33.9\%$** under weakly informative priors.
- **Original Units Interpretation:**
  - $1 \text{ SD}$ of `sleep_mid_hrs` is $1.08\text{ hours}$.
  - One extra hour of sleep corresponds to a **$+0.13$ point change** in `burnout_total` ($94\%\text{ HDI } [-0.46, +0.75]$ points).
  - Because the HDI comfortably spans zero, self-reported sleep duration shows no isolated association with burnout once perceived workload and phone habits are held constant.
  - In comparison, $1 \text{ unit increase}$ on the 1–4 perceived workload scale changes `burnout_total` by **$+2.08$ points** ($94\%\text{ HDI } [+1.00, +3.21]$ points).

### Prior Sensitivity Analysis (Sleep Coefficient)

| Prior Specification | Prior Form | Posterior Mean | Posterior SD | 94% HDI |
| :--- | :--- | :---: | :---: | :---: |
| **Weakly Informative** | $\text{Normal}(0, 2)$ | +0.146 | 0.352 | [-0.496, 0.814] |
| **Literature-Informed** | $\text{Normal}(-0.5, 0.5)$ | **-0.072** | 0.294 | [-0.635, 0.471] |

**Data vs. Prior Influence:**
The informative prior pulls the posterior mean downward by $\mathbf{-0.218\text{ points}}$ and narrows the credible interval. With a modest sample ($N=132$), the likelihood does not overwhelm the prior; hence, empirical conclusions about sleep duration are sensitive to prior assumptions.

### OLS Sanity Check Comparison

| Feature | Bayesian Posterior Mean | OLS Coefficient | Difference |
| :--- | :---: | :---: | :---: |
| `workload_code` | 1.178 | 1.211 | -0.033 |
| `phone_bed_code` | 0.914 | 0.948 | -0.034 |
| `performance_code` | -0.707 | -0.722 | +0.014 |
| `exercise_days_mid` | 0.538 | 0.560 | -0.023 |
| `bedtime_code` | 0.510 | 0.530 | -0.020 |
| `sleep_quality` | 0.321 | 0.343 | -0.022 |
| `performance_missing`| 0.222 | 0.233 | -0.011 |
| `deadlines_code` | 0.158 | 0.167 | -0.008 |
| `sleep_mid_hrs` | 0.146 | 0.161 | -0.016 |
| `screen_mid_hrs` | -0.133 | -0.154 | +0.021 |
| `intercept` | 14.974 | 14.977 | -0.003 |

*Conclusion:* Posterior means closely match OLS estimates with slight shrinkage towards zero, confirming that the MCMC sampler converged to the exact likelihood surface with appropriate regularization.

---

## Generated Artifacts in `outputs/`

```
smartpulse_models/outputs/
├── metrics_table.csv                  # RepeatedStratifiedKFold metrics (Dummy, LogReg, RF)
├── oof_predictions.csv                # Out-of-fold predicted probabilities with audit groups
├── bayes_summary.csv                  # Posterior summary (mean, SD, 94% HDI)
├── confusion_matrices.png             # Out-of-fold confusion matrices (threshold = 0.5)
├── roc_curves.png                     # Out-of-fold ROC curves with AUC annotations
├── precision_recall_vs_threshold.png  # Precision & Recall tradeoff curves
├── rf_permutation_importance.png      # RF held-out fold permutation importance
├── lr_odds_ratios.png                 # Logistic regression odds ratios with 94% CI
├── bayes_prior_predictive.png         # Prior predictive simulated distributions
├── bayes_trace_plot.png               # 4-chain MCMC trace plots
├── bayes_posterior_predictive.png     # Observed vs posterior simulated data
├── bayes_forest_plot.png              # Standardized posterior coefficient forest plot
└── bayes_prior_sensitivity.png        # Weak vs informative prior comparison
```

---

## Honest Methodological Discussion & Limitations

1. **Modest Predictive Power:** ROC-AUC values ($\sim 0.61$ to $0.64$) reflect realistic behavioral survey limits. Isolated daily habits do not determine student burnout in isolation.
2. **Cross-Sectional Design:** All measures were captured simultaneously in a single Google Form survey. Temporal ordering cannot be established, and **correlation does not imply causation**.
3. **Sample Characteristics & Convenience Sampling:** The respondent pool ($N=132$) consists predominantly of second-year engineering hostel students. Generalization to other academic years, university cultures, or broader youth populations is not warranted without external replication.
4. **Self-Reported Biases:** Habit midpoints and burnout scores rely on self-reported ordinal scales, which are susceptible to recall inaccuracies and mood-congruent response patterns.
5. **Ethical Use:** These models are designed solely for population-level academic insight in a university data science course; they **must not** be used for individual automated diagnostic or clinical screening.
