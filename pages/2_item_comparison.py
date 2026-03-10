"""Page 2: Item Comparison — Filter, browse, and inspect individual items."""

import json

import streamlit as st
import pandas as pd

from utils.data_loader import list_result_files, load_csv, detect_model_prefix, parse_timestamp_from_filename, get_model_col

st.set_page_config(page_title="Item Comparison", page_icon="🔍", layout="wide")
st.title("Item Comparison")

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

# --- Filters ---
st.sidebar.header("Filters")

main_cats = sorted(df["main_cat"].dropna().unique())
sel_cats = st.sidebar.multiselect("Main Category", main_cats, default=main_cats)

match_col = f"{prefix}final_vs_post"
match_filter = st.sidebar.radio("Match Status", ["All", "Match", "Mismatch"], horizontal=True)

gender_col = f"{prefix}gender"
if gender_col in df.columns:
    genders = sorted(df[gender_col].dropna().unique())
    sel_genders = st.sidebar.multiselect("Gender", genders, default=genders)
else:
    sel_genders = None

candidate_miss_filter = st.sidebar.checkbox("Candidate miss only")

# Apply filters
filtered = df[df["main_cat"].isin(sel_cats)].copy()
if match_filter == "Match":
    filtered = filtered[filtered[match_col] == True]
elif match_filter == "Mismatch":
    filtered = filtered[filtered[match_col] == False]
if sel_genders is not None and gender_col in df.columns:
    filtered = filtered[filtered[gender_col].isin(sel_genders)]
if candidate_miss_filter and "candidate_miss" in filtered.columns:
    filtered = filtered[filtered["candidate_miss"] == True]

st.caption(f"{len(filtered)} / {len(df)} items shown")

# --- Item table ---
display_cols = ["item_id", "main_cat", "sub_cat"]
if gender_col in df.columns:
    display_cols.append(gender_col)
display_cols += ["pre_cat", "post_cat"]
gemini_cat = f"{prefix}cat"
if gemini_cat in df.columns:
    display_cols.append(gemini_cat)
display_cols.append(match_col)

available_cols = [c for c in display_cols if c in filtered.columns]
table_df = filtered[available_cols].reset_index(drop=True)

st.dataframe(
    table_df,
    use_container_width=True,
    height=400,
    hide_index=True,
)

# --- Item detail view ---
st.divider()
st.subheader("Item Detail")

item_ids = filtered["item_id"].tolist()
if not item_ids:
    st.info("No items match current filters.")
    st.stop()

selected_item = st.selectbox("Select item", item_ids)
row = filtered[filtered["item_id"] == selected_item].iloc[0]

# Images
img_col1, img_col2 = st.columns(2)
with img_col1:
    st.markdown("**Front**")
    if pd.notna(row.get("front_url")):
        try:
            st.image(row["front_url"], width=300)
        except Exception:
            st.caption("Image unavailable")
    else:
        st.caption("No image URL")

with img_col2:
    st.markdown("**Back**")
    if pd.notna(row.get("back_url")):
        try:
            st.image(row["back_url"], width=300)
        except Exception:
            st.caption("Image unavailable")
    else:
        st.caption("No image URL")

# Second piece images (for sets)
if pd.notna(row.get("front_url2")) or pd.notna(row.get("back_url2")):
    st.markdown("**Second Piece**")
    img2_col1, img2_col2 = st.columns(2)
    with img2_col1:
        if pd.notna(row.get("front_url2")):
            try:
                st.image(row["front_url2"], width=300)
            except Exception:
                st.caption("Image unavailable")
    with img2_col2:
        if pd.notna(row.get("back_url2")):
            try:
                st.image(row["back_url2"], width=300)
            except Exception:
                st.caption("Image unavailable")

# Care label images
care_urls = [row.get(f"care_label_url{i}") for i in range(1, 5) if pd.notna(row.get(f"care_label_url{i}"))]
if care_urls:
    st.markdown("**Care Labels**")
    care_cols = st.columns(len(care_urls))
    for i, url in enumerate(care_urls):
        with care_cols[i]:
            try:
                st.image(url, width=250)
            except Exception:
                st.caption("Image unavailable")

# Comparison table
st.markdown("**Category Comparison**")
comp_data = {
    "Field": ["Category", "Category (EN)", "Season", "Color", "Style", "Pattern"],
    "Old (GPT-4o raw)": [
        row.get("pre_cat", ""),
        "",
        row.get("pre_season", ""),
        row.get("pre_color", ""),
        row.get("pre_style", ""),
        row.get("pre_pattern", ""),
    ],
    "Old (post-policy)": [
        row.get("post_cat", ""),
        "",
        row.get("post_season", ""),
        "",
        "",
        "",
    ],
    "New (Gemini)": [
        row.get(f"{prefix}cat", ""),
        row.get(f"{prefix}cat_en", ""),
        row.get(f"{prefix}season", ""),
        row.get(f"{prefix}color", ""),
        row.get(f"{prefix}style", ""),
        row.get(f"{prefix}pattern", ""),
    ],
    "Match": [
        row.get(f"{prefix}final_vs_post", ""),
        "",
        row.get(f"{prefix}vs_pre_season", ""),
        "",
        "",
        "",
    ],
}
st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

# Material
st.markdown("**Material Comparison**")
mat_data = {
    "Source": ["Existing (3-step OCR)", "Gemini OCR", "Gemini (EN)", "Care Label Raw"],
    "Value": [
        row.get("existing_materials", ""),
        row.get(f"{prefix}material", ""),
        row.get(f"{prefix}material_en", ""),
        row.get(f"{prefix}care_label_raw", ""),
    ],
}
st.dataframe(pd.DataFrame(mat_data), use_container_width=True, hide_index=True)

mat_match_col = f"{prefix}material_vs_existing"
if mat_match_col in row.index:
    match_val = row[mat_match_col]
    if match_val is True:
        st.success("Material: Match")
    elif match_val is False:
        st.error("Material: Mismatch")

# Extra info
with st.expander("Additional details"):
    info = {
        "item_id": row.get("item_id"),
        "main_cat": row.get("main_cat"),
        "sub_cat": row.get("sub_cat"),
        "sample_source": row.get("sample_source"),
        "gender": row.get(f"{prefix}gender", ""),
        "category_id": row.get(f"{prefix}category_id", ""),
        "meas_override": row.get(f"{prefix}meas_override", ""),
        "policy_changed_cat": row.get("policy_changed_cat", ""),
        "policy_changed_season": row.get("policy_changed_season", ""),
        "candidate_miss": row.get("candidate_miss", ""),
        "has_care_label": row.get("has_care_label", ""),
    }
    st.json(info)

    # Sizes
    sizes_raw = row.get("sizes", "")
    if pd.notna(sizes_raw) and sizes_raw:
        try:
            sizes = json.loads(sizes_raw)
            st.markdown("**Measurement sizes:**")
            st.json(sizes)
        except (json.JSONDecodeError, TypeError):
            st.text(f"Sizes (raw): {sizes_raw}")
