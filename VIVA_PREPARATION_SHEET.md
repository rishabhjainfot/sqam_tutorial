# SQA Mini-Project — Viva Voce Preparation Sheet

**Project Title:** *An SQA Testing Framework for Data Quality and Model Validation in Battery State-of-Health Prediction Models*  
**Course:** Software Quality Assurance and Metrics (SQAM)  
**Student:** Rishabh (B.Tech Electrical Engineering)

---

## 🎯 The Core Pitch (Say this in 30 seconds when asked "What did you do?")

> *"In electrical engineering, machine learning papers focus almost exclusively on chasing lower RMSE. However, in safety-critical systems like an EV Battery Management System, an average RMSE doesn't tell you whether the training data was corrupt, whether the model fails silently in late degradation stages, whether sensor noise breaks predictions, or whether an update silently caused a regression.*  
> *In this project, I treated the ML battery model as a **software artifact under test**. I designed and implemented a full SQA framework covering:*  
> *1) A Data Quality Audit using Wang & Strong's 4 dimensions;*  
> *2) Stage-Wise Functional Testing across degradation regimes;*  
> *3) Input Sensitivity & Robustness Stress Testing;*  
> *4) Automated Regression Testing; and*  
> *5) Formal Defect Logging mapped to ISO/IEC 25010 standards, demonstrated through an interactive Streamlit dashboard."*

---

## ❓ Top 8 Viva Questions & Exact Answers

### Q1: "Why did you use Random Forest instead of deep learning (LSTM, CNN, Transformer)?"
* **Answer:**  
  *"The objective of this project is not to invent a state-of-the-art predictive algorithm, but to build and evaluate an **SQA testing and certification framework**. In Software Quality Assurance, the artifact under test is deliberately kept deterministic and interpretable so that failures can be isolated to data anomalies, sensor perturbations, or hyperparameter regressions rather than opaque neural network training stochasticity. Random Forest provided an excellent baseline (R² = 0.9644, RMSE = 0.0291 Ah) while training in seconds, allowing our full test suite to run deterministically."*

---

### Q2: "How did you prevent data leakage in your model evaluation?"
* **Answer:**  
  *"Standard random k-fold or random train/test splits cause severe data leakage in time-series battery data, because cycles from the same battery cell share internal chemical characteristics. We enforced a strict **split by physical battery identity**: cells B0005, B0006, and B0007 were used exclusively for training, while battery B0018 was completely held out for testing. This tests true out-of-sample generalization across physical cells."*

---

### Q3: "Explain how you evaluated Data Quality before training."
* **Answer:**  
  *"We applied the classic **Wang & Strong (1996) Intrinsic Data Quality** framework directly to the raw sensor telemetry across four dimensions:*  
  * * **Completeness (100.0%):** Verified zero null readings in discharge cycles.*  
  * * **Consistency (99.2%–99.9%):** Verified that voltage, current, and temperature remained within physically valid operational envelopes (2.5–4.5 V, -5 to 0 A, 0–60 °C).*  
  * * **Accuracy (87.9%–94.8%):** Applied Tukey's 3×IQR fence outlier detection. Batteries B0005 (89.5%) and B0006 (87.9%) were flagged due to transient transition spikes.*  
  * * **Timeliness (91.7%–97.2%):** Verified uniform sampling interval regularity ($\Delta t \in \text{median} \pm 2\sigma$).  
  *This acts as an automated Quality Gate prior to training."*

---

### Q4: "What is Stage-Wise Testing and what did your results reveal?"
* **Answer:**  
  *"A single aggregate error metric can hide catastrophic failures in specific operational phases. We stratified battery B0018's cycles into Early Life (>90% capacity) and Mid Life (70%–90% capacity).*  
  * * **Early Life:** RMSE was 0.0130 Ah ($R^2 = 0.9463$).*  
  * * **Mid Life:** RMSE rose to 0.0335 Ah ($R^2 = 0.8855$).*  
  * * **Late Life (<70%):** Contained zero test cycles because the experimental protocol for cell B0018 was terminated before 70% capacity.*  
  * * **Key SQA finding:** Our stage-wise test explicitly revealed a **coverage deficit**. Without this SQA stratification, an engineer looking only at overall $R^2 = 0.9644$ would falsely assume the model was verified for end-of-life battery safety decisions."*

---

### Q5: "How does your Sensitivity Testing work and what does it measure?"
* **Answer:**  
  *"Sensitivity testing adapts software stress and boundary-value testing to continuous-output machine learning. We perturbed the `temp_range` feature by $\pm 5\%$, $\pm 10\%$, and $\pm 20\%$ to simulate thermocouple degradation and ambient sensor noise.*  
  *Under nominal $\pm 10\%$ noise, the mean shift in predicted SOH was only $0.0071\text{ Ah}$, with a maximum deviation of $0.0186\text{ Ah}$. Even under extreme $\pm 20\%$ perturbation, maximum error was $0.0206\text{ Ah}$—well below our safety-critical limit of $0.0500\text{ Ah}$. The model passed this robustness quality gate."*

---

### Q6: "Why did your Regression Test fail, and why is that a good thing?"
* **Answer:**  
  *"In SQA, detecting regressions proves the testing harness works! When upgrading from model v1 ($100$ trees) to model v2 ($200$ trees), common intuition suggests more trees should improve performance.*  
  *However, our automated regression test caught that **RMSE degraded by +8.1%** and **MAE degraded by +6.9%**, exceeding our 5% tolerance threshold. We formally logged two Major defects (`D-020` and `D-021`). This proved that without an SQA regression suite, a seemingly harmless hyperparameter tweak would have silently degraded production BMS performance."*

---

### Q7: "How did you calculate your Defect Density and SQA Metrics?"
* **Answer:**  
  *"Across 12 formal test cases (3 stage-wise + 6 sensitivity + 3 regression), 2 failed, resulting in:*  
  * * **Test Pass Rate:** $\frac{10}{12} = 83.33\%$*  
  * * **Defect Density:** $\frac{2}{12} \times 100 = 16.67\text{ defects per 100 test cases}$*  
  * * **Severity-Weighted Defect Score:** $2 \times 2 (\text{Major}) = 4.0$*  
  *These quantitative metrics provide objective release criteria."*

---

### Q8: "How does this map to the ISO/IEC 25010 software standard?"
* **Answer:**  
  *"We mapped our findings to two primary characteristics of ISO/IEC 25010 (SQuaRE):*  
  * * **Functional Suitability (Functional Correctness):** Evaluated via Stage-Wise RMSE, MAE, and $R^2$. Status: **PASS** for tested regimes.*  
  * * **Reliability (Fault Tolerance & Maturity):** Evaluated via input sensitivity (Fault Tolerance: **PASS**) and regression stability (Maturity: **PARTIAL** due to v2 regression).*  
  *This frames machine learning validation in internationally recognized software quality vocabulary."*
