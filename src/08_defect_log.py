"""
Script 08 — Defect Log Aggregator.

Combines defects from all three test stages into a master defect log.
Computes:
  - Defect Density  = total defects / total test cases × 100
  - Severity-Weighted Defect Score = 3×Critical + 2×Major + 1×Minor

Total test cases:
  Stage-wise  : 3   (one per life stage)
  Sensitivity : 6   (six perturbation levels)
  Regression  : 3   (RMSE, MAE, R²)

Run: python src/08_defect_log.py
Output: results/defect_log.csv
        results/defect_summary.json
"""

import pandas as pd
import numpy as np
import os, json

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
RES_DIR = os.path.join(RUN_DIR, 'results')

TOTAL_TEST_CASES = 12   # 3 stage + 6 sensitivity + 3 regression
SEVERITY_WEIGHTS = {'Critical': 3, 'Major': 2, 'Minor': 1}

SOURCE_FILES = [
    'defects_stage.csv',
    'defects_sensitivity.csv',
    'defects_regression.csv',
]


def main():
    all_defects = []
    for fname in SOURCE_FILES:
        path = os.path.join(RES_DIR, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            if len(df) > 0 and 'defect_id' in df.columns:
                all_defects.append(df)

    if all_defects:
        master = pd.concat(all_defects, ignore_index=True)
    else:
        master = pd.DataFrame(columns=['defect_id', 'test_case', 'severity',
                                       'description', 'root_cause_hypothesis',
                                       'status', 'source'])

    # Reorder columns for readability
    col_order = ['defect_id', 'test_case', 'severity', 'description',
                 'root_cause_hypothesis', 'status', 'source']
    master = master[[c for c in col_order if c in master.columns]]

    master.to_csv(os.path.join(RES_DIR, 'defect_log.csv'), index=False)

    # Compute aggregate metrics
    n_defects = len(master)
    defect_density = round(100 * n_defects / TOTAL_TEST_CASES, 2)
    weighted_score = sum(
        SEVERITY_WEIGHTS.get(sev, 1) for sev in master.get('severity', pd.Series([])).values
    )

    sev_counts = master['severity'].value_counts().to_dict() if 'severity' in master.columns else {}

    summary = {
        'total_test_cases':    TOTAL_TEST_CASES,
        'total_defects':       n_defects,
        'defect_density':      defect_density,
        'severity_weighted_score': weighted_score,
        'severity_breakdown':  sev_counts,
        'pass_rate':           round(100 * (1 - n_defects / TOTAL_TEST_CASES), 2),
    }

    with open(os.path.join(RES_DIR, 'defect_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    print('=== Defect Log Summary ===')
    print(f'  Total test cases        : {TOTAL_TEST_CASES}')
    print(f'  Total defects logged    : {n_defects}')
    print(f'  Defect density          : {defect_density}% (defects per 100 test cases)')
    print(f'  Severity-weighted score : {weighted_score}')
    print(f'  Pass rate               : {summary["pass_rate"]}%')
    print(f'  Severity breakdown      : {sev_counts}')
    print(f'\n  Defect log -> results/defect_log.csv')
    print(f'  Summary    -> results/defect_summary.json')


if __name__ == '__main__':
    main()
