"""Page 4: Material OCR — Match rates, mismatches, known issues."""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    list_result_files,
    load_csv,
    detect_model_prefix,
    parse_timestamp_from_filename,
    accuracy_by_main_cat,
    overall_accuracy,
)
from utils.charts import accuracy_bar_chart

st.set_page_config(page_title="Material OCR", page_icon="🧵", layout="wide")
st.title("Material OCR Analysis")

files = list_result_files()
if not files:
    st.warning("No validation result CSVs found in `data/`.")
    st.stop()

selected_file = st.selectbox(
    "Select run",
    files,
    format_func=lambda f: f"{parse_timestamp_from_filename(f)}  ({f})",
)

df = load_csv(selected_file)
prefix = detect_model_prefix(df)
mat_col = f"{prefix}material_vs_existing"

if mat_col not in df.columns:
    st.warning(f"Material match column `{mat_col}` not found in this run.")
    st.stop()

# --- KPIs ---
col1, col2, col3 = st.columns(3)

mat_acc = overall_accuracy(df, mat_col)
col1.metric("Overall Material Match", f"{mat_acc}%")

care_col = "has_care_label"
if care_col in df.columns:
    care_pct = df[care_col].sum() / len(df) * 100
    col2.metric("Care Label Coverage", f"{care_pct:.1f}%")
else:
    col2.metric("Care Label Coverage", "N/A")

mismatch_count = (df[mat_col] == False).sum()
col3.metric("Total Mismatches", mismatch_count)

# --- Accuracy by main_cat ---
st.divider()
st.subheader("Material Match Rate by Category")

acc_df = accuracy_by_main_cat(df, mat_col)
st.plotly_chart(accuracy_bar_chart(acc_df, "Material Match Rate by Main Category"), use_container_width=True)

with st.expander("Accuracy table"):
    st.dataframe(acc_df, use_container_width=True, hide_index=True)

# --- Mismatch table ---
st.divider()
st.subheader("Material Mismatches")

mismatches = df[df[mat_col] == False].copy()

if len(mismatches) == 0:
    st.success("No material mismatches!")
else:
    # Filter by main_cat
    main_cats = sorted(mismatches["main_cat"].dropna().unique())
    sel_cat = st.selectbox("Filter mismatches by category", ["All"] + main_cats)
    if sel_cat != "All":
        mismatches = mismatches[mismatches["main_cat"] == sel_cat]

    gemini_mat = f"{prefix}material"
    gemini_mat_en = f"{prefix}material_en"
    care_raw = f"{prefix}care_label_raw"

    display_cols = ["item_id", "main_cat", "existing_materials"]
    for c in [gemini_mat, gemini_mat_en, care_raw]:
        if c in mismatches.columns:
            display_cols.append(c)

    available = [c for c in display_cols if c in mismatches.columns]
    st.dataframe(
        mismatches[available].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

# --- Known issues ---
st.divider()
st.subheader("Known Issues")

st.markdown(
    """
    **`모→모헤어` / `모→모달` bug**: The old 3-step OCR pipeline incorrectly mapped
    generic `모` (wool) to 모헤어 (Mohair) or 모달 (Modal). Gemini correctly identifies
    the material. Some apparent "mismatches" are actually Gemini being correct.
    """
)

# Detect potential instances of the known bug
gemini_mat_col = f"{prefix}material"
if gemini_mat_col in df.columns and "existing_materials" in df.columns:
    wool_bug = df[
        (df[mat_col] == False)
        & (df["existing_materials"].str.contains("모헤어|모달", na=False))
    ]
    if len(wool_bug) > 0:
        st.warning(f"Found {len(wool_bug)} potential `모→모헤어/모달` bug instances in this run.")
        with st.expander("View these items"):
            cols = ["item_id", "main_cat", "existing_materials", gemini_mat_col]
            if care_raw in df.columns:
                cols.append(care_raw)
            available = [c for c in cols if c in wool_bug.columns]
            st.dataframe(wool_bug[available].reset_index(drop=True), use_container_width=True, hide_index=True)
    else:
        st.info("No `모→모헤어/모달` bug instances detected.")
