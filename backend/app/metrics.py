"""
SmartPulse Validation Metrics Module
Provides audited, mathematically rigorous evaluation metrics:
- Wilson score confidence intervals for proportions (Accuracy, P/R/F1)
- Bootstrap confidence intervals for continuous metrics (MAE, RMSE, R²)
- Classification & Confusion matrix vs MEASURED actuals only
- Regression metrics (MAE, RMSE, R², residuals, actual vs predicted)
- Subjective student feedback analytics & feedback vs correctness cross-tab
- Error analysis by class, key segments (workload, sleep, phone), largest residuals
- Strict low-sample safeguards (n=0: "Not yet established", n < min_n: low sample warning)
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Optional[List[float]]:
    """
    Computes the Wilson score interval for a binomial proportion.
    """
    if total <= 0:
        return None
    p = float(successes) / float(total)
    # Standard normal quantile: 1.95996 for 95%
    z = 1.959963984540054
    if confidence == 0.90:
        z = 1.6448536269514722
    elif confidence == 0.99:
        z = 2.5758293035489004

    denom = 1.0 + (z * z) / float(total)
    centre_adj = (p + (z * z) / (2.0 * float(total))) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / float(total)) + ((z * z) / (4.0 * float(total) * float(total))))

    lower = max(0.0, centre_adj - spread)
    upper = min(1.0, centre_adj + spread)
    return [round(lower, 4), round(upper, 4)]

def bootstrap_ci(
    y_true: List[float],
    y_pred: List[float],
    metric_type: str = "mae",
    n_boot: int = 1000,
    seed: int = 42,
    alpha: float = 0.05
) -> Optional[List[float]]:
    """
    Computes percentile bootstrap confidence intervals for MAE, RMSE, or R2.
    """
    n = len(y_true)
    if n < 3:
        return None

    rng = np.random.RandomState(seed)
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    scores = []

    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        sample_yt = yt[idx]
        sample_yp = yp[idx]

        if metric_type == "mae":
            score = np.mean(np.abs(sample_yt - sample_yp))
        elif metric_type == "rmse":
            score = np.sqrt(np.mean((sample_yt - sample_yp) ** 2))
        elif metric_type == "r2":
            ss_tot = np.sum((sample_yt - np.mean(sample_yt)) ** 2)
            if ss_tot < 1e-9:
                score = 0.0
            else:
                ss_res = np.sum((sample_yt - sample_yp) ** 2)
                score = 1.0 - (ss_res / ss_tot)
        else:
            raise ValueError(f"Unknown metric_type: {metric_type}")
        scores.append(score)

    lower = float(np.percentile(scores, 100 * (alpha / 2.0)))
    upper = float(np.percentile(scores, 100 * (1.0 - alpha / 2.0)))
    return [round(lower, 4), round(upper, 4)]

def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    min_n: int = 30
) -> Dict[str, Any]:
    """
    Calculates accuracy, per-class P/R/F1, macro/weighted F1, high-burnout recall,
    Wilson CIs, and confusion matrix vs MEASURED actuals only.
    """
    n = len(y_true)
    if n == 0:
        return {
            "status": "not_established",
            "message": "Not yet established (n=0)",
            "n": 0,
            "min_n": min_n
        }

    # Normalize category names
    def norm(cat: str) -> str:
        c = str(cat).strip().lower()
        if "high" in c:
            return "High"
        if "moderate" in c or "medium" in c:
            return "Moderate"
        if "low" in c:
            return "Low"
        return cat.strip()

    yt = [norm(y) for y in y_true]
    yp = [norm(y) for y in y_pred]

    correct_count = sum(1 for a, p in zip(yt, yp) if a == p)
    accuracy = correct_count / n
    acc_ci = wilson_score_interval(correct_count, n)

    # Unique classes preserving logical order
    ordered_possible = ["High", "Moderate", "Low"]
    all_classes = [c for c in ordered_possible if c in yt or c in yp]
    if not all_classes:
        all_classes = sorted(list(set(yt) | set(yp)))

    per_class = {}
    macro_p_sum = 0.0
    macro_r_sum = 0.0
    macro_f1_sum = 0.0
    weighted_f1_sum = 0.0

    for cls in all_classes:
        tp = sum(1 for a, p in zip(yt, yp) if a == cls and p == cls)
        fp = sum(1 for a, p in zip(yt, yp) if a != cls and p == cls)
        fn = sum(1 for a, p in zip(yt, yp) if a == cls and p != cls)
        support = sum(1 for a in yt if a == cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        prec_ci = wilson_score_interval(tp, tp + fp) if (tp + fp) > 0 else None
        rec_ci = wilson_score_interval(tp, tp + fn) if (tp + fn) > 0 else None

        per_class[cls] = {
            "precision": round(prec, 4),
            "precision_ci": prec_ci,
            "recall": round(rec, 4),
            "recall_ci": rec_ci,
            "f1": round(f1, 4),
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn
        }
        macro_p_sum += prec
        macro_r_sum += rec
        macro_f1_sum += f1
        weighted_f1_sum += f1 * support

    num_classes = max(1, len(all_classes))
    macro_f1 = macro_f1_sum / num_classes
    macro_p = macro_p_sum / num_classes
    macro_r = macro_r_sum / num_classes
    weighted_f1 = weighted_f1_sum / n if n > 0 else 0.0

    # High burnout recall callout
    high_rec_info = per_class.get("High", {"recall": 0.0, "recall_ci": None, "support": 0})
    high_burnout_recall = high_rec_info["recall"]
    high_burnout_recall_ci = high_rec_info["recall_ci"]

    # Confusion matrix
    # Format: matrix[actual_idx][pred_idx]
    cm = []
    for actual_cls in all_classes:
        row = []
        for pred_cls in all_classes:
            cnt = sum(1 for a, p in zip(yt, yp) if a == actual_cls and p == pred_cls)
            row.append(cnt)
        cm.append(row)

    is_low_sample = n < min_n
    progress_pct = min(100.0, round((n / float(min_n)) * 100.0, 1))

    return {
        "status": "ready",
        "n": n,
        "min_n": min_n,
        "is_low_sample": is_low_sample,
        "progress_pct": progress_pct,
        "accuracy": round(accuracy, 4),
        "accuracy_ci": acc_ci,
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "high_burnout_recall": high_burnout_recall,
        "high_burnout_recall_ci": high_burnout_recall_ci,
        "classes": all_classes,
        "per_class": per_class,
        "confusion_matrix": cm,
        "confusion_matrix_labels": all_classes
    }

def compute_regression_metrics(
    y_true: List[float],
    y_pred: List[float],
    min_n: int = 30
) -> Dict[str, Any]:
    """
    Computes MAE, RMSE, R2, actual-vs-predicted pairs, residuals,
    and bootstrap confidence intervals.
    """
    n = len(y_true)
    if n == 0:
        return {
            "status": "not_established",
            "message": "Not yet established (n=0)",
            "n": 0,
            "min_n": min_n
        }

    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    diff = yt - yp

    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))

    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    if ss_tot < 1e-9:
        r2 = 0.0
    else:
        ss_res = float(np.sum(diff ** 2))
        r2 = float(1.0 - (ss_res / ss_tot))

    mae_ci = bootstrap_ci(y_true, y_pred, "mae")
    rmse_ci = bootstrap_ci(y_true, y_pred, "rmse")
    r2_ci = bootstrap_ci(y_true, y_pred, "r2")

    pairs = [
        {
            "index": i + 1,
            "actual": round(float(a), 2),
            "predicted": round(float(p), 2),
            "residual": round(float(a - p), 2)
        }
        for i, (a, p) in enumerate(zip(yt, yp))
    ]

    is_low_sample = n < min_n
    progress_pct = min(100.0, round((n / float(min_n)) * 100.0, 1))

    return {
        "status": "ready",
        "n": n,
        "min_n": min_n,
        "is_low_sample": is_low_sample,
        "progress_pct": progress_pct,
        "mae": round(mae, 4),
        "mae_ci": mae_ci,
        "rmse": round(rmse, 4),
        "rmse_ci": rmse_ci,
        "r2": round(r2, 4),
        "r2_ci": r2_ci,
        "residual_mean": round(float(np.mean(diff)), 4),
        "residual_std": round(float(np.std(diff)), 4),
        "pairs": pairs
    }

def compute_feedback_analytics(
    feedbacks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Subjective feedback analysis:
    - Counts and percentages for Yes / No / Not sure
    - Cross-tabulation of feedback vs measured correctness (when both exist)
    - Stored and labeled separately: 'Subjective feedback — not ground truth'
    """
    n = len(feedbacks)
    if n == 0:
        return {
            "status": "not_established",
            "message": "Not yet established (n=0)",
            "n": 0,
            "is_ground_truth": False,
            "label": "Subjective Student Feedback (Not Ground Truth)"
        }

    counts = {"Yes": 0, "No": 0, "Not sure": 0}
    crosstab = {
        "Yes": {"correct": 0, "incorrect": 0, "unverified": 0},
        "No": {"correct": 0, "incorrect": 0, "unverified": 0},
        "Not sure": {"correct": 0, "incorrect": 0, "unverified": 0}
    }

    for item in feedbacks:
        raw_ag = str(item.get("agreement", "Not sure")).strip().capitalize()
        if raw_ag not in counts:
            if "yes" in raw_ag.lower() or "agree" in raw_ag.lower():
                raw_ag = "Yes"
            elif "no" in raw_ag.lower() or "disagree" in raw_ag.lower():
                raw_ag = "No"
            else:
                raw_ag = "Not sure"
        counts[raw_ag] += 1

        is_correct = item.get("is_correct")
        if is_correct is True:
            crosstab[raw_ag]["correct"] += 1
        elif is_correct is False:
            crosstab[raw_ag]["incorrect"] += 1
        else:
            crosstab[raw_ag]["unverified"] += 1

    percentages = {
        k: round((counts[k] / n) * 100.0, 1) for k in counts
    }

    agreement_rate = percentages["Yes"]
    agreement_ci = wilson_score_interval(counts["Yes"], n)

    return {
        "status": "ready",
        "n": n,
        "is_ground_truth": False,
        "label": "Subjective Student Feedback (Not Ground Truth)",
        "agreement_percentage": agreement_rate,
        "agreement_ci": agreement_ci,
        "counts": counts,
        "percentages": percentages,
        "cross_tabulation": crosstab
    }

def compute_error_analysis(
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Error analysis:
    - By class: False Positives (predicted High, actual Low), False Negatives (predicted Low, actual High)
    - Key input segments: workload (>=3 vs <3), sleep (<6h vs >=6h), phone bedtime (>=3 vs <3)
    - Largest residuals (top over/under predictions)
    - Low-sample warning flags (<5 per segment)
    """
    n = len(records)
    if n == 0:
        return {
            "status": "not_established",
            "message": "Not yet established (n=0)",
            "n": 0
        }

    false_positives = []
    false_negatives = []
    residuals_list = []

    # Segment accumulators
    segments = {
        "workload_heavy": {"name": "Heavy Workload (Score >= 3)", "total": 0, "correct": 0},
        "workload_light": {"name": "Light/Manageable Workload (Score < 3)", "total": 0, "correct": 0},
        "sleep_short": {"name": "Short Sleep (< 6.0 hrs)", "total": 0, "correct": 0},
        "sleep_adequate": {"name": "Adequate Sleep (>= 6.0 hrs)", "total": 0, "correct": 0},
        "phone_in_bed_high": {"name": "High Bedtime Phone Use (Score >= 3)", "total": 0, "correct": 0},
        "phone_in_bed_low": {"name": "Low Bedtime Phone Use (Score < 3)", "total": 0, "correct": 0},
    }

    for r in records:
        pred_cat = str(r.get("pred_cat", "")).strip().lower()
        actual_cat = str(r.get("actual_cat", "")).strip().lower()
        pred_high = "high" in pred_cat
        actual_high = "high" in actual_cat

        # Continuous residual
        pred_score = float(r.get("pred_score", 0.0))
        actual_score = float(r.get("actual_score", 0.0))
        res = actual_score - pred_score
        residuals_list.append({
            "record_id": r.get("id"),
            "actual_score": actual_score,
            "pred_score": pred_score,
            "residual": round(res, 2),
            "abs_residual": round(abs(res), 2)
        })

        is_match = (pred_high == actual_high)
        if pred_high and not actual_high:
            false_positives.append(r)
        elif not pred_high and actual_high:
            false_negatives.append(r)

        # Segments
        inputs = r.get("inputs", {})
        wl = inputs.get("workload_code", 2)
        if wl >= 3:
            segments["workload_heavy"]["total"] += 1
            if is_match: segments["workload_heavy"]["correct"] += 1
        else:
            segments["workload_light"]["total"] += 1
            if is_match: segments["workload_light"]["correct"] += 1

        sl = inputs.get("sleep_mid_hrs", 7.0)
        if sl < 6.0:
            segments["sleep_short"]["total"] += 1
            if is_match: segments["sleep_short"]["correct"] += 1
        else:
            segments["sleep_adequate"]["total"] += 1
            if is_match: segments["sleep_adequate"]["correct"] += 1

        ph = inputs.get("phone_bed_code", 2)
        if ph >= 3:
            segments["phone_in_bed_high"]["total"] += 1
            if is_match: segments["phone_in_bed_high"]["correct"] += 1
        else:
            segments["phone_in_bed_low"]["total"] += 1
            if is_match: segments["phone_in_bed_low"]["correct"] += 1

    segment_results = {}
    for seg_key, data in segments.items():
        tot = data["total"]
        acc = round((data["correct"] / tot) * 100.0, 1) if tot > 0 else 0.0
        segment_results[seg_key] = {
            "name": data["name"],
            "n": tot,
            "accuracy_pct": acc,
            "error_rate_pct": round(100.0 - acc, 1) if tot > 0 else 0.0,
            "low_sample_flag": tot < 5
        }

    # Top largest residuals
    residuals_sorted = sorted(residuals_list, key=lambda x: x["abs_residual"], reverse=True)
    top_residuals = residuals_sorted[:5]

    return {
        "status": "ready",
        "n": n,
        "false_positives_count": len(false_positives),
        "false_negatives_count": len(false_negatives),
        "fp_rate": round(len(false_positives) / n, 4) if n > 0 else 0.0,
        "fn_rate": round(len(false_negatives) / n, 4) if n > 0 else 0.0,
        "common_confusion": "Low Risk predicted as High" if len(false_positives) >= len(false_negatives) else "High Risk missed as Low",
        "segments": segment_results,
        "largest_residuals": top_residuals
    }
