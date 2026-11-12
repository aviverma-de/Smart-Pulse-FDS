"""
SmartPulse Validation Database (SQLite + SQLAlchemy)
"""

import os
import json
import uuid
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from . import config

Base = declarative_base()

class Student(Base):
    __tablename__ = "students"

    id = Column(String(64), primary_key=True)  # Anonymous ID
    return_code = Column(String(32), unique=True, nullable=False, index=True)
    consent_given = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="student", cascade="all, delete-orphan")
    feedback = relationship("StudentFeedback", back_populates="student", cascade="all, delete-orphan")
    outcomes = relationship("VerifiedOutcome", back_populates="student", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    inputs_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="assessments")
    predictions = relationship("Prediction", back_populates="assessment", cascade="all, delete-orphan")
    outcomes = relationship("VerifiedOutcome", back_populates="assessment", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    model_version = Column(String(32), default="v1.0", nullable=False)
    category = Column(String(32), nullable=False)  # "High Risk" or "Low Risk"
    probs = Column(Text, nullable=True)            # JSON: {"high": 0.65, "low": 0.35}
    score = Column(Float, nullable=True)           # Continuous score (5.0 - 25.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="predictions")
    assessment = relationship("Assessment", back_populates="predictions")
    feedback = relationship("StudentFeedback", back_populates="prediction", cascade="all, delete-orphan")

class StudentFeedback(Base):
    __tablename__ = "student_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    agreement = Column(String(32), nullable=False)  # "Yes", "No", "Not sure"
    score_feels_right = Column(String(32), nullable=True)  # "Yes", "No", "Not sure"
    comment = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="feedback")
    prediction = relationship("Prediction", back_populates="feedback")

class VerifiedOutcome(Base):
    __tablename__ = "verified_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True)
    bo1 = Column(Integer, nullable=False)
    bo2 = Column(Integer, nullable=False)
    bo3 = Column(Integer, nullable=False)
    bo4 = Column(Integer, nullable=False)
    bo5 = Column(Integer, nullable=False)
    measured_score = Column(Float, nullable=False)        # 5.0 - 25.0
    measured_category = Column(String(32), nullable=False) # "High Risk" or "Low Risk"
    days_after_assessment = Column(Float, default=0.0, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="outcomes")
    assessment = relationship("Assessment", back_populates="outcomes")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(32), unique=True, nullable=False, index=True)
    path = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    parent = Column(String(32), nullable=True)
    training_rows = Column(Integer, default=105, nullable=False)
    features = Column(Text, nullable=False)  # JSON list
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(32), nullable=False, index=True)
    n = Column(Integer, nullable=False)
    metrics_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

# SQLite database setup
DB_URL = f"sqlite:///{config.BASE_DIR / 'validation.db'}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Register v1.0 baseline if not present
        v1 = db.query(ModelVersion).filter_by(version="v1.0").first()
        if not v1:
            FEATURES = [
                "sleep_mid_hrs", "sleep_quality", "bedtime_code",
                "screen_mid_hrs", "phone_bed_code",
                "exercise_days_mid", "deadlines_code",
                "workload_code", "performance_code", "performance_missing"
            ]
            v1 = ModelVersion(
                version="v1.0",
                path=str(config.SAVED_MODELS_DIR),
                is_active=True,
                parent=None,
                training_rows=105,
                features=json.dumps(FEATURES),
                created_at=datetime.datetime.utcnow()
            )
            db.add(v1)
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
