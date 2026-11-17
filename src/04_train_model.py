"""
Script 04 — Train Random Forest Regressor (Model v1) and save baseline metrics.

Trains on features_train.csv, evaluates on features_test.csv.
Saves:
  results/rf_model_v1.joblib   — trained model
  results/baseline.json        — baseline metrics for regression testing
  results/predictions_v1.csv   — per-cycle predictions on test set

Run: python src/04_train_model.py
"""

import pandas as pd
import numpy as np
import os, json, joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
PROC_DIR = os.path.join(RUN_DIR, 'data', 'processed')
RES_DIR  = os.path.join(RUN_DIR, 'results')
os.makedirs(RES_DIR, exist_ok=True)

FEATURE_COLS = ['mean_voltage', 'terminal_voltage', 'discharge_duration',
                'mean_current', 'temp_range']
TARGET_COL   = 'capacity'


def load_data():
    train = pd.read_csv(os.path.join(PROC_DIR, 'features_train.csv'))
    test  = pd.read_csv(os.path.join(PROC_DIR, 'features_test.csv'))
    X_tr = train[FEATURE_COLS].values
    y_tr = train[TARGET_COL].values
    X_te = test[FEATURE_COLS].values
    y_te = test[TARGET_COL].values
    return X_tr, y_tr, X_te, y_te, test


def compute_metrics(y_true, y_pred, label=''):
    rmse = round(np.sqrt(mean_squared_error(y_true, y_pred)), 6)
    mae  = round(mean_absolute_error(y_true, y_pred), 6)
    r2   = round(r2_score(y_true, y_pred), 6)
    if label:
        print(f'  [{label}] RMSE={rmse:.4f}  MAE={mae:.4f}  R²={r2:.4f}')
    return {'rmse': rmse, 'mae': mae, 'r2': r2}


def main():
    print('Loading features ...')
    X_tr, y_tr, X_te, y_te, test_df = load_data()

    print('Training Random Forest Regressor v1 (n_estimators=100) ...')
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    metrics = compute_metrics(y_te, y_pred, label='Overall (v1)')

    # Save model
    model_path = os.path.join(RES_DIR, 'rf_model_v1.joblib')
    joblib.dump(model, model_path)
    print(f'  Model saved -> {model_path}')

    # Save baseline JSON for regression testing
    baseline = {
        'model_version': 'v1',
        'n_estimators': 100,
        'overall': metrics,
    }
    with open(os.path.join(RES_DIR, 'baseline.json'), 'w') as f:
        json.dump(baseline, f, indent=2)
    print(f'  Baseline saved -> results/baseline.json')

    # Save per-cycle predictions
    pred_df = test_df[['battery_id', 'cycle', TARGET_COL]].copy()
    pred_df['predicted_capacity'] = y_pred
    pred_df['residual'] = pred_df[TARGET_COL] - pred_df['predicted_capacity']
    pred_df.to_csv(os.path.join(RES_DIR, 'predictions_v1.csv'), index=False)
    print(f'  Predictions saved -> results/predictions_v1.csv')

    print('\nTraining complete.')


if __name__ == '__main__':
    main()
