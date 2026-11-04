# SmartPulse — Repository Discovery & Audit Findings

## 1. Inventory of Files

### Data Files
- `SmartPulse_Cleaned (1).xlsx` and `smartpulse_models/SmartPulse_Cleaned.xlsx`
  - 132 rows × 51 columns (Sheet: `Cleaned_Data`)
  - 10 respondents were removed in the cleaning phase as careless responses (identical answers on all 9 stress/burnout Likert items).
  - Only one predictor has missing values: `performance_code` with 12 missing entries corresponding to respondents who selected *"I have not had any exam yet"*.

### Source Scripts
- `smartpulse_models/01_classifier.py`:
  - Target: `burnout_high` (binary, $1$ if `burnout_total` $\ge 15$, $0$ otherwise). Class distribution: 71 High (53.8%), 61 Low (46.2%).
  - Evaluates Dummy baseline, Logistic Regression (L2 penalty, C=1.0), and Random Forest (500 trees, max_depth=4, min_samples_leaf=5).
  - 50 folds cross-validation: `RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=42)`.
  - All preprocessing inside `sklearn.pipeline.Pipeline`:
    - `SimpleImputer(strategy="median")`
    - `StandardScaler()`
- `smartpulse_models/02_bayesian_regression.py`:
  - Target: `burnout_total` (continuous scale 5–25, mean = 14.977, std = 3.980).
  - PyMC NUTS sampler (4 chains × 2,000 draws, 1,000 warmup draws = 8,000 posterior draws total).
  - Prior setup: Intercept $\sim \text{Normal}(15, 5)$, $\beta_j \sim \text{Normal}(0, 2)$, $\sigma \sim \text{HalfNormal}(5)$.
  - Max $\hat{R} = 1.0018$, 0 divergences, min Bulk ESS $\ge 9,255$.
  - Prior sensitivity analysis: Evaluated weakly informative prior $\text{Normal}(0, 2)$ vs. literature-informed $\text{Normal}(-0.5, 0.5)$ for `sleep_mid_hrs`.

### Pre-computed Outputs
- `smartpulse_models/outputs/metrics_table.csv`: Cross-validation scores (mean ± SD).
- `smartpulse_models/outputs/bayes_summary.csv`: Posterior parameter distributions (mean, SD, 94% HDI).
- `smartpulse_models/outputs/oof_predictions.csv`: Out-of-fold predicted probabilities for all 132 students.

---

## 2. Feature Definitions & Survey Answer Mappings

Both models use the identical set of 9 lifestyle features + 1 missing indicator (10 total):

| Feature Name | Question / Concept | Survey Coding & Values | Model Preprocessing |
| :--- | :--- | :--- | :--- |
| `sleep_mid_hrs` | Sleep duration per night | `<5 hrs`: 4.5, `5-6 hrs`: 5.5, `6-7 hrs`: 6.5, `7-8 hrs`: 7.5, `8-9 hrs`: 8.5, `>9 hrs`: 9.5 | Standard scaled |
| `sleep_quality` | Subjective sleep quality | 1: Very poor, 2: Poor, 3: Average, 4: Good, 5: Excellent | Standard scaled |
| `bedtime_code` | Typical sleep bedtime | 1: Before 11 PM, 2: 11 PM - 1 AM, 3: 1 AM - 3 AM, 4: After 3 AM | Standard scaled |
| `screen_mid_hrs` | Daily screen time | `<2 hrs`: 1.0, `2-4 hrs`: 3.0, `4-6 hrs`: 5.0, `6-8 hrs`: 7.0, `>8 hrs`: 9.0 | Standard scaled |
| `phone_bed_code` | Phone use in bed | 1: Never, 2: Sometimes, 3: Usually, 4: Always | Standard scaled |
| `exercise_days_mid` | Physical activity days/wk | 0 days: 0.0, 1-2 days: 1.5, 3-4 days: 3.5, 5+ days: 5.5 | Standard scaled |
| `deadlines_code` | Academic deadline density | 1: 0 to 2, 2: 3 to 5, 3: 6 to 8, 4: 9 or more | Standard scaled |
| `workload_code` | Perceived study workload | 1: Very light, 2: Manageable, 3: Heavy, 4: Overwhelming | Standard scaled |
| `performance_code` | Recent exam vs expectations | 1: Much below, 2: Slightly below, 3: As expected, 4: Slightly above, 5: Much above | Median imputed (median=2.0) + Scaled |
| `performance_missing` | No exam taken indicator | 1.0 if respondent selected "Haven't taken any exam yet", 0.0 otherwise | Standard scaled |

---

## 3. Verified Statistical Tests (Computed Directly from $N = 132$ Data)

1. **Workload vs. Burnout Risk:**
   - Contingency table (Workload $\ge 3$ vs. Burnout High): $\chi^2 = 11.4610$, $p = 0.000711$, Cramer's $V = 0.2947$, Odds Ratio = $4.3140$.
   - **Interpretation:** Students reporting heavy or overwhelming workload have 4.31 times higher odds of experiencing high burnout risk.

2. **Stress Trajectory Across Semester:**
   - Repeated measures Friedman Test on `stress_start` ($1.97 \pm 1.00$), `stress_mid` ($3.06 \pm 0.92$), and `stress_now` ($3.20 \pm 1.21$):
   - $\chi^2 = 108.4251$, $p = 2.86 \times 10^{-24}$, Kendall's $W = 0.4107$ ($p < 0.001$).
   - **Interpretation:** Student stress accelerates dramatically after the beginning of the semester and remains elevated.

3. **Bedtime Smartphone Usage vs. Burnout:**
   - $\chi^2 = 3.2246$, $p = 0.0725$, Cramer's $V = 0.1563$ (Non-significant at $\alpha = 0.05$).

4. **Exam Performance vs. Burnout:**
   - Mann-Whitney $U = 1444.0$, $p = 0.0622$, Rank Biserial Correlation = $0.1435$ (Non-significant at $\alpha = 0.05$).

5. **Exercise Frequency vs. Burnout:**
   - $\chi^2 = 1.9143$, $p = 0.1665$, Cramer's $V = 0.1204$ (Non-significant at $\alpha = 0.05$).

6. **Gender vs. Burnout:**
   - $\chi^2 = 0.0166$, $p = 0.8976$, Cramer's $V = 0.0112$ (Non-significant at $\alpha = 0.05$).
