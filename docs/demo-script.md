# SmartPulse — Professor Walkthrough & Demo Script

> **Tagline:** *"Understand stress. Predict burnout. Take action."*  
> **Target Audience:** Course Professor & Evaluation Committee  
> **Order of Presentation:** Overview Dashboard ➔ Student Assessment ➔ AI Prediction with Attributions ➔ Score & What-If Simulator ➔ Personalized Recommendations ➔ PDF Report

---

## ⏱️ Act 1: Population Overview Dashboard

1. **Open the browser at:** `http://localhost:5173/dashboard`
2. **Narration:**
   > *"Good morning, Professor. Welcome to SmartPulse. Rather than presenting isolated Python scripts, we engineered a full-stack clinical-disclaimed monitoring platform for student academic well-being.
   > Here on the Population Overview Dashboard, we see live population data from our N = 132 student cohort. Notice that our sample has an average burnout of 14.98 on a 25-point scale, with 53.8% exceeding the sample median.
   > Crucially, our Semester Stress Dynamics timeline demonstrates how student stress escalates by +1.23 points—over 60%—from semester kickoff through midterms and finals, supported by a repeated-measures Friedman test (p < 0.001)."*

---

## ⏱️ Act 2: Validated Student Assessment Flow

1. **Click:** `Assessment` in the top navigation bar (`http://localhost:5173/assessment`)
2. **Demonstration:**
   - Step 1: Select `5 to 6 hours` of sleep, `2 - Poor` quality, and `1:00 AM – 3:00 AM` bedtime. Click **Continue**.
   - Step 2: Select `6 to 8 hours` of non-academic screen time and `Usually` for bedtime phone use. Click **Continue**.
   - Step 3: Select `Heavy` workload, `1 to 2 days` of exercise, `6 to 8 deadlines`, and `Slightly below expectations`. Click **Continue**.
   - Step 4: Review PSS-4 items (stress items are kept separate to prevent target leakage).
   - Click **"Analyze My Well-being"**.
3. **Narration:**
   > *"Our 4-step progressive questionnaire uses the exact 9 lifestyle habits modeled in our study. All inputs map to validated ordinal midpoints. Notice that demographic items and stress outcome measures are strictly excluded from predictive features to prevent data leakage."*

---

## ⏱️ Act 3: AI Burnout Risk Prediction & Transparent Attributions

1. **Arrive at:** `http://localhost:5173/predictions`
2. **Narration:**
   > *"Upon submission, our backend runs real-time inference using our serialized 500-tree Random Forest classifier and Bayesian linear regressor.
   > The user is flagged as 'High Burnout Risk' with an estimated probability of ~64%.
   > Instead of black-box predictions, our 'Why this prediction?' section performs real feature attribution via standardized log-odds decomposition. We see that perceived heavy workload (+0.53 log-odds) and bedtime smartphone usage (+0.35 log-odds) are the primary driving risk factors for this student."*

---

## ⏱️ Act 4: Continuous Score & Interactive What-If Simulator

1. **Click:** `Score & What-If` (`http://localhost:5173/estimator`)
2. **Demonstration:**
   - Show the continuous score gauge (`~16.8 / 25`) with its 94% Credible Interval and cohort percentile.
   - Point to the **Actual vs. Predicted scatter plot** where the user's prediction is marked directly against the 132 student test-set points!
   - In the What-If Simulator, switch **Perceived Study Workload** from `Heavy` down to `Manageable`, and **Bedtime Smartphone** from `Usually` down to `Never`.
   - Watch the live debounced simulation drop the score by **-5.68 points**, triggering an automatic category transition from **High Risk ➔ Low Risk**.
3. **Narration:**
   > *"In our Burnout Score Estimator, we compute continuous burnout total via Bayesian posterior means. The scatter plot marks the student's score against all 132 real survey respondents.
   > On the right, our What-If Simulator demonstrates counterfactual sensitivity. Adjusting workload and removing bedtime phone use shifts the continuous prediction downward by 5.7 points. We also feature a prominent caution highlighting that these are hypothetical scenarios, preserving proper statistical nuance."*

---

## ⏱️ Act 5: Personalized Recommendations & Official PDF Report

1. **Click:** `Wellness` (`http://localhost:5173/recommendations`) and then `Report` (`http://localhost:5173/report`)
2. **Demonstration:**
   - Review rule-based lifestyle recommendations customized to the student's top risk factors.
   - Show the gentle campus counseling support note for students with elevated risk.
   - Click `Download PDF Report` on the Report view to display the cleanly generated ReportLab PDF.
3. **Narration:**
   > *"Our Recommendations engine provides supportive, non-clinical wellness suggestions tailored to the student's primary risk drivers. Students with high burnout estimates receive a gentle note connecting them with campus counseling resources. Finally, students can generate a formal downloadable PDF summary for their personal records.
   > SmartPulse is ready for evaluation."*
