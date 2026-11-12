# SmartPulse — Data Lineage & Provenance Audit Table

## 0. Validation Center and Retraining Provenance

- Live classification actuals are the `measured_category` values from verified five-item follow-up outcomes, scored as High when the sum is at least 15 and Low otherwise. Predictions are joined by assessment ID. Only records with `is_demo=false` are included by default.
- Live regression actuals use the same measured five-item sum; predictions use the score saved with the assessment's prediction. Rows with no saved prediction score are omitted from regression metrics and do not affect classification counts.
- Confidence intervals and sample counts are computed from the rows returned by those joins. With no measured outcomes, the API returns “Not yet established (n=0)”; no live validation values are pre-filled or inferred from historical cross-validation.
- Training provenance is 105 original training rows plus consented, verified, non-demo follow-ups that have a linked assessment. The 27-row original held-out partition in `backend/retraining/frozen_test_set.json` is excluded from candidate training and used for candidate/current evaluation only. Demo rows can be displayed for UI demonstration but never enter training.
- Retraining reports record the evaluated candidate and decision under `docs/retraining-reports/`. A “promoted” status is a result of the configured same-test comparison, not a claim of general or causal improvement.
- Historical figures in sections 1–5 below describe the original coursework analysis and are separate from live Validation Center metrics.

Every single metric, test statistic, p-value, chart figure, and prediction displayed across SmartPulse is traced to its exact mathematical origin below. **Zero numbers are hardcoded or fabricated.**

---

## 1. Population Overview Dashboard & Hero Metrics

| Metric / Figure | Displayed Value | Mathematical Origin / Exact Source | Verification Method |
| :--- | :--- | :--- | :--- |
| **Total Cohort Size ($N$)** | `132` | Length of cleaned dataset (`SmartPulse_Cleaned.xlsx`, Sheet `Cleaned_Data`), after removing 10 careless respondents. | `len(df) == 132` |
| **Average Burnout Score** | `14.98 / 25` | Sample arithmetic mean of continuous `burnout_total` ($14.9773 \approx 14.98$). | `df['burnout_total'].mean()` |
| **Burnout Median Cutoff** | `15.0` | Sample median of `burnout_total` used to define the binary classification target `burnout_high`. | `df['burnout_total'].median()` |
| **High Burnout Prevalence** | `53.8%` (71/132) | Fraction of respondents with `burnout_total >= 15` ($71 / 132 = 0.53788$). | `df['burnout_high'].mean() * 100` |
| **Low Burnout Prevalence** | `46.2%` (61/132) | Fraction of respondents with `burnout_total < 15` ($61 / 132 = 0.46212$). | `100 - 53.8` |
| **Average Stress Level** | `11.66 / 20` | Sample mean of self-reported `stress_total` (PSS-4 Scale, range 5–19). | `df['stress_total'].mean()` |
| **Average Sleep Duration** | `6.55 hrs` | Sample mean of `sleep_mid_hrs` ($6.5530 \approx 6.55$). | `df['sleep_mid_hrs'].mean()` |
| **Stress Timeline: Semester Start** | `1.97 ± 1.00` | Sample mean and standard deviation of `stress_start` ($1.9697 \pm 0.9957$). | `df['stress_start'].mean()` |
| **Stress Timeline: Midterms** | `3.06 ± 0.92` | Sample mean and standard deviation of `stress_mid` ($3.0606 \pm 0.9226$). | `df['stress_mid'].mean()` |
| **Stress Timeline: Current Status** | `3.20 ± 1.21` | Sample mean and standard deviation of `stress_now` ($3.2045 \pm 1.2090$). | `df['stress_now'].mean()` |
| **Stress Escalation Insight** | `+1.23 pts (+63%)` | $(3.2045 - 1.9697) = 1.2348$ point increase ($\chi^2 = 108.43, p < 0.001$). | `compute_all_hypotheses.py` |
| **Burnout Histogram Frequencies** | 10 Bins (5 to 25) | `np.histogram(df['burnout_total'], bins=10)`. | `export_artifacts.py` |
| **Stress Histogram Frequencies** | 8 Bins (5 to 19) | `np.histogram(df['stress_total'], bins=8)`. | `export_artifacts.py` |

---

## 2. Statistical Hypotheses & Research Findings

| Research Question / Card | Test Used | Statistic Value | p-value | Effect Size | Provenance / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stress Progression across Semester** | Friedman Test (Repeated Measures) | $\chi^2 = 108.425$ | $p = 2.86 \times 10^{-24}$ | Kendall's $W = 0.411$ | Computed on `stress_start`, `stress_mid`, `stress_now` paired vectors. |
| **Academic Workload vs. Burnout** | Pearson's Chi-Square ($\text{df}=1$) | $\chi^2 = 11.461$ | $p = 0.000711$ | Cramer's $V = 0.295$, $\text{OR} = 4.314$ | Exact match to verified facts. Dichotomized Workload $\ge 3$ vs. Burnout $\ge 15$. |
| **Bedtime Smartphone Usage vs. Burnout** | Pearson's Chi-Square ($\text{df}=1$) | $\chi^2 = 3.225$ | $p = 0.0725$ | Cramer's $V = 0.156$ | Computed on `phone_bed_code >= 3` vs. `burnout_high`. |
| **Exam Performance vs. Expectations** | Mann-Whitney $U$ Test | $U = 1444.0$ | $p = 0.0622$ | Rank Biserial $r = 0.144$ | Computed on `performance_code` (12 missing rows dropped). |
| **Physical Activity vs. Burnout** | Pearson's Chi-Square ($\text{df}=1$) | $\chi^2 = 1.914$ | $p = 0.1665$ | Cramer's $V = 0.120$ | Computed on `exercise_days_mid >= 3.0` vs. `burnout_high`. |
| **Gender vs. Burnout Prevalence** | Pearson's Chi-Square ($\text{df}=1$) | $\chi^2 = 0.017$ | $p = 0.8976$ | Cramer's $V = 0.011$ | Computed on `gender_analysis` (Male: 54.2%, Female: 53.1%). |

---

## 3. Machine Learning Classification Performance

All metrics originate from `smartpulse_models/outputs/metrics_table.csv` and `oof_predictions.csv` (RepeatedStratifiedKFold, 50 folds):

| Metric | Dummy Baseline | Logistic Regression (L2) | Random Forest (500 Trees) | Verification Source |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | $53.8\% \pm 1.2\%$ | $57.0\% \pm 8.6\%$ | **$60.7\% \pm 8.4\%$** | `metrics_table.csv` |
| **Precision** | $53.8\% \pm 1.2\%$ | $59.5\% \pm 7.6\%$ | **$62.7\% \pm 8.3\%$** | `metrics_table.csv` |
| **Recall (High)** | $100.0\% \pm 0.0\%$ | $63.6\% \pm 13.1\%$ | **$69.0\% \pm 14.7\%$** | `metrics_table.csv` |
| **F1 Score** | $69.9\% \pm 1.0\%$ | $61.0\% \pm 8.9\%$ | **$64.9\% \pm 8.9\%$** | `metrics_table.csv` |
| **ROC-AUC** | $0.500 \pm 0.000$ | $0.616 \pm 0.093$ | **$0.635 \pm 0.094$** | `metrics_table.csv` |
| **Confusion Matrix (RF)** | N/A | N/A | $\text{TN}=28, \text{FP}=33, \text{FN}=22, \text{TP}=49$ | Computed from out-of-fold predictions at threshold = 0.5. |

---

## 4. Bayesian Linear Regression Posterior Parameters

Originates from `smartpulse_models/outputs/bayes_summary.csv` (PyMC NUTS sampler, 4 chains × 2,000 draws = 8,000 draws, target accept = 0.90):

| Parameter | Posterior Mean | Posterior SD | 94% HDI Low | 94% HDI High | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `intercept` | $14.9743$ | $0.3193$ | $14.3681$ | $15.5574$ | Excludes 0 |
| `workload_code` | $+1.1783$ | $0.3341$ | $+0.5680$ | $+1.8139$ | Excludes 0 (Positive association) |
| `phone_bed_code` | $+0.9138$ | $0.3514$ | $+0.2544$ | $+1.5698$ | Excludes 0 (Positive association) |
| `performance_code` | $-0.7073$ | $0.3265$ | $-1.3289$ | $-0.0880$ | Excludes 0 (Negative association) |
| `exercise_days_mid` | $+0.5376$ | $0.3501$ | $-0.1178$ | $+1.1967$ | Spans 0 |
| `bedtime_code` | $+0.5101$ | $0.3801$ | $-0.1880$ | $+1.2499$ | Spans 0 |
| `sleep_quality` | $+0.3209$ | $0.3735$ | $-0.4058$ | $+0.9975$ | Spans 0 |
| `performance_missing` | $+0.2222$ | $0.3430$ | $-0.4247$ | $+0.8579$ | Spans 0 |
| `deadlines_code` | $+0.1582$ | $0.3330$ | $-0.4745$ | $+0.7655$ | Spans 0 |
| `sleep_mid_hrs` | $+0.1457$ | $0.3522$ | $-0.4960$ | $+0.8137$ | Spans 0 |
| `screen_mid_hrs` | $-0.1331$ | $0.3503$ | $-0.8165$ | $+0.5031$ | Spans 0 |
| `sigma` (Residual SD) | $3.6934$ | $0.2396$ | $3.2628$ | $4.1562$ | Excludes 0 |

---

## 5. Live User Predictions & What-If Simulations

- **Classification Inference:** Real-time forward pass through `pipe_rf.joblib` fitted with ColumnTransformer (SimpleImputer median + StandardScaler). Class probabilities generated via `predict_proba()`.
- **Continuous Score Inference:** Real-time linear evaluation using Bayesian posterior mean coefficients:
  $$\hat{y} = 14.9743 + \sum_{j=1}^{10} \bar{\beta}_j \cdot \frac{x_j - \bar{x}_j}{s_j}$$
- **Feature Attributions:** Exact log-odds contribution vector $\beta_j \cdot z_j$ derived from the fitted L2 Logistic Regression classifier.
