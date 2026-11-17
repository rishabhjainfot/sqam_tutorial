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
import json

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
PROC_DIR = os.path.join(RUN_DIR, 'data', 'processed')


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

    battery_ids = sorted(features['battery_id'].astype(str).unique())
    test_battery = os.environ.get('SQA_TEST_BATTERY', '').strip()
    if not test_battery:
        raise ValueError('Choose a held-out battery by setting SQA_TEST_BATTERY before running this script.')
    if test_battery not in battery_ids:
        raise ValueError(f'Held-out battery {test_battery!r} was not found. Available IDs: {battery_ids}')
    train_batteries = [bid for bid in battery_ids if bid != test_battery]
    if not train_batteries:
        raise ValueError('At least two battery IDs are required: one for training and one held out for testing.')

    train = features[features['battery_id'].astype(str).isin(train_batteries)]
    test  = features[features['battery_id'].astype(str) == test_battery]
    if train.empty or test.empty:
        raise ValueError('The selected split produced an empty train or test set. Check the input cycles.')

    train.to_csv(os.path.join(PROC_DIR, 'features_train.csv'), index=False)
    test.to_csv(os.path.join(PROC_DIR,  'features_test.csv'),  index=False)

    with open(os.path.join(RUN_DIR, 'run_config.json'), 'w', encoding='utf-8') as f:
        json.dump({'train_batteries': train_batteries, 'test_battery': test_battery}, f, indent=2)
    print(f'Train set: {len(train)} cycles from {train_batteries}')
    print(f'Test  set: {len(test)} cycles from {[test_battery]}')
    print('Feature extraction complete.')


if __name__ == '__main__':
    main()
