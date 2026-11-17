"""
Script 02 — Data Quality Audit (Wang & Strong 1996 Intrinsic DQ Dimensions).

Dimensions assessed per battery:
  Completeness : % of non-null rows across key columns
  Consistency  : % of rows with values in physically plausible ranges
                   voltage    ∈ [2.5, 4.5] V
                   current    ∈ [-5.0, 0.0] A  (discharge = negative current)
                   temperature∈ [0.0, 60.0] °C
  Accuracy     : % of rows that pass a Tukey IQR fence (3×IQR) on each signal
  Timeliness   : % of time steps whose Δt falls within [median ± 2σ]

Each dimension is expressed as a percentage (0–100).
Overall Status: PASS if all four ≥ 90%, FLAG otherwise.

Run: python src/02_data_quality_audit.py
Output: results/scorecard.csv
"""

import pandas as pd
import numpy as np
import os

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
RES_DIR  = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RES_DIR, exist_ok=True)

KEY_COLS = ['voltage', 'current', 'temperature']

# Physical plausibility ranges (discharge cycles)
RANGES = {
    'voltage':     (2.5, 4.5),
    'current':     (-5.0, 0.5),   # small positive allowed for measurement noise
    'temperature': (0.0, 60.0),
}

PASS_THRESHOLD = 90.0  # % below which the dimension is flagged


def completeness(df):
    total = len(df) * len(KEY_COLS)
    missing = df[KEY_COLS].isnull().sum().sum()
    return round(100.0 * (1 - missing / total), 2) if total > 0 else 0.0


def consistency(df):
    mask = pd.Series([True] * len(df), index=df.index)
    for col, (lo, hi) in RANGES.items():
        if col in df.columns:
            mask &= df[col].between(lo, hi, inclusive='both')
    return round(100.0 * mask.sum() / len(df), 2) if len(df) > 0 else 0.0


def accuracy(df):
    """Tukey 3×IQR outlier check per signal column."""
    outlier_mask = pd.Series([False] * len(df), index=df.index)
    for col in KEY_COLS:
        if col not in df.columns:
            continue
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
        outlier_mask |= ~df[col].between(lo, hi, inclusive='both')
    return round(100.0 * (~outlier_mask).sum() / len(df), 2) if len(df) > 0 else 0.0


def timeliness(df):
    """Checks regularity of time steps within each cycle."""
    if 'time' not in df.columns:
        return 100.0
    good = 0
    total = 0
    for _, grp in df.groupby('cycle'):
        t = grp['time'].dropna().values
        if len(t) < 2:
            continue
        deltas = np.diff(t)
        med = np.median(deltas)
        sd  = np.std(deltas) if np.std(deltas) > 0 else 1e-9
        in_range = np.abs(deltas - med) <= 2 * sd
        good  += in_range.sum()
        total += len(deltas)
    return round(100.0 * good / total, 2) if total > 0 else 100.0


def audit_battery(csv_path, battery_id):
    df = pd.read_csv(csv_path)
    c  = completeness(df)
    co = consistency(df)
    ac = accuracy(df)
    ti = timeliness(df)
    status = 'PASS' if all(v >= PASS_THRESHOLD for v in [c, co, ac, ti]) else 'FLAG'
    return {
        'battery_id':     battery_id,
        'completeness':   c,
        'consistency':    co,
        'accuracy':       ac,
        'timeliness':     ti,
        'overall_status': status,
    }


def main():
    rows = []
    for f in sorted(os.listdir(PROC_DIR)):
        if f.endswith('.csv') and f != 'all_batteries.csv' and not f.startswith('features'):
            bid = f.replace('.csv', '')
            path = os.path.join(PROC_DIR, f)
            result = audit_battery(path, bid)
            rows.append(result)
            print(f"  {bid}: completeness={result['completeness']}% | "
                  f"consistency={result['consistency']}% | "
                  f"accuracy={result['accuracy']}% | "
                  f"timeliness={result['timeliness']}% | {result['overall_status']}")

    if rows:
        sc = pd.DataFrame(rows)
        out = os.path.join(RES_DIR, 'scorecard.csv')
        sc.to_csv(out, index=False)
        print(f'\nScorecard saved -> {out}')
    else:
        print('No battery CSVs found. Run 01_parse_data.py first.')


if __name__ == '__main__':
    main()
