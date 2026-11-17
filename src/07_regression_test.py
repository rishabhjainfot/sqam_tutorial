"""
Script 07 — Regression Testing.

Trains a deliberately modified Model v2 (n_estimators=200, same seed) and
re-runs the full test suite against the saved v1 baseline.

A regression is flagged if any metric WORSENS by more than 5% relative to baseline:
  RMSE_v2 > RMSE_v1 × 1.05   (higher RMSE = worse)
  MAE_v2  > MAE_v1  × 1.05
  R²_v2   < R²_v1  × 0.95   (lower R² = worse)

Run: python src/07_regression_test.py
Output: results/rf_model_v2.joblib
        results/predictions_v2.csv
        results/regression_log.csv
        results/defects_regression.csv
"""

import pandas as pd
import numpy as np
import os, json, joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
PROC_DIR = os.path.join(RUN_DIR, 'data', 'processed')
RES_DIR  = os.path.join(RUN_DIR, 'results')

FEATURE_COLS = ['mean_voltage', 'terminal_voltage', 'discharge_duration',
                'mean_current', 'temp_range']
TARGET_COL   = 'capacity'
REGRESSION_THRESHOLD = 0.05   # 5% relative change triggers a regression


def metrics(y_true, y_pred):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    return round(rmse, 6), round(mae, 6), round(r2, 6)


def main():
    # Load baseline
    with open(os.path.join(RES_DIR, 'baseline.json')) as f:
        baseline = json.load(f)
    b_rmse = baseline['overall']['rmse']
    b_mae  = baseline['overall']['mae']
    b_r2   = baseline['overall']['r2']

    # Load data
    train = pd.read_csv(os.path.join(PROC_DIR, 'features_train.csv'))
    test  = pd.read_csv(os.path.join(PROC_DIR, 'features_test.csv'))
    X_tr, y_tr = train[FEATURE_COLS].values, train[TARGET_COL].values
    X_te, y_te = test[FEATURE_COLS].values, test[TARGET_COL].values

    # Train v2 (deliberately different hyperparameter)
    print('Training Random Forest Regressor v2 (n_estimators=200) ...')
    model_v2 = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model_v2.fit(X_tr, y_tr)
    joblib.dump(model_v2, os.path.join(RES_DIR, 'rf_model_v2.joblib'))

    y_pred_v2 = model_v2.predict(X_te)
    v2_rmse, v2_mae, v2_r2 = metrics(y_te, y_pred_v2)
    print(f'  v2: RMSE={v2_rmse:.4f}  MAE={v2_mae:.4f}  R²={v2_r2:.4f}')

    # Save v2 predictions
    pred_df = test.copy()
    pred_df['predicted_capacity_v2'] = y_pred_v2
    pred_df.to_csv(os.path.join(RES_DIR, 'predictions_v2.csv'), index=False)

    # Build regression log
    test_cases = [
        {
            'test_case_id': 'RT-001',
            'metric': 'Overall RMSE',
            'baseline': b_rmse,
            'post_change': v2_rmse,
            'direction': 'lower_is_better',
        },
        {
            'test_case_id': 'RT-002',
            'metric': 'Overall MAE',
            'baseline': b_mae,
            'post_change': v2_mae,
            'direction': 'lower_is_better',
        },
        {
            'test_case_id': 'RT-003',
            'metric': 'Overall R²',
            'baseline': b_r2,
            'post_change': v2_r2,
            'direction': 'higher_is_better',
        },
    ]

    reg_rows = []
    defects  = []
    defect_start_id = 20

    for tc in test_cases:
        b_val = tc['baseline']
        p_val = tc['post_change']
        if tc['direction'] == 'lower_is_better':
            regressed = p_val > b_val * (1 + REGRESSION_THRESHOLD)
        else:
            regressed = p_val < b_val * (1 - REGRESSION_THRESHOLD)

        status = 'FAIL' if regressed else 'PASS'
        pct_change = round(100 * (p_val - b_val) / (abs(b_val) + 1e-12), 2)

        reg_rows.append({
            'test_case_id':  tc['test_case_id'],
            'metric':        tc['metric'],
            'baseline_v1':   b_val,
            'post_change_v2':p_val,
            'pct_change':    pct_change,
            'status':        status,
        })
        print(f"  {tc['test_case_id']} | {tc['metric']:15s} | "
              f"v1={b_val:.4f} -> v2={p_val:.4f} ({pct_change:+.1f}%) | {status}")

        if regressed:
            defects.append({
                'defect_id':   f'D-{defect_start_id:03d}',
                'test_case':   f"Regression Test — {tc['metric']}",
                'severity':    'Major',
                'description': (f"{tc['metric']} degraded from {b_val:.4f} to {p_val:.4f} "
                                f"({pct_change:+.1f}%) after changing n_estimators 100→200"),
                'root_cause_hypothesis': (
                    'Increasing tree count changed ensemble variance; '
                    'check feature importance shift between v1 and v2.'
                ),
                'status': 'Open',
                'source': 'regression',
            })
            defect_start_id += 1

    reg_df = pd.DataFrame(reg_rows)
    reg_df.to_csv(os.path.join(RES_DIR, 'regression_log.csv'), index=False)
    print(f'\nRegression log saved -> results/regression_log.csv')

    if defects:
        pd.DataFrame(defects).to_csv(os.path.join(RES_DIR, 'defects_regression.csv'), index=False)
        print(f'Regression defects logged -> {len(defects)} defect(s)')
    else:
        pd.DataFrame(columns=['defect_id','test_case','severity','description',
                               'root_cause_hypothesis','status','source']
                     ).to_csv(os.path.join(RES_DIR, 'defects_regression.csv'), index=False)
        print('No regressions detected.')


if __name__ == '__main__':
    main()
