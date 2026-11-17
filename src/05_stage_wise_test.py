"""
Script 05 — Stage-wise functional testing.

Partitions test cycles by SOH (capacity relative to initial capacity):
  Early life : capacity >= 90% of initial   (fresh battery)
  Mid life   : 70% <= capacity < 90%        (normal degradation)
  Late life  : capacity < 70%               (significant degradation)

Computes RMSE, MAE, R² per stage.
A stage is FLAGGED as a defect if:
  - Its RMSE > 1.5 × overall RMSE, OR
  - R² < 0.80

Run: python src/05_stage_wise_test.py
Output: results/stage_perf.csv
        results/defects_stage.csv  (preliminary defect entries from this stage)
"""

import pandas as pd
import numpy as np
import os, json
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
RES_DIR  = os.path.join(os.path.dirname(__file__), '..', 'results')

RMSE_FLAG_MULTIPLIER = 1.5
R2_FLAG_THRESHOLD    = 0.80


def classify_stage(capacity, initial_capacity):
    ratio = capacity / initial_capacity
    if ratio >= 0.90:
        return 'Early Life (>90%)'
    elif ratio >= 0.70:
        return 'Mid Life (70-90%)'
    else:
        return 'Late Life (<70%)'


def metrics(y_true, y_pred):
    if len(y_true) < 2:
        return {'rmse': np.nan, 'mae': np.nan, 'r2': np.nan}
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    return {'rmse': round(rmse, 6), 'mae': round(mae, 6), 'r2': round(r2, 6)}


def main():
    pred_path = os.path.join(RES_DIR, 'predictions_v1.csv')
    if not os.path.exists(pred_path):
        print('predictions_v1.csv not found. Run 04_train_model.py first.')
        return

    df = pd.read_csv(pred_path)
    initial_capacity = df['capacity'].max()  # first (highest) capacity = reference

    df['stage'] = df['capacity'].apply(lambda c: classify_stage(c, initial_capacity))

    # Load overall RMSE from baseline
    baseline_path = os.path.join(RES_DIR, 'baseline.json')
    with open(baseline_path) as f:
        baseline = json.load(f)
    overall_rmse = baseline['overall']['rmse']

    rows = []
    defects = []
    defect_id = 1

    stage_order = ['Early Life (>90%)', 'Mid Life (70-90%)', 'Late Life (<70%)']
    for stage in stage_order:
        sub = df[df['stage'] == stage]
        n   = len(sub)
        m   = metrics(sub['capacity'].values, sub['predicted_capacity'].values)

        flags = []
        if not np.isnan(m['rmse']) and m['rmse'] > RMSE_FLAG_MULTIPLIER * overall_rmse:
            flags.append(f"RMSE ({m['rmse']:.4f}) > 1.5× overall ({overall_rmse:.4f})")
        if not np.isnan(m['r2']) and m['r2'] < R2_FLAG_THRESHOLD:
            flags.append(f"R² ({m['r2']:.4f}) < {R2_FLAG_THRESHOLD}")

        status = 'FAIL' if flags else 'PASS'
        severity = 'Critical' if 'Late Life' in stage and flags else ('Major' if flags else '-')

        row = {
            'stage':  stage,
            'n_cycles': n,
            'rmse':  m['rmse'],
            'mae':   m['mae'],
            'r2':    m['r2'],
            'status': status,
        }
        rows.append(row)
        print(f"  {stage:25s} | n={n:3d} | RMSE={m['rmse']:.4f} | MAE={m['mae']:.4f} | "
              f"R²={m['r2']:.4f} | {status}")

        if flags:
            defects.append({
                'defect_id':    f'D-{defect_id:03d}',
                'test_case':    f'Stage-Wise Test — {stage}',
                'severity':     severity,
                'description':  '; '.join(flags),
                'root_cause_hypothesis': (
                    'Insufficient training samples in this degradation stage; '
                    'feature set may not capture late-stage voltage plateau collapse.'
                ),
                'status': 'Open',
                'source': 'stage_wise',
            })
            defect_id += 1

    stage_df = pd.DataFrame(rows)
    stage_df.to_csv(os.path.join(RES_DIR, 'stage_perf.csv'), index=False)
    print(f'\nStage performance saved -> results/stage_perf.csv')

    if defects:
        pd.DataFrame(defects).to_csv(os.path.join(RES_DIR, 'defects_stage.csv'), index=False)
        print(f'Stage defects logged -> results/defects_stage.csv ({len(defects)} defect(s))')
    else:
        pd.DataFrame(columns=['defect_id','test_case','severity','description',
                               'root_cause_hypothesis','status','source']
                     ).to_csv(os.path.join(RES_DIR, 'defects_stage.csv'), index=False)
        print('No stage-wise defects found.')


if __name__ == '__main__':
    main()
