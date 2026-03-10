"""WMS Inference Dashboard — Main entry point."""

import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(
    page_title="WMS Inference Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("WMS Inference Dashboard")
st.markdown(
    """
    Visualize and compare inference validation results from the clothing/accessory
    categorization pipeline.

    **Pages:**
    - **Accuracy Overview** — KPIs, accuracy by category, multi-run trends
    - **Item Comparison** — Filter and inspect individual items
    - **Mismatch Report** — Confusion matrices and top misclassification pairs
    - **Mismatch Gallery** — Browse mismatched items with images
    - **Material OCR** — Material extraction accuracy and known issues
    """
)

# --- File uploader ---
st.divider()
st.subheader("Upload CSV Files")

uploaded_files = st.file_uploader(
    "Upload validation result CSVs",
    type=["csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    for uploaded in uploaded_files:
        dest = DATA_DIR / uploaded.name
        if dest.exists():
            st.info(f"`{uploaded.name}` already exists — skipping.")
        else:
            dest.write_bytes(uploaded.getvalue())
            st.success(f"Saved `{uploaded.name}`")
    st.cache_data.clear()

# Show existing files
existing = sorted(
    [f.name for f in DATA_DIR.iterdir() if f.suffix == ".csv"],
    reverse=True,
)
if existing:
    with st.expander(f"{len(existing)} CSV file(s) loaded"):
        for f in existing:
            st.text(f)
else:
    st.info("No CSV files yet. Upload above or place files in the `data/` folder.")

st.sidebar.success("Select a page above.")
