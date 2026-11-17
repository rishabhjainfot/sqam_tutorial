# SQA Mini-Project: Full Context Handoff

**Purpose of this file:** Paste or upload this into another AI model so it can continue helping from exactly where this conversation left off. Everything decided so far is below. Treat the "Decisions Already Made" section as settled unless the user says otherwise.

---

## 1. Who the User Is

- Rishabh, 4th-year B.Tech Electrical Engineering student at Delhi University (based in Delhi, India).
- Strong EE background, familiar with MATLAB/Simulink.
- **No prior backend/frontend development knowledge**, but wants to learn and wants a basic GUI as a deliverable.
- Comfortable-ish with Python basics; building practical software skills through projects.
- Course: **Software Quality Assurance and Metrics** (tutorial course).

## 2. The Assignment

- A mini-project worth **40 marks**. Scope must be focused and finishable in a short timeframe (about 4 weeks), not a capstone.
- The professor supplied sample titles (handwritten list, transcribed below). They are all "AI/ML fault or defect detection for electrical/embedded systems" topics. The user must reframe one of them through an **SQA lens**.
- The user rejected generic software-only ideas (e.g., firmware cyclomatic complexity on random GitHub repos) and asked for something that clearly relates to **electrical engineering and the professor's list**.

### Professor's sample titles (transcribed from the user's photo of handwritten notes, headed "ECE")
1. AI-based Embedded Firmware Quality Prediction (predict firmware modules likely to fail/contain defects; predicts firmware risk score)
2. Predictive Maintenance of Motors using Vibration and Current Signals (detect motor faults before failure; metrics: accuracy, F1, false alarm rate, detection time)
3. AI-based Lithium-Ion Battery Fault Detection (detect battery faults from voltage/current/temperature data)
4. Battery State-of-Health Prediction for EVs (predict remaining battery health before significant degradation occurs)
5. Solar PV Fault Detection & Quality Monitoring (automatically identify electrical faults in photovoltaic systems)
6. AI-Based Inverter Fault Diagnosis (identify open-circuit and other inverter faults automatically)
7. Semiconductor/Wafer Defect Detection using deep learning (struck through in the note)
8. PCB/PCBA Defect Detection using computer vision (soldering/manufacturing defects)
9. Unknown Semiconductor Defect Detection Using Active Learning (known and previously unseen defect patterns)

(A margin note at the top right about sensors/battery backup/LoRa is partly illegible and was not used.)

### Milestone 1 submission requirements (from a screenshot of the professor's instructions)
The first submission must contain:
1. Abstract
2. Introduction
3. Related Work
4. Proposed Framework
5. Result Tables and Analysis ("preferable as implementation is already done")

The user asked for roughly **2 pages per section**.

---

## 3. Decisions Already Made

### Chosen project: "Idea B" (battery State-of-Health, maps to professor's samples #3/#4)

**Working title:** *An SQA Testing Framework for Data Quality and Model Validation in Battery State-of-Health Prediction Models*

**Core framing:** The project does NOT try to build the most accurate SOH model. It treats a simple ML SOH model as a **software artifact under test** and builds a repeatable SQA process to certify whether the model and its training data are trustworthy, using the rigor applied to safety-critical embedded software.

**Other ideas considered and not chosen:**
- Idea A: SQA test framework for AI motor fault detection (CWRU bearing dataset; classification; robustness/noise testing; defect logging). Close runner-up.
- Idea C: Fault-injection test plan for a solar PV fault detection model (Simulink-generated data).
- Earlier generic ideas (cyclomatic complexity on firmware, Simulink Model Advisor metrics, CI/CD quality gates, software reliability growth models, mutation testing) were set aside as too far from the EE domain.

### Dataset and model
- Dataset: **NASA Prognostics Center of Excellence (PCoE) Li-ion battery dataset** (voltage, current, temperature, capacity over charge/discharge cycles; `.mat` files).
- Model: **Random Forest Regressor**, deliberately simple, predicting capacity/SOH from per-cycle features (mean/terminal voltage, discharge duration, mean current, temperature range).
- Split **by battery identity, not random rows**, to avoid data leakage.
- Python stack: pandas, numpy, scipy, scikit-learn, matplotlib.

### GUI
- **Streamlit** (pure Python, no separate frontend/backend). Four tabs:
  1. Data Quality Scorecard
  2. Model Performance by degradation stage
  3. Sensitivity Test (interactive slider that perturbs temperature and shows live prediction shift)
  4. Regression Test Log

---

## 4. Aim, Objectives, Scope

**Aim:** To design, implement, and empirically validate a Software Quality Assurance testing framework for a machine learning-based Lithium-ion battery State-of-Health prediction model, by systematically evaluating both the quality of the underlying training data and the reliability, robustness, and regression-stability of the predictive model, using established data quality and software testing metrics, and presenting the results through an interactive dashboard.

**Objectives:**
1. Data quality assessment of the NASA PCoE dataset (Wang & Strong dimensions: completeness, consistency, accuracy, timeliness) before modelling.
2. Develop the Random Forest SOH model as the artifact under test.
3. Stage-wise functional testing: RMSE/MAE/R² separately for early-life (>90% capacity), mid-life (70-90%), late-life (<70%).
4. Robustness/sensitivity testing: perturb inputs (e.g., temperature by ±5%, ±10%, ±20%) and measure output shift.
5. Regression testing: save baseline results, make one deliberate model change, re-run the suite, diff and flag regressions.
6. Defect logging (ID, test case, severity, root-cause hypothesis) and aggregate metrics (defect density per 100 test cases, severity-weighted defect score, regression pass rate).
7. Map findings to ISO/IEC 25010 (Functional Suitability and Reliability).
8. Streamlit dashboard presenting all of the above.

**Scope statement:** One dataset, one simple model class, no deep learning, no state-of-the-art accuracy chase, no real-world field data validation. The contribution is the SQA methodology around the model, intended to generalize to other ML-based fault/health prediction systems in electrical/embedded contexts. This pre-empts the viva question "why not a better model?"

---

## 5. How SQA Is Applied (explanation the user asked for)

- **Data quality audit** = treating the dataset as a software input artifact subject to QA ("garbage in, garbage out" formalized with Wang & Strong).
- **Stage-wise testing** = stratified functional testing, so an average error number cannot hide failure in the safety-critical late-life region.
- **Sensitivity testing** = adaptation of boundary-value/stress testing to a continuous-output regression model.
- **Regression testing** = used in the literal SQA sense: after any model change, confirm nothing that previously passed now fails.
- **Defect logging** = each out-of-threshold failure is logged like a bug-tracker entry (ID, severity, root cause, status).
- **ISO/IEC 25010 mapping** = report findings in standard software quality vocabulary (Functional Suitability = error metrics; Reliability = sensitivity coefficients + regression pass rate). Data quality is framed as a precondition for both.

---

## 6. Reference Papers

All were located via web search. **Please re-verify volume/page/year details on Google Scholar before final submission** (see notes).

1. **Domain foundation:** "AI-Driven Prognostics for State of Health Prediction in Li-ion Batteries: A Comprehensive Analysis with Validation." arXiv:2504.05728 (2025). Reviews SOH prediction on CALCE, NASA PCoE, and UDDS datasets; used to justify the dataset and benchmark reasonable performance.
2. **Data quality framework:** Wang, R. Y., & Strong, D. M. (1996). Beyond accuracy: What data quality means to data consumers. *Journal of Management Information Systems*, 12(4), 5-33. https://doi.org/10.1080/07421222.1996.11518099
   - BibTeX key used: `wang1996beyond`. Project uses the **Intrinsic DQ** dimensions (accuracy, completeness, consistency, timeliness).
3. **ML testing methodology:** Zhang, J. M., Harman, M., Ma, L., & Liu, Y. (2020). Machine learning testing: Survey, landscapes and horizons. *IEEE Transactions on Software Engineering*. (arXiv:1906.10742; DOI 10.1109/TSE.2019.2962027.) Surveys 144 papers; covers correctness, robustness, fairness, testing components and workflow.
   - Note: earlier in the chat this was cited as 48(1), 1-36, 2020. The early-access year is 2019/2020 and the journal issue is likely 2022. Check Google Scholar and cite consistently.
4. **ML quality model / ISO 25010 for ML:** Siebert, J., et al. (2021). Construction of a quality model for machine learning systems. *Software Quality Journal*. https://link.springer.com/article/10.1007/s11219-021-09557-y (Full author list was not confirmed in search results; verify.)
5. **Standard:** ISO/IEC 25010:2011, SQuaRE system and software quality models (reference directly for characteristic names).

Citation formats offered to the user: APA 7, IEEE, and BibTeX (for Wang & Strong). The user can request the same for the others.

---

## 7. Research Gap / How the Project Differs From Existing Work

Honest positioning: not a new algorithm or theory, but a **novel combination and application** of three established frameworks to an EE health-monitoring problem.

| Source | Primary focus | Gap | This project's contribution |
|---|---|---|---|
| Domain SOH papers (NASA PCoE; SVR/RF/CNN/LSTM/Transformer) | Minimize RMSE/MAE | No data quality audit; no stage-wise, sensitivity, or regression testing | Treats the model as an artifact under test |
| Wang & Strong (1996) | Generic data quality dimensions (business data) | No link to ML or sensor data | Applies it to sensor-generated ML training data |
| Zhang et al. (2020) | Survey of ML testing techniques | Survey only; examples from autonomous driving/vision/NLP | Implements a concrete subset for battery health monitoring |
| Siebert et al. (2021) | Prescriptive ML quality-model methodology | Abstract; no worked numerical case | Builds and runs a quality model end-to-end |
| ISO/IEC 25010 | Generic quality taxonomy | Not ML-specific | Maps ML test results to standard vocabulary |

**One-paragraph gap statement:** While extensive research exists on maximizing SOH prediction accuracy, and separate work exists on data quality frameworks and ML testing methodologies, no identified study integrates data quality auditing, stage-wise and sensitivity-based model testing, and regression testing into a single applied SQA framework for battery health prediction in an electrical engineering context. This project addresses that gap at a scale appropriate to an undergraduate SQA tutorial.

---

## 8. Four-Week Plan

**Week 1 (Days 1-7): Setup, data, data quality audit**
- Download NASA PCoE data; set up Python environment; parse `.mat` files to a clean CSV (cycle, voltage, current, temperature, capacity).
- Read Wang & Strong; write a half-page summary of the four Intrinsic DQ dimensions.
- Build the audit script: completeness (% missing), consistency (units, duplicate timestamps), accuracy (z-score/IQR outliers), timeliness (sampling interval regularity).
- Produce the Data Quality Scorecard (Deliverable 1).

**Week 2 (Days 8-14): Model + baseline testing**
- Feature engineering per cycle; train Random Forest; split by battery.
- Baseline RMSE/MAE/R².
- Stage-wise testing (early/mid/late life) with a bar chart.

**Week 3 (Days 15-21): Sensitivity, regression, defects**
- Sensitivity testing (perturb temperature, plot perturbation vs prediction change).
- Regression testing (save JSON baseline, change the model, re-run, diff script).
- Log defects formally; compile the ISO 25010 quality summary.

**Week 4 (Days 22-28): GUI + report**
- Build the four-tab Streamlit dashboard.
- Write the report: Introduction, Methodology, Results, ISO 25010 discussion, Conclusion.
- Polish charts, dry-run the viva demo, buffer day.

---

## 9. Current Status (as of the end of this conversation)

**Done:**
- Idea selection, aim/objectives/scope, paper selection, research-gap analysis, 4-week plan.
- A Word document, **`SQA_MiniProject_Report_Milestone1.docx`** (9 pages, A4), containing the title, Abstract, 1. Introduction, 2. Related Work (with the comparison table), 3. Proposed Framework, and 4. Result Tables and Analysis. **Share this .docx alongside this file** if the next model needs the exact report text.

**Not done (important):**
- **No implementation has been run yet.** Section 4 of the report contains only **placeholder tables** ("[ to be filled after implementation ]"): Data Quality Scorecard, Stage-Wise Performance, Sensitivity Results, Regression Test Log, Defect Log, and the ISO 25010 summary narrative.
- No code has been written yet. The assistant offered to write the Week 1 data quality audit script next.
- No real results, numbers, or charts exist. **Do not invent results.** Section 4 must be filled with measured values from real runs.

---

## 10. Suggested Next Steps for the Next Model

1. Write the **Week 1 data quality audit script** (parse NASA PCoE `.mat` files, compute the four DQ dimension scores per battery, output a scorecard table/CSV). This populates Table 4.1.
2. Then feature extraction, Random Forest training, stage-wise evaluation, sensitivity script, regression/baseline-diff script, defect log generator, and the Streamlit app, in that order.
3. Help the user replace the placeholders in Section 4 with real numbers and write the analysis paragraphs.
4. Offer to draft the remaining formatted references (IEEE/APA/BibTeX) for papers 1, 3, and 4 once their details are verified.
5. Offer a viva Q&A prep sheet (likely questions: "what's new here," "why Random Forest," "why not deep learning," "how did you define a defect," "how is ISO 25010 used").

## 11. Interaction Style Notes

- The user wants **concrete, step-by-step, plain-language** guidance and clear definitions of exactly what has to be done, and pushed back when earlier answers drifted from EE relevance.
- The user is a beginner at web/app development; explain Streamlit code simply and keep scope small.
- Be honest about what is and isn't finished, and flag anything that needs verification (especially citations).
