"""
Streamlit Dashboard — SQA Testing Framework for Battery SOH Prediction
Four tabs: Data Quality Scorecard | Stage-Wise Performance | Sensitivity Testing | Regression Log

Run: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Path helpers ──────────────────────────────────────────────────────────────
BASE = os.environ.get('SQA_RUN_DIR', os.path.join(os.path.dirname(__file__), '..'))
RES  = os.path.join(BASE, 'results')

def res(fname):
    return os.path.join(RES, fname)

def load_csv(fname):
    p = res(fname)
    return pd.read_csv(p) if os.path.exists(p) else None

def load_json(fname):
    p = res(fname)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SQA Dashboard — Battery SOH",
    page_icon="🔋",
    layout="wide",
)

st.title("🔋 SQA Testing Framework — Battery State-of-Health Prediction")
st.caption(
    "An SQA mini-project | SQAM Course | "
    "Dataset: NASA PCoE Li-ion Battery | Model: Random Forest Regressor"
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Data Quality Scorecard",
    "📈 Stage-Wise Performance",
    "🌡️ Sensitivity Testing",
    "🔁 Regression Test Log",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Data Quality Scorecard
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Data Quality Scorecard (Wang & Strong 1996)")
    st.markdown(
        "Each battery's raw discharge data is assessed across four **Intrinsic Data Quality** "
        "dimensions. A dimension score < 90% earns a **FLAG**; a battery fails if any dimension is flagged."
    )

    sc = load_csv('scorecard.csv')
    if sc is None:
        st.warning("scorecard.csv not found. Run `python src/02_data_quality_audit.py` first.")
    else:
        # Add emoji status column
        display_sc = sc.copy()
        display_sc['overall_status'] = display_sc['overall_status'].apply(
            lambda v: '✅ PASS' if v == 'PASS' else '⚠️ FLAG'
        )
        for col in ['completeness', 'consistency', 'accuracy', 'timeliness']:
            display_sc[col] = display_sc[col].apply(lambda v: f"{v:.1f}%")

        st.dataframe(display_sc, use_container_width=True, hide_index=True)

        # Summary bar chart
        dims = ['completeness', 'consistency', 'accuracy', 'timeliness']
        fig, ax = plt.subplots(figsize=(8, 3.5))
        x = np.arange(len(sc))
        w = 0.2
        colors = ['#4c72b0', '#dd8452', '#55a868', '#c44e52']
        for i, dim in enumerate(dims):
            ax.bar(x + i * w, sc[dim], width=w, label=dim.capitalize(),
                   color=colors[i], alpha=0.85)
        ax.axhline(90, color='red', linestyle='--', linewidth=1, label='Pass threshold (90%)')
        ax.set_xticks(x + 1.5 * w)
        ax.set_xticklabels(sc['battery_id'])
        ax.set_ylabel('Score (%)')
        ax.set_ylim(0, 105)
        ax.set_title('Data Quality Scores per Battery')
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig, use_container_width=True)

        st.markdown("**Interpretation:** Scores reflect Wang & Strong (1996) Intrinsic DQ dimensions "
                    "applied to raw NASA PCoE discharge cycle data. Consistency uses physical range checks; "
                    "Accuracy uses Tukey 3×IQR outlier detection; Timeliness checks sampling interval regularity.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Stage-Wise Model Performance
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Stage-Wise Model Performance")
    st.markdown(
        "The test set (Battery B0018) is partitioned into three degradation stages. "
        "A stage **FAILS** if RMSE > 1.5× overall RMSE, or R² < 0.80. "
        "This reveals whether the model hides failure in a specific operating region."
    )

    stage = load_csv('stage_perf.csv')
    base  = load_json('baseline.json')

    if stage is None:
        st.warning("stage_perf.csv not found. Run `python src/05_stage_wise_test.py` first.")
    else:
        # Overall metrics banner
        if base:
            o = base['overall']
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall RMSE (v1)", f"{o['rmse']:.4f} Ah")
            c2.metric("Overall MAE  (v1)", f"{o['mae']:.4f} Ah")
            c3.metric("Overall R²   (v1)", f"{o['r2']:.4f}")

        display_stage = stage.copy()
        display_stage['status'] = display_stage['status'].apply(
            lambda v: '✅ PASS' if v == 'PASS' else '❌ FAIL'
        )
        display_stage['rmse'] = display_stage['rmse'].apply(lambda v: f"{v:.4f}")
        display_stage['mae']  = display_stage['mae'].apply(lambda v: f"{v:.4f}")
        display_stage['r2']   = display_stage['r2'].apply(lambda v: f"{v:.4f}")
        st.dataframe(display_stage, use_container_width=True, hide_index=True)

        # Bar chart: RMSE by stage
        fig, ax = plt.subplots(figsize=(7, 4))
        stage_labels = [s.split('(')[0].strip() for s in stage['stage']]
        bar_colors = ['#55a868' if s == 'PASS' else '#c44e52' for s in stage['status']]
        ax.bar(stage_labels, stage['rmse'], color=bar_colors, width=0.5, alpha=0.85)
        if base:
            ax.axhline(base['overall']['rmse'], color='navy', linestyle='--',
                       linewidth=1.4, label=f"Overall RMSE={base['overall']['rmse']:.4f}")
            ax.axhline(base['overall']['rmse'] * 1.5, color='red', linestyle=':',
                       linewidth=1.2, label='Flag threshold (1.5× overall)')
        ax.set_ylabel('RMSE (Ah)')
        ax.set_title('RMSE by Degradation Stage')
        green_patch = mpatches.Patch(color='#55a868', label='PASS')
        red_patch   = mpatches.Patch(color='#c44e52', label='FAIL')
        ax.legend(handles=[green_patch, red_patch], fontsize=8, loc='upper left')
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig, use_container_width=True)

        st.info(
            "**Why stage-wise testing matters:** An aggregate RMSE can mask catastrophic "
            "failure in the Late Life stage — exactly when reliable SOH prediction is most critical "
            "for battery management system decisions."
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Sensitivity Testing (interactive)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Sensitivity / Robustness Testing")
    st.markdown(
        "Temperature (`temp_range`) is perturbed by a chosen percentage. "
        "The chart shows predicted SOH before and after perturbation across all test cycles. "
        "A large divergence indicates the model is brittle to sensor noise."
    )

    sens = load_csv('sensitivity.csv')
    if sens is None:
        st.warning("sensitivity.csv not found. Run `python src/06_sensitivity_test.py` first.")
    else:
        # Static summary table
        display_sens = sens[['perturbation', 'mean_delta_capacity',
                              'max_delta_capacity', 'status']].copy()
        display_sens.columns = ['Perturbation', 'Mean ΔSOH (Ah)', 'Max ΔSOH (Ah)', 'Status']
        display_sens['Status'] = display_sens['Status'].apply(
            lambda v: '⚠️ SENSITIVE' if v == 'SENSITIVE' else '✅ OK'
        )
        display_sens['Mean ΔSOH (Ah)'] = display_sens['Mean ΔSOH (Ah)'].apply(lambda v: f"{v:.4f}")
        display_sens['Max ΔSOH (Ah)']  = display_sens['Max ΔSOH (Ah)'].apply(lambda v: f"{v:.4f}")

        st.dataframe(display_sens, use_container_width=True, hide_index=True)

        # Interactive: load predictions and re-compute perturbation live
        try:
            import joblib
            test_df = pd.read_csv(os.path.join(BASE, 'data', 'processed', 'features_test.csv'))
            model   = joblib.load(res('rf_model_v1.joblib'))

            FEATURE_COLS = ['mean_voltage', 'terminal_voltage', 'discharge_duration',
                            'mean_current', 'temp_range']
            X_base = test_df[FEATURE_COLS].values
            y_base = model.predict(X_base)

            temp_idx = FEATURE_COLS.index('temp_range')

            st.subheader("Interactive Perturbation Explorer")
            pct = st.slider(
                "Temperature perturbation (%)", min_value=-30, max_value=30, value=0, step=5
            )

            X_pert = X_base.copy()
            X_pert[:, temp_idx] = X_base[:, temp_idx] * (1 + pct / 100)
            y_pert = model.predict(X_pert)

            fig2, ax2 = plt.subplots(figsize=(9, 4))
            cycles = test_df['cycle'].values
            ax2.plot(cycles, test_df['capacity'].values, 'k-', linewidth=1.5,
                     label='Actual Capacity', zorder=3)
            ax2.plot(cycles, y_base,  'b--', linewidth=1.2, alpha=0.8, label='Baseline Prediction (0%)')
            ax2.plot(cycles, y_pert,  'r-',  linewidth=1.2, alpha=0.8,
                     label=f'Perturbed Prediction ({pct:+d}%)')
            ax2.set_xlabel('Discharge Cycle')
            ax2.set_ylabel('Capacity (Ah)')
            ax2.set_title(f'Predicted SOH: Baseline vs Temp Perturbation {pct:+d}%')
            ax2.legend(fontsize=8)
            ax2.grid(alpha=0.3)
            st.pyplot(fig2, use_container_width=True)

            mean_d = np.mean(np.abs(y_pert - y_base))
            max_d  = np.max(np.abs(y_pert - y_base))
            st.metric("Mean |ΔSOH|", f"{mean_d:.4f} Ah")
            st.metric("Max  |ΔSOH|", f"{max_d:.4f} Ah")

        except Exception as e:
            st.info(f"Interactive chart requires the trained model. Run scripts 03–04 first. ({e})")

        st.markdown(
            "**SQA link:** Sensitivity testing is an adaptation of boundary-value and stress testing "
            "for a continuous-output regression model. It evaluates the Fault Tolerance "
            "sub-characteristic of the ISO/IEC 25010 Reliability characteristic."
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Regression Test Log
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Regression Test Log & Defect Summary")
    st.markdown(
        "After training Model v2 (n_estimators=200), the full test suite is re-run. "
        "Any metric that worsens by >5% relative to the v1 baseline is flagged **FAIL**."
    )

    reg  = load_csv('regression_log.csv')
    dlog = load_csv('defect_log.csv')
    dsum = load_json('defect_summary.json')

    if reg is None:
        st.warning("regression_log.csv not found. Run `python src/07_regression_test.py` first.")
    else:
        display_reg = reg.copy()
        display_reg['status'] = display_reg['status'].apply(
            lambda v: '✅ PASS' if v == 'PASS' else '❌ FAIL'
        )
        display_reg['baseline_v1']    = display_reg['baseline_v1'].apply(lambda v: f"{v:.4f}")
        display_reg['post_change_v2'] = display_reg['post_change_v2'].apply(lambda v: f"{v:.4f}")
        display_reg['pct_change']     = display_reg['pct_change'].apply(lambda v: f"{v:+.1f}%")
        st.dataframe(display_reg, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Master Defect Log")

    if dlog is None or len(dlog) == 0:
        st.success("No defects logged across all test stages.")
    else:
        display_dlog = dlog.copy()
        display_dlog['severity'] = display_dlog['severity'].apply(
            lambda v: f"🔴 {v}" if v == 'Critical' else (f"🟡 {v}" if v == 'Major' else f"🟢 {v}")
        )
        st.dataframe(display_dlog, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Aggregate Quality Metrics")

    if dsum:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Defects",      dsum.get('total_defects', '-'))
        c2.metric("Defect Density",     f"{dsum.get('defect_density', '-')}%")
        c3.metric("Severity-Wt. Score", dsum.get('severity_weighted_score', '-'))
        c4.metric("Pass Rate",          f"{dsum.get('pass_rate', '-')}%")

        iso = load_json('iso_summary.json')
        if iso:
            st.subheader("ISO/IEC 25010 Mapping")
            ch = iso.get('characteristics', {})
            for name, detail in ch.items():
                with st.expander(f"**{name}** — {detail.get('sub_characteristic', '')}"):
                    st.write(detail.get('rationale', ''))
                    st.write(f"**Assessment:** {detail.get('assessment', '')}")

    st.info(
        "**Defect density** = total defects / total test cases × 100. "
        "**Severity-weighted score** = 3×Critical + 2×Major + 1×Minor. "
        "These metrics map to ISO/IEC 25010 Reliability characteristic."
    )
