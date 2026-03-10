"""Page 5: Mismatch Gallery — Browse all mismatched items with images."""

import json

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

items_per_page = st.sidebar.slider("Items per page", 1, 20, 5)

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

# --- Pagination ---
total_pages = (total + items_per_page - 1) // items_per_page
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
start = (page - 1) * items_per_page
end = min(start + items_per_page, total)

st.caption(f"Showing items {start + 1}–{end} of {total} (page {page}/{total_pages})")

# --- Render items ---
for idx in range(start, end):
    row = filtered.iloc[idx]
    item_id = row.get("item_id", "?")

    # Determine mismatch badges
    is_cat_miss = row.get(cat_match_col) == False
    is_mat_miss = row.get(mat_match_col) == False if mat_match_col in row.index else False
    badges = []
    if is_cat_miss:
        badges.append("Category")
    if is_mat_miss:
        badges.append("Material")
    badge_str = " | ".join(badges)

    st.divider()
    st.subheader(f"{item_id}  —  {row.get('main_cat', '')} / {row.get('sub_cat', '')}   [{badge_str}]")

    # --- Item images (front/back) ---
    img_cols = st.columns(4)
    with img_cols[0]:
        if pd.notna(row.get("front_url")):
            try:
                st.image(row["front_url"], caption="Front", width=250)
            except Exception:
                st.caption("Front: unavailable")
    with img_cols[1]:
        if pd.notna(row.get("back_url")):
            try:
                st.image(row["back_url"], caption="Back", width=250)
            except Exception:
                st.caption("Back: unavailable")

    # Care label images
    care_urls = [row.get(f"care_label_url{i}") for i in range(1, 5) if pd.notna(row.get(f"care_label_url{i}"))]
    for i, url in enumerate(care_urls):
        with img_cols[2 + i] if (2 + i) < 4 else st.columns(1)[0]:
            try:
                st.image(url, caption=f"Care Label {i+1}", width=200)
            except Exception:
                st.caption(f"Care label {i+1}: unavailable")

    # --- Category comparison ---
    if is_cat_miss:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Old raw:** {row.get('pre_cat', '—')}")
        c2.markdown(f"**Old post-policy:** {row.get('post_cat', '—')}")
        gemini_label = row.get(gemini_cat, '—')
        gemini_en = row.get(gemini_cat_en, '')
        c3.markdown(f"**Gemini:** {gemini_label}" + (f" ({gemini_en})" if pd.notna(gemini_en) and gemini_en else ""))

    # --- Material comparison ---
    if is_mat_miss:
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"**Existing OCR:** {row.get('existing_materials', '—')}")
        gemini_m = row.get(gemini_mat, '—')
        gemini_m_en = row.get(gemini_mat_en, '')
        m2.markdown(f"**Gemini OCR:** {gemini_m}" + (f" ({gemini_m_en})" if pd.notna(gemini_m_en) and gemini_m_en else ""))
        m3.markdown(f"**Care label raw:** {row.get(care_raw_col, '—')}")
