# SmartPulse — Student Stress & Burnout Monitoring Platform

> **Tagline:** *"Understand stress. Predict burnout. Take action."*  
> **Course:** Foundations of Data Science (FDS) Final Project  
> **Dataset:** $N = 132$ university respondents (`SmartPulse_Cleaned.xlsx`, Sheet: `Cleaned_Data`)  
> **Status:** Full-Stack Production Build Verified (Backend & Frontend Active)

---

## 🌟 Executive Overview

SmartPulse is a university-grade web platform engineered to analyze student lifestyle habits, evaluate burnout risk through machine learning, and deliver non-clinical wellness recommendations. The system is designed with rigorous statistical integrity, privacy-first data handling, and responsible AI guardrails.

---

## 🏛️ System Architecture

SmartPulse is organized into a clean decoupled architecture:

```
FDS/
├── backend/                         # FastAPI High-Performance Python Backend
│   ├── app/
│   │   ├── config.py                # Configuration, CORS, Seed, Disclaimers
│   │   ├── main.py                  # FastAPI entry point & lifespan handler
│   │   ├── models.py                # Pydantic schemas & strict validators
│   │   ├── preprocessing.py         # Leakage-free feature transformations
│   │   ├── model_loader.py          # Startup model artifact loader
│   │   ├── routers/                 # Modular RESTful endpoints
│   │   │   ├── overview.py          # GET /api/overview
│   │   │   ├── predict.py           # POST /api/predict/category, /score
│   │   │   ├── whatif.py            # POST /api/whatif (Simulator)
│   │   │   ├── explain.py           # POST /api/explain (Attribution)
│   │   │   └── report.py            # POST /api/report (ReportLab PDF)
│   │   └── services/
│   │       ├── prediction_service.py # Real inference & attribution logic
│   │       └── report_service.py     # Clean PDF generation engine
│   ├── saved_models/                # Serialized Joblib pipelines & parameters
│   │   ├── pipe_rf.joblib           # 500-Tree Random Forest Classifier
│   │   ├── pipe_lr.joblib           # L2 Logistic Regression Pipeline
│   │   ├── reg_ols.joblib           # OLS Linear Regressor
│   │   ├── preprocessor_meta.json   # Scaling & median imputation params
│   │   └── bayes_params.json        # 8,000 NUTS MCMC draw posterior means
│   ├── artifacts/                   # Pre-computed verified JSON artifacts
│   ├── tests/                       # Pytest test suite (10/10 passing)
│   ├── train_and_save.py            # Model serialization script
│   └── export_artifacts.py          # Artifacts generation script
│
├── frontend/                        # Modern React 19 + Vite 6 Web Application
│   ├── src/
│   │   ├── components/              # Reusable glassmorphic UI components
│   │   │   ├── Navbar.jsx           # Glass navigation with mobile drawer
│   │   │   ├── Footer.jsx           # Privacy & disclaimer footer
│   │   │   ├── Card.jsx             # Glassmorphic card container
│   │   │   ├── StatCard.jsx         # Animated count-up metric card
│   │   │   ├── Gauge.jsx            # Score indicator gauge
│   │   │   ├── RiskBadge.jsx        # High/Low risk indicator
│   │   │   └── Disclaimer.jsx       # Prominent ethical & clinical notice
│   │   ├── pages/
│   │   │   ├── HomePage.jsx         # Hero, glance strip, explore cards
│   │   │   ├── DashboardPage.jsx    # Population analytics & stress timeline
│   │   │   ├── AssessmentPage.jsx   # 4-step validated student questionnaire
│   │   │   ├── PredictionsPage.jsx  # AI risk category & feature attributions
│   │   │   ├── EstimatorPage.jsx    # Continuous score & What-If simulator
│   │   │   ├── RecommendationsPage.jsx # Rule-based supportive wellness suggestions
│   │   │   └── ReportPage.jsx       # Document preview & PDF download
│   │   ├── utils/
│   │   │   ├── api.js               # Centralized fetch client
│   │   │   └── constants.js         # Survey mappings & feature definitions
│   │   └── App.jsx                  # React Router configuration
│   └── package.json
│
├── docs/                            # Documentation & Audit Artifacts
│   ├── decisions.md                 # Architectural & engineering decisions
│   ├── repo-findings.md             # Dataset discovery & script audit
│   ├── data-lineage.md              # Provenance tracing table for all figures
│   └── demo-script.md               # Professor walkthrough script
└── smartpulse_models/               # Original coursework models & outputs
```

---

## 🚀 Quickstart & Run Commands

### 1. Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Run automated test suite (10 tests)
python -m pytest -v

# Launch FastAPI server on http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend (React + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install

# Run development server on http://localhost:5173
npm run dev

# Or build production static assets
npm run build
```

---

## 🛡️ Limitations & Responsible Use

1. **Academic Demonstration Only:** This application is developed for educational coursework in statistical learning. It **must not** be used for clinical diagnosis, psychiatric screening, or high-stakes academic evaluations.
2. **Non-Causal Design:** The underlying dataset is cross-sectional. Observed relationships demonstrate statistical correlation; they do not prove that altering an isolated habit will mechanically reduce burnout.
3. **Sample Characteristics:** The respondent pool ($N = 132$) is drawn predominantly from 2nd-year engineering hostel residents at a single institution.
4. **Self-Report Bias:** Ordinal scales reflect respondent subjective perception rather than objective physiological tracking.
5. **Privacy by Design:** Zero mandatory accounts or login credentials. Assessment answers are evaluated in-memory and discarded unless explicitly exported as a local PDF.

---

## 📚 Supporting Documentation
- [Architecture & Implementation Decisions](docs/decisions.md)
- [Repository Findings & Preprocessing Discovery](docs/repo-findings.md)
- [Data Lineage & Provenance Audit Table](docs/data-lineage.md)
- [Professor Walkthrough & Demo Script](docs/demo-script.md)
