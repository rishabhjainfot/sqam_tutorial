"""
Script 06 — Sensitivity / Robustness Testing.

Perturbs the 'temperature' feature (via temp_range) by ±5%, ±10%, ±20%
across all test cycles and measures the resulting shift in predicted capacity.

A "sensitive" flag is raised if max ΔSOH > 0.05 Ah for a 10% perturbation
(equivalent to ~5% SOH shift for a ~1 Ah cell).

Perturbation simulates real-world sensor noise or measurement uncertainty.

Run: python src/06_sensitivity_test.py
Output: results/sensitivity.csv
        results/defects_sensitivity.csv
"""

import pandas as pd
import numpy as np
import os, joblib

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
RES_DIR  = os.path.join(os.path.dirname(__file__), '..', 'results')

FEATURE_COLS = ['mean_voltage', 'terminal_voltage', 'discharge_duration',
                'mean_current', 'temp_range']
TARGET_COL   = 'capacity'

PERTURBATIONS = [-0.20, -0.10, -0.05, +0.05, +0.10, +0.20]  # fraction of original value
SENSITIVITY_FLAG_THRESHOLD = 0.05  # Ah — flag if max ΔSOH > this at ±10%


def main():
    model_path = os.path.join(RES_DIR, 'rf_model_v1.joblib')
    if not os.path.exists(model_path):
        print('rf_model_v1.joblib not found. Run 04_train_model.py first.')
        return

    model   = joblib.load(model_path)
    test_df = pd.read_csv(os.path.join(PROC_DIR, 'features_test.csv'))
    X_base  = test_df[FEATURE_COLS].values
    y_base_pred = model.predict(X_base)   # baseline predictions

    temp_col_idx = FEATURE_COLS.index('temp_range')

    rows    = []
    defects = []
    defect_start_id = 10  # leave room for stage defects starting at D-001

    for pct in PERTURBATIONS:
        X_pert = X_base.copy()
        X_pert[:, temp_col_idx] = X_base[:, temp_col_idx] * (1 + pct)

        y_pert_pred = model.predict(X_pert)
        delta       = np.abs(y_pert_pred - y_base_pred)

        mean_delta = float(np.mean(delta))
        max_delta  = float(np.max(delta))
        pct_label  = f'{pct:+.0%}'

        flag = (abs(pct) == 0.10) and (max_delta > SENSITIVITY_FLAG_THRESHOLD)
        status = 'SENSITIVE' if flag else 'OK'

        row = {
            'perturbation':     pct_label,
            'perturbation_frac': pct,
            'mean_delta_capacity': round(mean_delta, 6),
            'max_delta_capacity':  round(max_delta, 6),
            'status': status,
        }
        rows.append(row)
        print(f"  Temp perturbation {pct_label:>5s}: "
              f"mean ΔSOH={mean_delta:.4f} Ah  max ΔSOH={max_delta:.4f} Ah  [{status}]")

        if flag:
            defects.append({
                'defect_id':   f'D-{defect_start_id:03d}',
                'test_case':   f'Sensitivity Test — temp_range {pct_label}',
                'severity':    'Major',
                'description': (f'max ΔSOH={max_delta:.4f} Ah exceeds threshold '
                                f'{SENSITIVITY_FLAG_THRESHOLD} Ah at ±10% temperature perturbation'),
                'root_cause_hypothesis': (
                    'Model relies heavily on temp_range feature; '
                    'consider adding temperature regularization or feature scaling.'
                ),
                'status': 'Open',
                'source': 'sensitivity',
            })
            defect_start_id += 1

    sens_df = pd.DataFrame(rows)
    sens_df.to_csv(os.path.join(RES_DIR, 'sensitivity.csv'), index=False)
    print(f'\nSensitivity results saved -> results/sensitivity.csv')

    if defects:
        pd.DataFrame(defects).to_csv(os.path.join(RES_DIR, 'defects_sensitivity.csv'), index=False)
        print(f'Sensitivity defects logged -> results/defects_sensitivity.csv ({len(defects)} defect(s))')
    else:
        pd.DataFrame(columns=['defect_id','test_case','severity','description',
                               'root_cause_hypothesis','status','source']
                     ).to_csv(os.path.join(RES_DIR, 'defects_sensitivity.csv'), index=False)
        print('No sensitivity defects found.')


if __name__ == '__main__':
    main()
