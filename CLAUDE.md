# WMS Inference Dashboard — Regression Test Viewer

## Background

This is a Streamlit dashboard for visualizing and comparing AI inference validation results from a clothing + accessory categorization pipeline.

The WMS (Warehouse Management System) backend uses an AI pipeline to classify clothing items into categories. We recently rewrote the inference Lambda to be stateless and switched from GPT-4o to Gemini 3 Flash, achieving ~87% category accuracy (up from ~60%).

A Python validation script (`validate_prompt.py` in the main WMS backend repo) runs batches of items through both the old and new models, producing CSV result files. This dashboard makes those CSVs easy to explore and compare.

---

## Data Format

### CSV Schema

Each row = one item. Columns:

**Item metadata:**
- `item_id` — unique item ID
- `main_cat` — main category: `outer`, `top`, `bottom`, `onepiece`, `set`, `bag`, `wallet`, `muffler`, `hat`
- `sub_cat` — sub category (e.g. `jacket`, `coat`, `pants`)
- `sample_source` — how the item was sampled

**Stage 1 — Pre-engineered (raw GPT-4o, before Go composite policy):**
- `pre_cat`, `pre_season`, `pre_color`, `pre_style`, `pre_pattern`

**Stage 2 — Post-engineered (after Go composite policy applies measurement rules etc.):**
- `post_cat`, `post_season`

**Policy impact:**
- `policy_changed_cat` (bool), `policy_changed_season` (bool)
- `sizes` — JSON string, e.g. `{"top": 57.8, "outer": 0.0, "bottom": 103.2, "onepiece": 0.0}`

**Stage 3 — New model results (column prefix: `gemini3flashpreview_`):**
- `*_raw_cat` (Korean), `*_raw_cat_en` (English) — raw model prediction before post-processing
- `*_cat` (Korean), `*_cat_en` (English) — after measurement rules
- `*_gender` — predicted gender (male/female)
- `*_category_id` — predicted leaf category ID (integer)
- `*_meas_override` — whether measurement rules overrode the model prediction
- `*_season`, `*_color`, `*_style`, `*_pattern`
- `*_raw_vs_pre` (bool) — raw Gemini vs raw GPT-4o match
- `*_final_vs_post` (bool) — **KEY metric**: full pipeline vs full pipeline match
- `*_vs_pre_season` (bool) — season match
- `*_material`, `*_material_en` — Gemini OCR material extraction
- `*_care_label_raw` — raw OCR text from care label
- `*_material_vs_existing` (bool) — material match vs existing 3-step OCR pipeline

**Ground truth / images:**
- `existing_materials` — materials from existing OCR pipeline (Korean, comma-separated)
- `has_care_label` (bool) — whether item has care label images
- `front_url`, `back_url` — item images (.webp, hosted on studio.charan.kr CDN)
- `front_url2`, `back_url2` — second piece images (for set items only)
- `candidate_miss` (bool) — main_cat changed after inference; raw_vs_pre unreliable for these

### Boolean columns
In the CSV, Python bools are written as string `True`/`False`. Parse on load:
```python
bool_cols = [col for col in df.columns if df[col].dtype == object and df[col].isin(['True', 'False', '']).all()]
df[bool_cols] = df[bool_cols].replace({'True': True, 'False': False, '': None})
```

### Column prefix detection
The model slug prefix (e.g. `gemini3flashpreview_`) may vary across runs. Auto-detect by finding columns ending in `_final_vs_post`.

### File naming convention
- `validation_results_YYYYMMDD_HHMMSS[_thinking_minimal].csv` — main results
- `*_errors.csv` — API call errors (columns: item_id, model, error)
- `*_report.md` — auto-generated markdown report

### Sample sizes
- Small runs: ~50-150 items (early prompt iterations)
- Large runs: ~2200 items (full validation including accessories)

---

## Key Metrics

1. **Category accuracy (pipeline vs pipeline)** = `*_final_vs_post` — the most important metric. Compares new Gemini pipeline output vs what the old GPT-4o pipeline stored.
2. **Raw accuracy** = `*_raw_vs_pre` — raw model output comparison (no post-processing). Lower because accessories have no old raw predictions.
3. **Material OCR** = `*_material_vs_existing` — Gemini single-call OCR vs old 3-step GPT pipeline.
4. **Season accuracy** = `*_vs_pre_season` — typically low (~33%) because Gemini is more conservative.

---

## Category Details

- **Clothing**: outer, top, bottom, onepiece, set (9 main categories with ~100+ leaf categories total)
- **Accessories**: bag, wallet, muffler, hat (new, added to inference pipeline)
- Category names are **Korean** (e.g. 라이더재킷, 싱글재킷). English labels in `*_cat_en` columns.
- `outer` is the hardest category (~79% accuracy) — many similar jacket/coat subtypes
- `onepiece` and `set` are easiest (~99-100%) — distinctive silhouettes
- Accessories: bag ~84%, hat ~96%, muffler 100%, wallet ~83%

---

## Known Issues in Data

- **`모→모헤어`/`모→모달` bug**: old 3-step OCR pipeline incorrectly mapped `모` (generic wool) to Mohair or Modal. Gemini gets this right. Some "mismatches" are actually Gemini being correct.
- **Candidate miss items** (`candidate_miss=True`): items where `main_cat` was changed after inference. `raw_vs_pre` is unreliable for these, but `final_vs_post` is still valid.
- **Accuracy varies ~1-2%** between runs due to LLM non-determinism (temperature=1.0).

---

## Tech Stack

- **Streamlit** for the dashboard
- **Pandas** for data processing
- **Plotly** for interactive charts
- Deploy via **Streamlit Community Cloud** (connect GitHub repo)

---

## Image URLs

Item images are hosted at `https://studio.charan.kr/charan-studio/release/daily/.../*.webp`. These may require VPN or internal network access. Use `st.image(url)` with a try/except fallback.
