"""Page 3: Mismatch Report — Confusion matrices, top confusion pairs, overrides."""

import streamlit as st
import pandas as pd

from utils.data_loader import list_result_files, load_csv, detect_model_prefix, parse_timestamp_from_filename
from utils.charts import confusion_heatmap

st.set_page_config(page_title="Mismatch Report", page_icon="📋", layout="wide")
st.title("Mismatch Report")

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

# --- Filter by main_cat ---
main_cats = sorted(df["main_cat"].dropna().unique())
sel_cat = st.selectbox("Filter by main category", ["All"] + main_cats)

if sel_cat != "All":
    filtered = df[df["main_cat"] == sel_cat].copy()
else:
    filtered = df.copy()

match_col = f"{prefix}final_vs_post"
gemini_cat = f"{prefix}cat"

st.caption(f"{len(filtered)} items | {(filtered[match_col] == False).sum()} mismatches")

# --- Confusion matrix ---
st.subheader("Confusion Matrix")
if "post_cat" in filtered.columns and gemini_cat in filtered.columns:
    # Only show items that have both values
    cm_df = filtered.dropna(subset=["post_cat", gemini_cat])
    if len(cm_df) > 0:
        fig = confusion_heatmap(cm_df, "post_cat", gemini_cat, f"post_cat vs Gemini cat ({sel_cat})")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for confusion matrix.")
else:
    st.info("Required columns not found.")

# --- Top confusion pairs ---
st.subheader("Top Confusion Pairs")
if "post_cat" in filtered.columns and gemini_cat in filtered.columns:
    mismatches = filtered[filtered[match_col] == False].dropna(subset=["post_cat", gemini_cat])
    if len(mismatches) > 0:
        pairs = (
            mismatches.groupby(["post_cat", gemini_cat])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(20)
        )
        pairs.columns = ["Old (post_cat)", "New (Gemini)", "Count"]
        st.dataframe(pairs, use_container_width=True, hide_index=True)
    else:
        st.success("No mismatches!")
else:
    st.info("Required columns not found.")

# --- Measurement override impact ---
st.divider()
st.subheader("Measurement Override Impact")

override_col = f"{prefix}meas_override"
if override_col in df.columns:
    overridden = df[df[override_col] == True]
    st.metric("Items with measurement override", len(overridden))
    if len(overridden) > 0:
        override_acc = (overridden[match_col] == True).sum() / len(overridden) * 100
        st.metric("Accuracy of overridden items", f"{override_acc:.1f}%")

        with st.expander("Override details"):
            cols = ["item_id", "main_cat", "pre_cat", "post_cat", gemini_cat, match_col]
            available = [c for c in cols if c in overridden.columns]
            st.dataframe(overridden[available].reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.info("No measurement override column found.")

# --- Candidate miss items ---
st.divider()
st.subheader("Candidate Miss Items")

if "candidate_miss" in df.columns:
    candidates = df[df["candidate_miss"] == True]
    st.metric("Candidate miss items", len(candidates))
    if len(candidates) > 0:
        st.caption("These items had their main_cat changed after inference. `raw_vs_pre` is unreliable for them.")
        cols = ["item_id", "main_cat", "sub_cat", "pre_cat", "post_cat", gemini_cat, match_col]
        available = [c for c in cols if c in candidates.columns]
        st.dataframe(candidates[available].reset_index(drop=True), use_container_width=True, hide_index=True, height=300)
else:
    st.info("No `candidate_miss` column found.")
