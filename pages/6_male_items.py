"""Page 6: Male Items — Browse items inferred as male gender."""

import streamlit as st
import pandas as pd

from utils.data_loader import list_result_files, load_csv, detect_model_prefix, parse_timestamp_from_filename

st.set_page_config(page_title="Male Items", page_icon="👔", layout="wide")
st.title("Male Items")

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

gender_col = f"{prefix}gender"
if gender_col not in df.columns:
    st.warning("No gender column found in this run.")
    st.stop()

gemini_cat = f"{prefix}cat"
gemini_cat_en = f"{prefix}cat_en"
cat_match_col = f"{prefix}final_vs_post"

# Filter to male items
male_df = df[df[gender_col] == "male"].reset_index(drop=True)

# --- Sidebar filters ---
st.sidebar.header("Filters")
main_cats = sorted(male_df["main_cat"].dropna().unique())
sel_cats = st.sidebar.multiselect("Main Category", main_cats, default=main_cats)
male_df = male_df[male_df["main_cat"].isin(sel_cats)].reset_index(drop=True)

total = len(male_df)
total_all = len(df)
st.caption(f"{total} male items out of {total_all} total ({total / total_all * 100:.1f}%)")

if total == 0:
    st.info("No male items with current filters.")
    st.stop()

# --- Render as 3-column grid ---
COLS_PER_ROW = 3

for row_start in range(0, total, COLS_PER_ROW):
    cols = st.columns(COLS_PER_ROW)
    for col_idx in range(COLS_PER_ROW):
        idx = row_start + col_idx
        if idx >= total:
            break

        row = male_df.iloc[idx]
        item_id = row.get("item_id", "?")

        with cols[col_idx]:
            # Category match status
            is_cat_miss = row.get(cat_match_col) == False
            status = ":red[Category Mismatch]" if is_cat_miss else ":green[Category Match]"

            st.markdown(f"**{item_id}** — {row.get('main_cat', '')} / {row.get('sub_cat', '')}  {status}")

            # Front + back thumbnails
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

            # Category info
            post = row.get("post_cat", "—")
            gem = row.get(gemini_cat, "—")
            gem_en = row.get(gemini_cat_en, "")
            gem_label = f"{gem} ({gem_en})" if pd.notna(gem_en) and gem_en else str(gem)
            st.caption(f"Old: **{post}** → New: **{gem_label}**")

            st.divider()
