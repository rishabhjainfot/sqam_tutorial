"""
Script 01 — Parse NASA PCoE .mat files into clean CSVs.
Each .mat battery file contains charge, discharge, and impedance cycles.
We extract only discharge cycles (where Capacity is recorded).

Run: python src/01_parse_data.py
Output: data/processed/B0005.csv, B0006.csv, B0007.csv, B0018.csv
        data/processed/all_batteries.csv
"""

import scipy.io
import pandas as pd
import numpy as np
import os
from pathlib import Path
import re

RUN_DIR = os.environ.get('SQA_RUN_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
RAW_DIR = os.path.join(RUN_DIR, 'data', 'raw')
OUT_DIR = os.path.join(RUN_DIR, 'data', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)

CANONICAL_COLUMNS = ['battery_id', 'cycle', 'timestep', 'time', 'voltage',
                     'current', 'temperature', 'capacity']


def safe_filename(value):
    """Keep user-supplied CSV battery IDs from becoming filesystem paths."""
    name = re.sub(r'[^A-Za-z0-9_.-]+', '_', str(value)).strip('._')
    return name or 'battery'


def parse_battery(mat_path, battery_id):
    """Parse one .mat file and return a tidy DataFrame of discharge cycles."""
    mat = scipy.io.loadmat(mat_path, simplify_cells=True)

    # The top-level key is the battery name (e.g. 'B0005')
    bkey = [k for k in mat if not k.startswith('_')][0]
    cycles = mat[bkey]['cycle']

    rows = []
    cycle_num = 0

    for cyc in cycles:
        mtype = str(cyc['type']).strip()
        if mtype != 'discharge':
            continue

        cycle_num += 1
        data = cyc['data']

        # Some cycles may be missing Capacity — skip them
        cap = data.get('Capacity', None)
        if cap is None or (hasattr(cap, '__len__') and len(cap) == 0):
            continue
        if isinstance(cap, (list, np.ndarray)):
            cap = float(cap[0]) if len(cap) > 0 else np.nan
        else:
            cap = float(cap)

        voltage_arr     = np.array(data.get('Voltage_measured', []), dtype=float)
        current_arr     = np.array(data.get('Current_measured', []), dtype=float)
        temperature_arr = np.array(data.get('Temperature_measured', []), dtype=float)
        time_arr        = np.array(data.get('Time', []), dtype=float)

        if len(voltage_arr) == 0:
            continue

        # Append one row per timestep inside the discharge cycle
        n = len(voltage_arr)
        for i in range(n):
            rows.append({
                'battery_id':  battery_id,
                'cycle':       cycle_num,
                'timestep':    i,
                'time':        time_arr[i] if i < len(time_arr) else np.nan,
                'voltage':     voltage_arr[i],
                'current':     current_arr[i] if i < len(current_arr) else np.nan,
                'temperature': temperature_arr[i] if i < len(temperature_arr) else np.nan,
                'capacity':    cap,
            })

    df = pd.DataFrame(rows)
    return df


def load_canonical_csv(csv_path):
    """Read long-format CSV data using the project's standard column names."""
    df = pd.read_csv(csv_path)
    required = {'cycle', 'time', 'voltage', 'current', 'temperature', 'capacity'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'{Path(csv_path).name} is missing required columns: {sorted(missing)}')
    if 'battery_id' not in df.columns:
        df['battery_id'] = Path(csv_path).stem
    if 'time' not in df.columns:
        df['time'] = np.nan
    if 'timestep' not in df.columns:
        df['timestep'] = df.groupby(['battery_id', 'cycle']).cumcount()
    df = df[CANONICAL_COLUMNS].copy()
    for col in ['cycle', 'timestep', 'time', 'voltage', 'current', 'temperature', 'capacity']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['battery_id'] = df['battery_id'].astype(str)
    return df.dropna(subset=['cycle', 'voltage', 'capacity'])


def main():
    all_dfs = []
    mat_files = sorted(Path(RAW_DIR).glob('*.mat'))
    csv_files = sorted(Path(RAW_DIR).glob('*.csv'))
    if mat_files and csv_files:
        raise ValueError('Use one input format per run: .mat files or canonical .csv files, not both.')

    if mat_files:
        for mat_path in mat_files:
            bid = mat_path.stem
            print(f'  Parsing {mat_path.name} ...')
            df = parse_battery(str(mat_path), bid)
            out_path = os.path.join(OUT_DIR, f'{safe_filename(bid)}.csv')
            df.to_csv(out_path, index=False)
            print(f'  -> {len(df)} rows, {df["cycle"].nunique()} discharge cycles -> {out_path}')
            all_dfs.append(df)
    elif csv_files:
        for csv_path in csv_files:
            print(f'  Loading {csv_path.name} ...')
            all_dfs.append(load_canonical_csv(csv_path))
        combined_csv = pd.concat(all_dfs, ignore_index=True)
        for bid, df in combined_csv.groupby('battery_id'):
            out_path = os.path.join(OUT_DIR, f'{safe_filename(bid)}.csv')
            df.to_csv(out_path, index=False)
            print(f'  -> {len(df)} rows from {df["cycle"].nunique()} cycles -> {out_path}')
        all_dfs = [combined_csv]

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.to_csv(os.path.join(OUT_DIR, 'all_batteries.csv'), index=False)
        print(f'\nCombined: {len(combined)} rows across {combined["battery_id"].nunique()} batteries')
        print('Parse complete.')
    else:
        raise FileNotFoundError(f'No .mat or .csv dataset files found in {RAW_DIR}')


if __name__ == '__main__':
    main()
