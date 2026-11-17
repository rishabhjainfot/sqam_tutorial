@echo off
REM ============================================================
REM  SQA Mini-Project — Run All Scripts in Sequence
REM  Usage: Open "Anaconda Prompt", cd to d:\Sqam, then run this
REM ============================================================

echo.
echo ========== STEP 0: Install dependencies ==========
pip install -r requirements.txt

echo.
echo ========== STEP 1: Parse .mat files ==========
python src/01_parse_data.py

echo.
echo ========== STEP 2: Data Quality Audit ==========
python src/02_data_quality_audit.py

echo.
echo ========== STEP 3: Feature Extraction ==========
python src/03_feature_extraction.py

echo.
echo ========== STEP 4: Train Model v1 ==========
python src/04_train_model.py

echo.
echo ========== STEP 5: Stage-Wise Test ==========
python src/05_stage_wise_test.py

echo.
echo ========== STEP 6: Sensitivity Test ==========
python src/06_sensitivity_test.py

echo.
echo ========== STEP 7: Regression Test ==========
python src/07_regression_test.py

echo.
echo ========== STEP 8: Defect Log ==========
python src/08_defect_log.py

echo.
echo ========== STEP 9: ISO 25010 Summary ==========
python src/09_iso25010_summary.py

echo.
echo ========== ALL DONE — Launch Dashboard ==========
echo Run:  streamlit run dashboard/app.py
echo Then open:  http://localhost:8501
pause
