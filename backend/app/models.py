"""
SmartPulse Pydantic Schemas and Request/Response Models
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

class AssessmentInput(BaseModel):
    # Lifestyle features
    sleep_mid_hrs: float = Field(
        ...,
        description="Daily sleep duration in hours (allowed: 4.5, 5.5, 6.5, 7.5, 8.5, 9.5)",
        examples=[6.5]
    )
    sleep_quality: int = Field(
        ...,
        ge=1, le=5,
        description="Self-rated sleep quality (1 = Very poor to 5 = Excellent)",
        examples=[3]
    )
    bedtime_code: int = Field(
        ...,
        ge=1, le=4,
        description="Typical bedtime (1: Before 11pm, 2: 11pm-1am, 3: 1am-3am, 4: After 3am)",
        examples=[2]
    )
    screen_mid_hrs: float = Field(
        ...,
        description="Daily non-academic screen time hours (allowed: 1.0, 3.0, 5.0, 7.0, 9.0)",
        examples=[5.0]
    )
    phone_bed_code: int = Field(
        ...,
        ge=1, le=4,
        description="Phone use in bed before sleeping (1: Never, 2: Sometimes, 3: Usually, 4: Always)",
        examples=[3]
    )
    exercise_days_mid: float = Field(
        ...,
        description="Days per week of exercise (allowed: 0.0, 1.5, 3.5, 5.5)",
        examples=[1.5]
    )
    deadlines_code: int = Field(
        ...,
        ge=1, le=4,
        description="Density of upcoming academic deadlines (1: 0-2, 2: 3-5, 3: 6-8, 4: 9+)",
        examples=[2]
    )
    workload_code: int = Field(
        ...,
        ge=1, le=4,
        description="Perceived academic workload (1: Very light, 2: Manageable, 3: Heavy, 4: Overwhelming)",
        examples=[3]
    )
    performance_code: Optional[float] = Field(
        default=None,
        description="Recent exam performance vs expectations (1: Much below to 5: Much above, or null if no exams yet)",
        examples=[3.0]
    )

    # Optional PSS stress items (for display & stress score calculation only; NOT fed to ML models)
    pss1_no_control: Optional[int] = Field(default=3, ge=1, le=5)
    pss2_confident: Optional[int] = Field(default=3, ge=1, le=5)
    pss3_going_my_way: Optional[int] = Field(default=3, ge=1, le=5)
    pss4_piling_up: Optional[int] = Field(default=3, ge=1, le=5)

    @field_validator("sleep_mid_hrs")
    @classmethod
    def validate_sleep_hours(cls, v):
        allowed = {4.5, 5.5, 6.5, 7.5, 8.5, 9.5}
        if round(v, 1) not in allowed:
            raise ValueError(f"sleep_mid_hrs must be one of {sorted(allowed)}")
        return round(v, 1)

    @field_validator("screen_mid_hrs")
    @classmethod
    def validate_screen_hours(cls, v):
        allowed = {1.0, 3.0, 5.0, 7.0, 9.0}
        if round(v, 1) not in allowed:
            raise ValueError(f"screen_mid_hrs must be one of {sorted(allowed)}")
        return round(v, 1)

    @field_validator("exercise_days_mid")
    @classmethod
    def validate_exercise_days(cls, v):
        allowed = {0.0, 1.5, 3.5, 5.5}
        if round(v, 1) not in allowed:
            raise ValueError(f"exercise_days_mid must be one of {sorted(allowed)}")
        return round(v, 1)

    @field_validator("performance_code")
    @classmethod
    def validate_performance(cls, v):
        if v is not None and v not in {1.0, 2.0, 3.0, 4.0, 5.0}:
            raise ValueError("performance_code must be between 1.0 and 5.0, or null")
        return v

class PredictionResponse(BaseModel):
    category: str
    risk_label: str
    probabilities: Dict[str, float]
    model_used: str
    threshold: float
    disclaimer: str

class ScoreResponse(BaseModel):
    predicted_score: float
    credible_interval_94: List[float]
    scale_min: int
    scale_max: int
    percentile: float
    calculated_stress_total: Optional[int] = None
    disclaimer: str

class WhatIfRequest(BaseModel):
    baseline: AssessmentInput
    modified: AssessmentInput

class WhatIfScenarioResult(BaseModel):
    score: float
    category: str
    probabilities: Dict[str, float]

class WhatIfResponse(BaseModel):
    baseline: WhatIfScenarioResult
    modified: WhatIfScenarioResult
    score_difference: float
    category_changed: bool
    direction: str
    caution: str
    disclaimer: str

class FeatureContribution(BaseModel):
    feature: str
    label: str
    user_value: Any
    contribution: float
    direction: str  # "increases_risk" or "decreases_risk"

class TopFactorExplanation(BaseModel):
    feature: str
    label: str
    impact_level: str
    explanation: str

class ExplainResponse(BaseModel):
    method: str
    contributions: List[FeatureContribution]
    top_factors: List[TopFactorExplanation]
    disclaimer: str

class ReportRequest(BaseModel):
    inputs: AssessmentInput
    prediction: PredictionResponse
    score: ScoreResponse
    explanation: ExplainResponse
    student_name: Optional[str] = "Student"
    opt_in_storage: Optional[bool] = False
