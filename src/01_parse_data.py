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

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)

BATTERIES = ['B0005', 'B0006', 'B0007', 'B0018']


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


def main():
    all_dfs = []
    for bid in BATTERIES:
        mat_path = os.path.join(RAW_DIR, f'{bid}.mat')
        if not os.path.exists(mat_path):
            print(f'  [SKIP] {bid}.mat not found in {RAW_DIR}')
            continue

        print(f'  Parsing {bid}.mat ...')
        df = parse_battery(mat_path, bid)
        out_path = os.path.join(OUT_DIR, f'{bid}.csv')
        df.to_csv(out_path, index=False)
        print(f'  -> {len(df)} rows, {df["cycle"].nunique()} discharge cycles -> {out_path}')
        all_dfs.append(df)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.to_csv(os.path.join(OUT_DIR, 'all_batteries.csv'), index=False)
        print(f'\nCombined: {len(combined)} rows across {combined["battery_id"].nunique()} batteries')
        print('Parse complete.')
    else:
        print('\nNo .mat files found. Download B0005.mat–B0018.mat into data/raw/ first.')


if __name__ == '__main__':
    main()
