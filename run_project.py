"""Choose battery data and run the complete SQA analysis from a small GUI.

Accepted inputs:
  * NASA PCoE-style .mat files, one battery per file; or
  * long-format .csv files with cycle, time, voltage, current, temperature,
    capacity, and optionally battery_id and timestep columns.

Each run is written to its own runs/ folder so previous results and the
project's example data are not overwritten.
"""

import csv
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent
REQUIRED_CSV_COLUMNS = {'cycle', 'time', 'voltage', 'current', 'temperature', 'capacity'}
PIPELINE = [
    ('01_parse_data.py', 'Parse and combine the selected dataset'),
    ('02_data_quality_audit.py', 'Audit the data quality'),
    ('03_feature_extraction.py', 'Build cycle features and split by battery'),
    ('04_train_model.py', 'Train model v1 and save baseline'),
    ('05_stage_wise_test.py', 'Test early, mid, and late battery life'),
    ('06_sensitivity_test.py', 'Run temperature sensitivity checks'),
    ('07_regression_test.py', 'Compare model v2 with the baseline'),
    ('08_defect_log.py', 'Collect defects and calculate quality metrics'),
    ('09_iso25010_summary.py', 'Create the ISO/IEC 25010 summary'),
]


def inspect_input(folder: Path):
    mat_files = sorted(folder.glob('*.mat'))
    csv_files = sorted(folder.glob('*.csv'))
    if mat_files and csv_files:
        raise ValueError('Please put one input type in the selected folder: .mat files or CSV files, not both.')
    if not mat_files and not csv_files:
        raise ValueError('The selected folder has no .mat or .csv files at its top level.')

    if mat_files:
        ids = [p.stem for p in mat_files]
        return 'mat', mat_files, sorted(set(ids))

    ids = set()
    for path in csv_files:
        with path.open('r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_CSV_COLUMNS - columns
            if missing:
                raise ValueError(
                    f'{path.name} is not in the supported long-format CSV layout. '
                    f'Missing columns: {", ".join(sorted(missing))}'
                )
            if 'battery_id' in columns:
                for row in reader:
                    battery_id = (row.get('battery_id') or '').strip()
                    if battery_id:
                        ids.add(battery_id)
            else:
                ids.add(path.stem)
    if len(ids) < 2:
        raise ValueError('At least two battery IDs are needed: one for training and one to hold out for testing.')
    return 'csv', csv_files, sorted(ids)


class ProjectLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title('Battery SQA Project Runner')
        self.root.geometry('780x610')
        self.root.minsize(700, 540)
        self.dataset_folder = None
        self.dataset_files = []
        self.dataset_type = None
        self.run_dir = None

        main = ttk.Frame(root, padding=16)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='Run the Battery SQA Pipeline', font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(
            main,
            text=('1. Choose a folder of compatible battery files.  2. Select one battery to hold out.\n'
                  '3. Click Run. The scripts execute in order and save results in a new run folder.'),
            justify='left', wraplength=730
        ).pack(anchor='w', pady=(5, 12))

        row = ttk.Frame(main)
        row.pack(fill='x')
        self.choose_button = ttk.Button(row, text='Choose dataset folder…', command=self.choose_folder)
        self.choose_button.pack(side='left')
        self.folder_label = ttk.Label(row, text='No dataset selected', wraplength=570)
        self.folder_label.pack(side='left', padx=10)

        split_row = ttk.Frame(main)
        split_row.pack(fill='x', pady=(12, 4))
        ttk.Label(split_row, text='Hold out this battery for testing:').pack(side='left')
        self.battery = tk.StringVar()
        self.battery_box = ttk.Combobox(split_row, textvariable=self.battery, state='disabled', width=22)
        self.battery_box.pack(side='left', padx=10)

        self.input_hint = ttk.Label(
            main,
            text=('Supported input: NASA PCoE-style .mat files, or long-format CSV rows with '
                  'cycle, time in seconds, voltage in V, current in A, temperature in °C and capacity in Ah. '
                  'CSV may also include battery_id and timestep. Other formats or units need a small parser/adapter first.'),
            wraplength=730, justify='left'
        )
        self.input_hint.pack(anchor='w', pady=(4, 10))

        self.run_button = ttk.Button(main, text='Run all analysis scripts', command=self.start_run, state='disabled')
        self.run_button.pack(anchor='w', pady=(0, 10))

        self.log = tk.Text(main, height=18, wrap='word', state='disabled', font=('Consolas', 9))
        self.log.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self.log, orient='vertical', command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        actions = ttk.Frame(main)
        actions.pack(fill='x', pady=(10, 0))
        self.open_button = ttk.Button(actions, text='Open run results folder', command=self.open_results, state='disabled')
        self.open_button.pack(side='left')
        self.dashboard_button = ttk.Button(actions, text='Open dashboard', command=self.open_dashboard, state='disabled')
        self.dashboard_button.pack(side='left', padx=8)

    def append_log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text.rstrip() + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def choose_folder(self):
        selected = filedialog.askdirectory(title='Choose a folder containing the battery dataset files')
        if not selected:
            return
        try:
            kind, files, ids = inspect_input(Path(selected))
        except Exception as exc:
            messagebox.showerror('Dataset not ready', str(exc))
            return
        if len(ids) < 2:
            messagebox.showerror('Need at least two batteries', 'The pipeline needs multiple battery IDs so one can be held out for testing.')
            return
        self.dataset_folder = Path(selected)
        self.dataset_files = files
        self.dataset_type = kind
        self.folder_label.configure(text=f'{self.dataset_folder} ({len(files)} {kind.upper()} file(s), {len(ids)} battery IDs)')
        self.battery_box.configure(values=ids, state='readonly')
        self.battery.set(ids[-1])
        self.run_button.configure(state='normal')
        self.append_log(f'Dataset ready: {len(files)} {kind.upper()} file(s); battery IDs: {", ".join(ids)}')

    def start_run(self):
        if not self.dataset_folder or not self.battery.get():
            messagebox.showwarning('Select a dataset', 'Choose a dataset folder and a held-out battery first.')
            return
        self.run_button.configure(state='disabled')
        self.choose_button.configure(state='disabled')
        self.open_button.configure(state='disabled')
        self.dashboard_button.configure(state='disabled')
        worker = threading.Thread(target=self.run_pipeline, daemon=True)
        worker.start()

    def run_pipeline(self):
        try:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            run_dir = ROOT / 'runs' / f'run_{stamp}'
            raw_dir = run_dir / 'data' / 'raw'
            raw_dir.mkdir(parents=True, exist_ok=False)
            self.run_dir = run_dir
            for source in self.dataset_files:
                shutil.copy2(source, raw_dir / source.name)

            env = os.environ.copy()
            env['SQA_RUN_DIR'] = str(run_dir)
            env['SQA_TEST_BATTERY'] = self.battery.get()
            self.root.after(0, self.append_log, f'\nRun folder: {run_dir}')
            self.root.after(0, self.append_log, f'Held-out test battery: {self.battery.get()}')

            for script, description in PIPELINE:
                self.root.after(0, self.append_log, f'\n{description}…')
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'src' / script)],
                    cwd=ROOT, env=env, capture_output=True, text=True, errors='replace'
                )
                if result.stdout:
                    self.root.after(0, self.append_log, result.stdout)
                if result.stderr:
                    self.root.after(0, self.append_log, result.stderr)
                if result.returncode != 0:
                    raise RuntimeError(f'{script} stopped with exit code {result.returncode}. See the log above.')
            self.root.after(0, self.append_log, '\nAll nine scripts completed successfully.')
            self.root.after(0, self.finish_success)
        except Exception as exc:
            self.root.after(0, self.append_log, f'\nRUN STOPPED: {exc}')
            self.root.after(0, self.finish_failure, str(exc))

    def finish_success(self):
        self.run_button.configure(state='normal')
        self.choose_button.configure(state='normal')
        self.open_button.configure(state='normal')
        self.dashboard_button.configure(state='normal')
        messagebox.showinfo('Analysis complete', f'All analysis scripts finished. Results are in:\n{self.run_dir}')

    def finish_failure(self, error):
        self.run_button.configure(state='normal')
        self.choose_button.configure(state='normal')
        messagebox.showerror('Pipeline stopped', error)

    def open_results(self):
        if self.run_dir:
            open_folder(self.run_dir)

    def open_dashboard(self):
        if not self.run_dir:
            return
        env = os.environ.copy()
        env['SQA_RUN_DIR'] = str(self.run_dir)
        subprocess.Popen(
            [sys.executable, '-m', 'streamlit', 'run', str(ROOT / 'dashboard' / 'app.py')],
            cwd=ROOT, env=env
        )


def open_folder(path: Path):
    if sys.platform.startswith('win'):
        os.startfile(str(path))
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(path)])
    else:
        subprocess.Popen(['xdg-open', str(path)])


if __name__ == '__main__':
    root = tk.Tk()
    ProjectLauncher(root)
    root.mainloop()
