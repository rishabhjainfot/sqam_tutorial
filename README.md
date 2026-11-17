# Battery SOH Prediction: SQA Testing Framework

This SQAM mini-project treats a machine-learning model as a software artifact under test. It audits the battery data, evaluates a Random Forest capacity predictor, checks robustness and regression behavior, and records quality findings.

## Dataset and model

The project uses the NASA Prognostics Center of Excellence lithium-ion battery dataset for batteries B0005, B0006, B0007, and B0018. Each discharge cycle is summarized into features for voltage, current, discharge duration, and temperature range. The target is measured capacity in amp-hours, used here as a proxy for State of Health (SOH).

The model trains on B0005, B0006, and B0007 and evaluates on B0018, keeping the test battery separate from training.

## Run

Use Python 3.10 or newer.

```bash
pip install -r requirements.txt
python src/01_parse_data.py
python src/02_data_quality_audit.py
python src/03_feature_extraction.py
python src/04_train_model.py
python src/05_stage_wise_test.py
python src/06_sensitivity_test.py
python src/07_regression_test.py
python src/08_defect_log.py
python src/09_iso25010_summary.py
python src/10_fill_report.py
streamlit run dashboard/app.py
```

On Windows, `run_all.bat` runs the analysis scripts through step 9. The input dataset is included under `data/raw/`.

## Project contents

- `data/raw/`: original NASA MATLAB files
- `data/processed/`: parsed timestep data and per-cycle features
- `src/`: parsing, audit, feature, model, and test scripts
- `results/`: saved models, predictions, scorecards, and defect logs
- `dashboard/app.py`: four-tab Streamlit dashboard
- `report/`: completed Word report
- `PROJECT_OVERVIEW.md` and `VIVA_PREPARATION_SHEET.md`: architecture and presentation notes
- `CONVERSATION_HISTORY.md` and `SQA_Project_Handoff_Context.md`: project handoff notes

## Current findings

The baseline model's test RMSE is about 0.0291 Ah on B0018. Temperature perturbation checks stayed under the selected 0.05 Ah threshold. The 200-tree model increased RMSE and MAE relative to the 100-tree baseline, so the regression checks detected a performance regression. B0018 contains no cycles below 70% capacity, leaving late-life performance unvalidated; the project reports this as a coverage gap.

Data source: NASA Ames Prognostics Center of Excellence battery dataset. Project source mirrors: https://github.com/anirudhkhatry/SOH-prediction-using-NASA-Dataset
