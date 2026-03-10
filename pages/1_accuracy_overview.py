"""Page 1: Accuracy Overview — KPIs, accuracy by category, multi-run trends."""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    list_result_files,
    load_csv,
    detect_model_prefix,
    overall_accuracy,
    accuracy_by_main_cat,
    parse_timestamp_from_filename,
    get_model_col,
)
from utils.charts import accuracy_bar_chart, match_mismatch_stacked_bar, accuracy_trend_chart

st.set_page_config(page_title="Accuracy Overview", page_icon="📊", layout="wide")
st.title("Accuracy Overview")

files = list_result_files()
if not files:
    st.warning("No validation result CSVs found in `data/`. Drop files there to get started.")
    st.stop()

# --- Run selector ---
selected_files = st.multiselect(
    "Select run(s)",
    files,
    default=[files[0]],
    format_func=lambda f: f"{parse_timestamp_from_filename(f)}  ({f})",
)

if not selected_files:
    st.info("Select at least one run.")
    st.stop()

# --- Primary run analysis ---
primary_file = selected_files[0]
df = load_csv(primary_file)
prefix = detect_model_prefix(df)

st.subheader(f"Run: {parse_timestamp_from_filename(primary_file)}")
st.caption(f"{len(df)} items — prefix: `{prefix}`")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)

cat_acc = overall_accuracy(df, f"{prefix}final_vs_post")
raw_acc = overall_accuracy(df, f"{prefix}raw_vs_pre")
season_acc = overall_accuracy(df, f"{prefix}vs_pre_season")

material_col = f"{prefix}material_vs_existing"
if material_col in df.columns:
    mat_acc = overall_accuracy(df, material_col)
else:
    mat_acc = None

col1.metric("Category Accuracy (pipeline)", f"{cat_acc}%")
col2.metric("Raw Accuracy", f"{raw_acc}%")
col3.metric("Season Accuracy", f"{season_acc}%")
if mat_acc is not None:
    col4.metric("Material OCR Match", f"{mat_acc}%")
else:
    col4.metric("Material OCR Match", "N/A")

# --- Accuracy by main_cat ---
st.divider()

acc_df = accuracy_by_main_cat(df, f"{prefix}final_vs_post")

left, right = st.columns(2)
with left:
    st.plotly_chart(accuracy_bar_chart(acc_df, "Category Accuracy by Main Category"), use_container_width=True)
with right:
    st.plotly_chart(match_mismatch_stacked_bar(acc_df), use_container_width=True)

# --- Detailed table ---
with st.expander("Accuracy table"):
    st.dataframe(acc_df, use_container_width=True, hide_index=True)

# --- Multi-run trend ---
if len(selected_files) > 1:
    st.divider()
    st.subheader("Multi-Run Comparison")

    trend_data = []
    for f in selected_files:
        run_df = load_csv(f)
        run_prefix = detect_model_prefix(run_df)
        acc = overall_accuracy(run_df, f"{run_prefix}final_vs_post")
        trend_data.append({"run": parse_timestamp_from_filename(f), "accuracy": acc, "items": len(run_df)})

    st.plotly_chart(accuracy_trend_chart(trend_data), use_container_width=True)

    # Per-category comparison
    comparison_rows = []
    for f in selected_files:
        run_df = load_csv(f)
        run_prefix = detect_model_prefix(run_df)
        run_acc = accuracy_by_main_cat(run_df, f"{run_prefix}final_vs_post")
        run_acc["run"] = parse_timestamp_from_filename(f)
        comparison_rows.append(run_acc)

    if comparison_rows:
        comp_df = pd.concat(comparison_rows, ignore_index=True)
        pivot = comp_df.pivot_table(index="main_cat", columns="run", values="accuracy")
        st.dataframe(pivot, use_container_width=True)
