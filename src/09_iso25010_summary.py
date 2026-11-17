"""
Script 09 — ISO/IEC 25010 Quality Summary.

Maps all measured test results to the two relevant ISO/IEC 25010 characteristics:
  Functional Suitability (Functional Correctness sub-characteristic)
    <- stage-wise RMSE/MAE/R²
  Reliability (Fault Tolerance sub-characteristic)
    <- sensitivity coefficients, regression pass rate

Writes results/iso_summary.json for use in dashboard and report.

Run: python src/09_iso25010_summary.py
Output: results/iso_summary.json  (overwrites the placeholder from defect_log)
"""

import pandas as pd
import numpy as np
import os, json

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
RES_DIR = os.path.join(RUN_DIR, 'results')


def load_json(fname):
    path = os.path.join(RES_DIR, fname)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_csv(fname):
    path = os.path.join(RES_DIR, fname)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def main():
    baseline    = load_json('baseline.json')
    defect_sum  = load_json('defect_summary.json')
    stage_df    = load_csv('stage_perf.csv')
    sens_df     = load_csv('sensitivity.csv')
    reg_df      = load_csv('regression_log.csv')

    # --- Functional Suitability ---
    overall_metrics = baseline.get('overall', {})

    stage_summary = []
    if not stage_df.empty:
        for _, row in stage_df.iterrows():
            stage_summary.append({
                'stage':  row.get('stage', ''),
                'rmse':   row.get('rmse', None),
                'mae':    row.get('mae',  None),
                'r2':     row.get('r2',   None),
                'status': row.get('status', ''),
            })

    # --- Reliability ---
    # Sensitivity: pick the ±10% rows as representative
    sens_10 = {}
    if not sens_df.empty:
        sub = sens_df[sens_df['perturbation_frac'].abs().round(2) == 0.10]
        if not sub.empty:
            sens_10 = {
                'mean_delta_capacity_at_10pct': float(sub['mean_delta_capacity'].mean()),
                'max_delta_capacity_at_10pct':  float(sub['max_delta_capacity'].max()),
                'status': sub['status'].iloc[0],
            }

    reg_pass_rate = None
    if not reg_df.empty and 'status' in reg_df.columns:
        reg_pass_rate = round(100 * (reg_df['status'] == 'PASS').sum() / len(reg_df), 1)

    iso_summary = {
        'standard': 'ISO/IEC 25010:2011',
        'characteristics': {
            'Functional Suitability': {
                'sub_characteristic': 'Functional Correctness',
                'rationale': (
                    'The model is assessed for correctness of SOH predictions '
                    'across all degradation stages. RMSE and MAE quantify prediction error; '
                    'R² quantifies explanatory power.'
                ),
                'overall': overall_metrics,
                'stage_wise': stage_summary,
                'assessment': (
                    'PASS' if all(s.get('status') == 'PASS' for s in stage_summary)
                    else 'PARTIAL — some degradation stages fail quality thresholds'
                ),
            },
            'Reliability': {
                'sub_characteristic': 'Fault Tolerance',
                'rationale': (
                    'Reliability is assessed via (a) sensitivity to input perturbation '
                    'representing sensor noise, and (b) regression testing ensuring model '
                    'changes do not silently degrade performance.'
                ),
                'sensitivity_at_10pct_temperature_perturbation': sens_10,
                'regression_pass_rate': reg_pass_rate,
                'assessment': (
                    'PASS' if (reg_pass_rate is not None and reg_pass_rate == 100.0)
                    else 'PARTIAL — see regression log for details'
                ),
            },
        },
        'defect_summary': defect_sum,
    }

    out_path = os.path.join(RES_DIR, 'iso_summary.json')
    with open(out_path, 'w') as f:
        json.dump(iso_summary, f, indent=2)

    print('=== ISO/IEC 25010 Quality Summary ===')
    fs = iso_summary['characteristics']['Functional Suitability']
    re = iso_summary['characteristics']['Reliability']
    print(f"  Functional Suitability  : {fs['assessment']}")
    print(f"  Reliability             : {re['assessment']}")
    print(f'  Summary saved -> {out_path}')


if __name__ == '__main__':
    main()
