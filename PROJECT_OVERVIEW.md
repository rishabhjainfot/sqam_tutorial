# Project Technical Documentation & Architecture Guide

**Project Title:** *An SQA Testing Framework for Data Quality and Model Validation in Battery State-of-Health Prediction Models*  
**Course:** Software Quality Assurance and Metrics (SQAM)  
**Author / Student:** Rishabh (4th-year B.Tech Electrical Engineering, Delhi University)  
**Dataset:** NASA Ames Prognostics Center of Excellence (PCoE) Li-ion Battery Dataset (B0005, B0006, B0007, B0018)  
**Artifact Under Test:** Scikit-Learn Random Forest Regressor for Capacity / State-of-Health (SOH) Estimation  

---

## 1. Problem Statement & Motivation

In safety-critical electrical applications—such as Electric Vehicle (EV) Battery Management Systems (BMS)—machine learning models predict battery State-of-Health (SOH) and Remaining Useful Life (RUL). However, existing research almost exclusively optimizes for dataset-wide accuracy (minimizing RMSE or maximizing R²).

This traditional approach creates major risks:
1. **Garbage-In, Garbage-Out:** Sensor telemetry is rarely audited for missingness, unit inconsistencies, or anomalous spikes before training.
2. **Concealed Regional Failure:** A low global RMSE can easily mask severe, catastrophic prediction errors in late-life degradation stages (<70% capacity) where thermal runaway and failure risks are highest.
3. **Sensor Fragility:** Models are rarely stress-tested against thermal sensor drift or measurement noise.
4. **Silent Regressions:** Hyperparameter and architecture updates are not subjected to automated regression test suites, meaning updates can silently break existing capabilities.

This project addresses these gaps by building an applied **Software Quality Assurance (SQA)** testing framework.

---

## 2. System Architecture & Testing Pipeline

```
+-----------------------------------------------------------------------------------+
|                            STAGE 1: DATA QUALITY AUDIT                            |
|                     Wang & Strong (1996) Intrinsic Dimensions                     |
|      [Completeness]          [Consistency]          [Accuracy]      [Timeliness]  |
|      (Null checking)      (Physical ranges)      (Tukey 3xIQR)     (Delta-t check)|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        STAGE 2: MODEL ARTIFACT UNDER TEST                         |
|         Per-Cycle Feature Extraction (Mean/Terminal V, Current, Duration, Temp)   |
|         Strict Disjoint Split: Train on B0005, B0006, B0007 | Test on B0018       |
|         Model v1: Random Forest Regressor (n_estimators=100) -> baseline.json     |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        STAGE 3: STAGE-WISE FUNCTIONAL TEST                        |
|       Early Life (>90% cap)       Mid Life (70-90% cap)       Late Life (<70% cap)|
|       N=38, RMSE=0.0130 Ah        N=94, RMSE=0.0335 Ah        N=0 (Coverage gap)  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                       STAGE 4: SENSITIVITY & ROBUSTNESS TEST                      |
|       Temperature perturbation: -20%, -10%, -5%, +5%, +10%, +20%                  |
|       Maximum output divergence = 0.0206 Ah (< 0.0500 Ah safety threshold)       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            STAGE 5: REGRESSION TESTING                            |
|       Model v2 (n_estimators=200) vs. Model v1 Baseline (100 trees)               |
|       RMSE +8.1% (FAIL) | MAE +6.9% (FAIL) | R2 -0.6% (PASS)                      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                    STAGE 6: DEFECT LOGGING & ISO/IEC 25010                        |
|       Defects: D-020 & D-021 | Defect Density = 16.67% | Pass Rate = 83.33%       |
|       Functional Suitability: PASS | Reliability: PARTIAL (regression vulnerable) |
+-----------------------------------------------------------------------------------+
```

---

## 3. Empirical Results Summary

### 3.1 Data Quality Scorecard (Wang & Strong 1996)
- **Completeness:** 100.0% across all 4 batteries.
- **Consistency:** 99.2% – 100.0% adherence to physical voltage, current, and temperature bounds.
- **Accuracy:** B0005 (89.5%) and B0006 (87.9%) were flagged due to Tukey 3×IQR transition outliers. B0007 (94.8%) and B0018 (91.1%) passed.
- **Timeliness:** 91.7% – 97.2% regular sampling intervals.

### 3.2 Stage-Wise Functional Correctness
- **Early Life (>90% capacity, N=38):** RMSE = 0.0130 Ah, MAE = 0.0111 Ah, R² = 0.9463 (PASS).
- **Mid Life (70–90% capacity, N=94):** RMSE = 0.0335 Ah, MAE = 0.0264 Ah, R² = 0.8855 (PASS).
- **Late Life (<70% capacity, N=0):** Identified an operational test coverage gap (B0018 stopped cycling before 70%).

### 3.3 Robustness & Input Sensitivity
- Perturbation levels: $\pm 5\%$, $\pm 10\%$, $\pm 20\%$.
- Maximum observed divergence: **0.0206 Ah** (~1.08% capacity) at +20% temperature perturbation.
- All perturbation levels passed the 0.0500 Ah safety threshold.

### 3.4 Regression Testing & Defect Logging
- Increasing trees from 100 to 200 worsened RMSE by +8.1% and MAE by +6.9%.
- Automated regression suite caught this and logged defects `D-020` and `D-021`.
- Defect Density: **16.67%** (2 defects / 12 test cases).
- Severity-Weighted Defect Score: **4.0**.
- Test Suite Pass Rate: **83.33%**.

---

## 4. Deliverables & Reproduction Guide

### Prerequisites
- Python 3.10+ or Anaconda Environment
- Packages: `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `streamlit`, `python-docx`, `joblib`

### Execution Commands
```bat
# 1. Clone / Navigate to project
cd d:\Sqam

# 2. Run entire testing and analysis pipeline (Scripts 01 to 09)
run_all.bat

# 3. Populate final Word report with all real measurements and analysis
pip install python-docx
python src/10_fill_report.py

# 4. Launch interactive 4-tab Streamlit dashboard
streamlit run dashboard/app.py
```
*(Dashboard opens at `http://localhost:8501`)*
