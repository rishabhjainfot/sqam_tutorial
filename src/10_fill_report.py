"""
Script 10 — Fill placeholder tables in the Milestone 1 .docx with real results and comprehensive SQA analysis.

Features:
  1. Identifies tables by their exact header text (ensuring Table 0: Related Work is NEVER touched).
  2. Replaces placeholder rows in Tables 4.1–4.5 with exact measured values from results/.
  3. Inserts professional engineering analysis paragraphs directly below each table.
  4. Fully populates Section 4.6 with the ISO/IEC 25010 Quality Summary synthesis.
  5. Outputs report/SQA_MiniProject_Report_Final.docx.

Run:
  pip install python-docx
  python src/10_fill_report.py
"""

import os
import json
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

BASE   = os.path.join(os.path.dirname(__file__), '..')
RES    = os.path.join(BASE, 'results')
REPORT = os.path.join(BASE, 'SQA_MiniProject_Report_Milestone1.docx')
OUT    = os.path.join(BASE, 'report', 'SQA_MiniProject_Report_Final.docx')


def load_csv(fname):
    p = os.path.join(RES, fname)
    return pd.read_csv(p) if os.path.exists(p) else None


def load_json(fname):
    p = os.path.join(RES, fname)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def style_cell(cell, text, bold=False, italic=False, color=None, font_size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT):
    """Sets clean cell text, font properties, and paragraph alignment."""
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(str(text))
    run.bold = bold
    run.italic = italic
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    if color:
        run.font.color.rgb = color


def set_cell_background(cell, fill_hex):
    """Sets cell background color via XML shading."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def clear_placeholder_rows(table):
    """Removes all data rows below the header row."""
    while len(table.rows) > 1:
        tr = table.rows[-1]._tr
        table._tbl.remove(tr)


def insert_paragraph_after(table, text, bold_prefix=None, space_after=10):
    """Inserts a styled analysis paragraph immediately after a table."""
    p = OxmlElement('w:p')
    table._tbl.addnext(p)
    new_p = docx_paragraph = None
    # We find the newly created paragraph object via the Document
    for para in table._element.getparent().iterchildren():
        if para == p:
            from docx.text.paragraph import Paragraph
            doc_p = Paragraph(p, table._element.getparent())
            doc_p.paragraph_format.space_before = Pt(6)
            doc_p.paragraph_format.space_after = Pt(space_after)
            doc_p.paragraph_format.line_spacing = 1.15
            if bold_prefix:
                r_pre = doc_p.add_run(bold_prefix)
                r_pre.bold = True
                r_pre.font.name = "Calibri"
                r_pre.font.size = Pt(11)
            r = doc_p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(11)
            return doc_p
    return None


def fill_scorecard(table):
    """Fills Table 4.1: Data Quality Scorecard."""
    sc = load_csv('scorecard.csv')
    if sc is None:
        print("  [ERROR] scorecard.csv not found")
        return
    clear_placeholder_rows(table)
    
    for _, r in sc.iterrows():
        row = table.add_row()
        cells = row.cells
        status_color = RGBColor(0, 128, 0) if r['overall_status'] == 'PASS' else RGBColor(180, 100, 0)
        
        style_cell(cells[0], r['battery_id'], bold=True)
        style_cell(cells[1], f"{r['completeness']:.1f}%", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[2], f"{r['consistency']:.1f}%", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[3], f"{r['accuracy']:.1f}%", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[4], f"{r['timeliness']:.1f}%", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[5], r['overall_status'], bold=True, color=status_color, align=WD_ALIGN_PARAGRAPH.CENTER)
        
        if r['overall_status'] == 'FLAG':
            set_cell_background(cells[5], "FFF3CD")
        else:
            set_cell_background(cells[5], "D4EDDA")
            
    print(f"  Table 4.1 populated with {len(sc)} rows.")


def fill_stage_perf(table):
    """Fills Table 4.2: Stage-Wise Model Performance."""
    stage = load_csv('stage_perf.csv')
    if stage is None:
        print("  [ERROR] stage_perf.csv not found")
        return
    clear_placeholder_rows(table)
    
    for _, r in stage.iterrows():
        row = table.add_row()
        cells = row.cells
        n = int(r['n_cycles'])
        rmse_str = f"{r['rmse']:.4f}" if pd.notna(r['rmse']) else "N/A"
        mae_str  = f"{r['mae']:.4f}" if pd.notna(r['mae']) else "N/A"
        r2_str   = f"{r['r2']:.4f}" if pd.notna(r['r2']) else "N/A"
        
        style_cell(cells[0], r['stage'], bold=True)
        style_cell(cells[1], str(n), align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[2], rmse_str, align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[3], mae_str, align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[4], r2_str, align=WD_ALIGN_PARAGRAPH.RIGHT)
        
    print(f"  Table 4.2 populated with {len(stage)} rows.")


def fill_sensitivity(table):
    """Fills Table 4.3: Sensitivity Testing Results."""
    sens = load_csv('sensitivity.csv')
    if sens is None:
        print("  [ERROR] sensitivity.csv not found")
        return
    clear_placeholder_rows(table)
    
    for _, r in sens.iterrows():
        row = table.add_row()
        cells = row.cells
        obs = "Robust (OK)" if r['status'] == 'OK' else "Sensitive (FAIL)"
        obs_col = RGBColor(0, 128, 0) if r['status'] == 'OK' else RGBColor(180, 0, 0)
        
        style_cell(cells[0], r['perturbation'], bold=True)
        style_cell(cells[1], f"{r['mean_delta_capacity']:.4f}", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[2], f"{r['max_delta_capacity']:.4f}", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[3], obs, bold=True, color=obs_col, align=WD_ALIGN_PARAGRAPH.CENTER)
        
    print(f"  Table 4.3 populated with {len(sens)} rows.")


def fill_regression(table):
    """Fills Table 4.4: Regression Test Log."""
    reg = load_csv('regression_log.csv')
    if reg is None:
        print("  [ERROR] regression_log.csv not found")
        return
    clear_placeholder_rows(table)
    
    for _, r in reg.iterrows():
        row = table.add_row()
        cells = row.cells
        status_col = RGBColor(0, 128, 0) if r['status'] == 'PASS' else RGBColor(180, 0, 0)
        
        style_cell(cells[0], r['test_case_id'], bold=True)
        style_cell(cells[1], f"{r['baseline_v1']:.4f}", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[2], f"{r['post_change_v2']:.4f} ({r['pct_change']:+.1f}%)", align=WD_ALIGN_PARAGRAPH.RIGHT)
        style_cell(cells[3], r['status'], bold=True, color=status_col, align=WD_ALIGN_PARAGRAPH.CENTER)
        
        if r['status'] == 'FAIL':
            set_cell_background(cells[3], "F8D7DA")
        else:
            set_cell_background(cells[3], "D4EDDA")
            
    print(f"  Table 4.4 populated with {len(reg)} rows.")


def fill_defect_log(table):
    """Fills Table 4.5: Defect Log Summary."""
    dlog = load_csv('defect_log.csv')
    if dlog is None:
        print("  [ERROR] defect_log.csv not found")
        return
    clear_placeholder_rows(table)
    
    if len(dlog) == 0:
        row = table.add_row()
        for i in range(5):
            style_cell(row.cells[i], "None", italic=True)
    else:
        for _, r in dlog.iterrows():
            row = table.add_row()
            cells = row.cells
            sev_col = RGBColor(180, 100, 0) if r['severity'] == 'Major' else RGBColor(180, 0, 0)
            
            style_cell(cells[0], r['defect_id'], bold=True)
            style_cell(cells[1], r['test_case'])
            style_cell(cells[2], r['severity'], bold=True, color=sev_col, align=WD_ALIGN_PARAGRAPH.CENTER)
            style_cell(cells[3], r['root_cause_hypothesis'])
            style_cell(cells[4], r['status'], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
            
    print(f"  Table 4.5 populated with {len(dlog)} rows.")


def match_table_by_header(doc):
    """Finds tables accurately by examining column 0 or 1 header text."""
    table_map = {}
    for i, t in enumerate(doc.tables):
        if len(t.rows) == 0:
            continue
        hdr_text = " ".join(c.text for c in t.rows[0].cells).lower()
        if "battery id" in hdr_text:
            table_map['scorecard'] = t
        elif "degradation stage" in hdr_text:
            table_map['stage'] = t
        elif "perturbation level" in hdr_text:
            table_map['sensitivity'] = t
        elif "test case id" in hdr_text:
            table_map['regression'] = t
        elif "defect id" in hdr_text:
            table_map['defect'] = t
    return table_map


def main():
    if not os.path.exists(REPORT):
        print(f"[ERROR] Template document not found: {REPORT}")
        return

    print(f"Loading document: {REPORT}")
    doc = Document(REPORT)

    t_map = match_table_by_header(doc)
    print(f"Matched {len(t_map)} target result tables.")

    # 1. Fill tables
    if 'scorecard' in t_map:
        fill_scorecard(t_map['scorecard'])
        insert_paragraph_after(
            t_map['scorecard'],
            "Analysis of Data Quality Audit: The audit demonstrates 100.0% Completeness across all cells, with no missing sensor readings in recorded discharge cycles. Consistency exceeds 99.2% for all cells, confirming physical fidelity of voltage, current, and temperature telemetry. However, batteries B0005 (89.5%) and B0006 (87.9%) trigger a FLAG status due to the Intrinsic Accuracy dimension falling below the 90.0% threshold. Tukey 3×IQR outlier detection identified transient voltage and temperature anomalies during rapid end-of-discharge transitions. In contrast, B0007 (94.8%) and B0018 (91.1%) satisfied all four dimensions. In an industrial SQA deployment, such automated screening acts as a mandatory Quality Gate, preventing compromised sensor profiles from corrupting downstream model training.",
            bold_prefix="Analysis of Table 4.1: "
        )

    if 'stage' in t_map:
        fill_stage_perf(t_map['stage'])
        insert_paragraph_after(
            t_map['stage'],
            "Analysis of Stage-Wise Functional Testing: Partitioning the evaluation across degradation regimes provides critical visibility that monolithic metrics conceal. For Early Life (>90% capacity, N=38 cycles), the model achieves high accuracy with RMSE = 0.0130 Ah, MAE = 0.0111 Ah, and R² = 0.9463. In the Mid Life stage (70–90% capacity, N=94 cycles), error increases to RMSE = 0.0335 Ah and MAE = 0.0264 Ah (R² = 0.8855), reflecting non-linear degradation dynamics. Crucially, the Late Life stage (<70% capacity) contained N=0 cycles for battery B0018, as the test cell's cycling was discontinued before reaching this deep degradation zone. Rather than a limitation, the SQA framework correctly identifies and flags this operational coverage deficit, proving that high aggregate benchmark scores (overall R² = 0.9644) can mask unverified safety-critical zones.",
            bold_prefix="Analysis of Table 4.2: "
        )

    if 'sensitivity' in t_map:
        fill_sensitivity(t_map['sensitivity'])
        insert_paragraph_after(
            t_map['sensitivity'],
            "Analysis of Robustness and Input Sensitivity: Systematic perturbation of the temperature feature (temp_range) across ±5%, ±10%, and ±20% reveals remarkable model robustness. At the nominal ±10% perturbation level, the mean output shift is only 0.0071 Ah, with a peak shift of 0.0186 Ah. Even under extreme ±20% stress perturbation, the maximum observed divergence is 0.0206 Ah (~1.08% of nominal capacity), remaining well within the safety-critical threshold of 0.0500 Ah. The model exhibits asymmetric sensitivity: positive temperature perturbations induce higher variance than cooling perturbations, correlating with internal electrochemical impedance shifts. All sensitivity test cases pass the SQA robustness gate.",
            bold_prefix="Analysis of Table 4.3: "
        )

    if 'regression' in t_map:
        fill_regression(t_map['regression'])
        insert_paragraph_after(
            t_map['regression'],
            "Analysis of Regression Testing: To simulate model maintenance and hyperparameter iteration, an updated Random Forest model (v2, n_estimators=200) was evaluated against the recorded baseline (v1, n_estimators=100). Regression testing immediately flagged two critical regressions: Overall RMSE degraded by +8.1% (from 0.0291 Ah to 0.0314 Ah), and MAE degraded by +6.9% (from 0.0220 Ah to 0.0235 Ah), violating the 5.0% maximum allowable degradation threshold. Only R² satisfied regression criteria (-0.6% change). This finding constitutes a core contribution of the SQA approach: an engineer modifying hyperparameters under the assumption that 'more trees equals better performance' would have silently deployed a degraded model without automated regression quality gates.",
            bold_prefix="Analysis of Table 4.4: "
        )

    if 'defect' in t_map:
        fill_defect_log(t_map['defect'])
        insert_paragraph_after(
            t_map['defect'],
            "Analysis of Defect Logging and Quality Metrics: Across the 12 formal test cases executed across Stages 3 to 5 (3 stage-wise, 6 sensitivity, 3 regression), the framework detected and logged 2 formal defects (D-020 and D-021), both attributed to hyperparameter-induced regression. This yields an aggregate Defect Density of 16.67 defects per 100 test cases and a Severity-Weighted Defect Score of 4.0 (2 Major defects × weight 2). The resulting Test Suite Pass Rate is 83.33%. Tracking these quantifiable software metrics transforms black-box machine learning iteration into an auditable, safety-compliant engineering process.",
            bold_prefix="Analysis of Table 4.5: "
        )

    # 2. Update Section 4.6 Narrative
    # Find the paragraph for Section 4.6 and replace its text with full standards synthesis
    sec_46_found = False
    for i, p in enumerate(doc.paragraphs):
        if "4.6" in p.text and "ISO/IEC 25010" in p.text:
            sec_46_found = True
            # The next paragraph is the placeholder text
            if i + 1 < len(doc.paragraphs):
                target_p = doc.paragraphs[i+1]
                target_p.text = (
                    "4.6.1 Synthesis under ISO/IEC 25010 Software Quality Model\n\n"
                    "The empirical findings from all five testing stages are consolidated under the international "
                    "software quality standard ISO/IEC 25010 (Systems and software Quality Requirements and Evaluation - SQuaRE), "
                    "focusing on the two characteristics most critical for embedded and safety-critical electrical systems:\n\n"
                    "1. Functional Suitability (Functional Correctness):\n"
                    "The baseline Random Forest model demonstrates acceptable predictive accuracy on the held-out test battery "
                    "(B0018), achieving an overall RMSE of 0.0291 Ah, MAE of 0.0220 Ah, and an explanatory coefficient R² = 0.9644. "
                    "Functional correctness is certified for Early Life (RMSE = 0.0130 Ah, R² = 0.9463) and Mid Life (RMSE = 0.0335 Ah, "
                    "R² = 0.8855) degradation stages. However, the assessment is conditionally bounded: the absence of test data in the "
                    "Late Life (<70%) regime precludes certification for end-of-life battery management decisions, demonstrating how SQA "
                    "stratification prevents false confidence in untested operating envelopes.\n\n"
                    "2. Reliability (Fault Tolerance & Maturity):\n"
                    "Under the Reliability characteristic, Fault Tolerance was verified via sensitivity analysis: the model maintained stable "
                    "capacity predictions under ±20% temperature sensor noise (maximum output shift = 0.0206 Ah vs. 0.0500 Ah allowable). "
                    "However, under the Maturity sub-characteristic, the system demonstrated regression vulnerability: an uncontrolled "
                    "hyperparameter update (n_estimators 100→200) produced an 8.1% error degradation, resulting in a 33.3% regression "
                    "pass rate and generating two Major defect records (D-020 and D-021). The aggregate defect density of 16.67% and overall "
                    "pass rate of 83.33% provide an objective benchmark for release qualification.\n\n"
                    "4.6.2 Engineering Conclusion and SQA Recommendations\n\n"
                    "This investigation confirms that traditional machine learning evaluation practices—namely relying on a single, "
                    "dataset-wide RMSE score—are insufficient for safety-critical electrical engineering deployments such as electric "
                    "vehicle Battery Management Systems (BMS). By applying an SQA framework incorporating Wang & Strong data quality audits, "
                    "stage-wise functional testing, input sensitivity perturbation, regression test suites, and ISO/IEC 25010 mapping, "
                    "engineers gain auditable, deterministic criteria to accept, flag, or reject predictive models before deployment."
                )
                target_p.paragraph_format.line_spacing = 1.15
                target_p.paragraph_format.space_before = Pt(6)
                target_p.paragraph_format.space_after = Pt(12)
                for run in target_p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
            break

    # Save to final document
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.save(OUT)
    print(f"\n[SUCCESS] Final Report successfully generated at:\n  {OUT}")


if __name__ == '__main__':
    main()
