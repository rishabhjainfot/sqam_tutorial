"""
Script 03 — Feature extraction: one row per discharge cycle.

Features extracted from raw timestep data per cycle:
  mean_voltage      : mean of voltage readings
  terminal_voltage  : mean of last 5 voltage readings (end-of-discharge voltage)
  discharge_duration: total time span of cycle (seconds)
  mean_current      : mean of |current| readings
  temp_range        : max(temperature) - min(temperature)
  capacity          : measured capacity (Ah) — this is the target / SOH proxy

Train/test split BY BATTERY (not random rows) to prevent data leakage:
  Train : B0005, B0006, B0007
  Test  : B0018

Run: python src/03_feature_extraction.py
Output: data/processed/features_train.csv, features_test.csv
"""

import pandas as pd
import numpy as np
import os

PROC_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')

TRAIN_BATTERIES = ['B0005', 'B0006', 'B0007']
TEST_BATTERIES  = ['B0018']


def extract_features(df):
    """Aggregate raw timestep rows into one row per (battery_id, cycle)."""
    rows = []
    for (bid, cyc), grp in df.groupby(['battery_id', 'cycle']):
        grp = grp.sort_values('timestep')
        v = grp['voltage'].dropna().values
        c = grp['current'].dropna().values
        t = grp['temperature'].dropna().values
        ti = grp['time'].dropna().values
        cap = grp['capacity'].iloc[0]

        if len(v) == 0:
            continue

        mean_v    = np.mean(v)
        term_v    = np.mean(v[-5:]) if len(v) >= 5 else np.mean(v)
        dur       = (ti[-1] - ti[0]) if len(ti) >= 2 else np.nan
        mean_c    = np.mean(np.abs(c)) if len(c) > 0 else np.nan
        temp_rng  = (np.max(t) - np.min(t)) if len(t) > 0 else np.nan

        rows.append({
            'battery_id':        bid,
            'cycle':             cyc,
            'mean_voltage':      round(mean_v, 5),
            'terminal_voltage':  round(term_v, 5),
            'discharge_duration':round(dur, 3) if not np.isnan(dur) else np.nan,
            'mean_current':      round(mean_c, 5),
            'temp_range':        round(temp_rng, 5),
            'capacity':          round(cap, 6),
        })
    return pd.DataFrame(rows)


def main():
    all_path = os.path.join(PROC_DIR, 'all_batteries.csv')
    if not os.path.exists(all_path):
        print('all_batteries.csv not found. Run 01_parse_data.py first.')
        return

    df = pd.read_csv(all_path)
    features = extract_features(df)

    # Drop rows with any NaN feature
    features = features.dropna()

    train = features[features['battery_id'].isin(TRAIN_BATTERIES)]
    test  = features[features['battery_id'].isin(TEST_BATTERIES)]

    train.to_csv(os.path.join(PROC_DIR, 'features_train.csv'), index=False)
    test.to_csv(os.path.join(PROC_DIR,  'features_test.csv'),  index=False)

    print(f'Train set: {len(train)} cycles from {TRAIN_BATTERIES}')
    print(f'Test  set: {len(test)}  cycles from {TEST_BATTERIES}')
    print('Feature extraction complete.')


if __name__ == '__main__':
    main()
