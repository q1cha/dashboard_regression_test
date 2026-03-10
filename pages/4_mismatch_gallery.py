"""Page 4: Mismatch Gallery — Browse all mismatched items with images."""

import streamlit as st
import pandas as pd

from utils.data_loader import list_result_files, load_csv, detect_model_prefix, parse_timestamp_from_filename

st.set_page_config(page_title="Mismatch Gallery", page_icon="🖼", layout="wide")
st.title("Mismatch Gallery")

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

cat_match_col = f"{prefix}final_vs_post"
mat_match_col = f"{prefix}material_vs_existing"
gemini_cat = f"{prefix}cat"
gemini_cat_en = f"{prefix}cat_en"
gemini_mat = f"{prefix}material"
gemini_mat_en = f"{prefix}material_en"
care_raw_col = f"{prefix}care_label_raw"

# --- Sidebar filters ---
st.sidebar.header("Filters")

mismatch_type = st.sidebar.radio(
    "Mismatch type",
    ["Category", "Material OCR", "Both"],
    horizontal=True,
)

main_cats = sorted(df["main_cat"].dropna().unique())
sel_cats = st.sidebar.multiselect("Main Category", main_cats, default=main_cats)

# --- Filter mismatches ---
filtered = df[df["main_cat"].isin(sel_cats)].copy()

if mismatch_type == "Category":
    filtered = filtered[filtered[cat_match_col] == False]
elif mismatch_type == "Material OCR":
    if mat_match_col in filtered.columns:
        filtered = filtered[filtered[mat_match_col] == False]
    else:
        st.warning("No material match column in this run.")
        st.stop()
else:  # Both
    cat_miss = filtered[cat_match_col] == False
    mat_miss = filtered[mat_match_col] == False if mat_match_col in filtered.columns else pd.Series(False, index=filtered.index)
    filtered = filtered[cat_miss | mat_miss]

filtered = filtered.reset_index(drop=True)
total = len(filtered)

st.caption(f"{total} mismatched items")

if total == 0:
    st.success("No mismatches with current filters!")
    st.stop()

# --- Render all items as compact cards ---
# Columns: 3 items per row
COLS_PER_ROW = 3

for row_start in range(0, total, COLS_PER_ROW):
    cols = st.columns(COLS_PER_ROW)
    for col_idx in range(COLS_PER_ROW):
        idx = row_start + col_idx
        if idx >= total:
            break

        row = filtered.iloc[idx]
        item_id = row.get("item_id", "?")
        is_cat_miss = row.get(cat_match_col) == False
        is_mat_miss = row.get(mat_match_col) == False if mat_match_col in row.index else False

        with cols[col_idx]:
            # Header
            badges = []
            if is_cat_miss:
                badges.append(":red[CAT]")
            if is_mat_miss:
                badges.append(":orange[MAT]")

            st.markdown(f"**{item_id}** — {row.get('main_cat', '')} / {row.get('sub_cat', '')}  {' '.join(badges)}")

            # Front + back thumbnails side by side
            img_l, img_r = st.columns(2)
            with img_l:
                if pd.notna(row.get("front_url")):
                    try:
                        st.image(row["front_url"], use_container_width=True)
                    except Exception:
                        st.caption("—")
            with img_r:
                if pd.notna(row.get("back_url")):
                    try:
                        st.image(row["back_url"], use_container_width=True)
                    except Exception:
                        st.caption("—")

            # Care label thumbnails
            care_urls = [row.get(f"care_label_url{i}") for i in range(1, 5) if pd.notna(row.get(f"care_label_url{i}"))]
            if care_urls:
                care_cols = st.columns(len(care_urls))
                for i, url in enumerate(care_urls):
                    with care_cols[i]:
                        try:
                            st.image(url, use_container_width=True)
                        except Exception:
                            st.caption("—")

            # Category mismatch info
            if is_cat_miss:
                post = row.get("post_cat", "—")
                gem = row.get(gemini_cat, "—")
                gem_en = row.get(gemini_cat_en, "")
                gem_label = f"{gem} ({gem_en})" if pd.notna(gem_en) and gem_en else str(gem)
                st.caption(f"Old: **{post}** → New: **{gem_label}**")

            # Material mismatch info
            if is_mat_miss:
                existing = row.get("existing_materials", "—")
                gem_m = row.get(gemini_mat, "—")
                st.caption(f"Existing: **{existing}** → Gemini: **{gem_m}**")

            st.divider()
