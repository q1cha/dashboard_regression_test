"""CSV loading, parsing, and caching utilities."""

import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"


def list_result_files() -> list[str]:
    """Return validation result CSV filenames sorted newest-first."""
    files = []
    for f in DATA_DIR.iterdir():
        if f.name.startswith("validation_results_") and f.suffix == ".csv" and "_errors" not in f.name:
            files.append(f.name)
    return sorted(files, reverse=True)


def parse_timestamp_from_filename(filename: str) -> str:
    """Extract a human-readable timestamp from filename."""
    m = re.search(r"(\d{8})_(\d{6})", filename)
    if m:
        d, t = m.group(1), m.group(2)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]} {t[:2]}:{t[2:4]}:{t[4:6]}"
    return filename


def detect_model_prefix(df: pd.DataFrame) -> str:
    """Auto-detect model column prefix by finding columns ending in _final_vs_post."""
    for col in df.columns:
        if col.endswith("_final_vs_post"):
            return col.replace("_final_vs_post", "_")
    return ""


def _parse_booleans(df: pd.DataFrame) -> pd.DataFrame:
    """Convert string True/False columns to proper booleans."""
    for col in df.columns:
        if df[col].dtype == object:
            unique = set(df[col].dropna().unique())
            if unique <= {"True", "False", ""}:
                df[col] = df[col].replace({"True": True, "False": False, "": None})
    return df


@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    """Load and parse a validation result CSV."""
    path = DATA_DIR / filename
    df = pd.read_csv(path)
    df = _parse_booleans(df)
    return df


def get_model_col(df: pd.DataFrame, suffix: str) -> str:
    """Get the full column name for a model-prefixed column."""
    prefix = detect_model_prefix(df)
    return f"{prefix}{suffix}"


def accuracy_by_main_cat(df: pd.DataFrame, bool_col: str) -> pd.DataFrame:
    """Compute accuracy (match rate) grouped by main_cat."""
    col = bool_col if bool_col in df.columns else get_model_col(df, bool_col)
    subset = df.dropna(subset=[col]).copy()
    subset[col] = subset[col].astype(bool).astype(int)
    grouped = subset.groupby("main_cat")[col].agg(["sum", "count"]).reset_index()
    grouped.columns = ["main_cat", "matches", "total"]
    grouped = grouped[grouped["total"] > 0]
    grouped["accuracy"] = (grouped["matches"] / grouped["total"] * 100).round(1)
    return grouped.sort_values("accuracy", ascending=False)


def overall_accuracy(df: pd.DataFrame, bool_col: str) -> float:
    """Compute overall accuracy for a boolean match column."""
    col = bool_col if bool_col in df.columns else get_model_col(df, bool_col)
    series = df[col].dropna().astype(bool).astype(int)
    if len(series) == 0:
        return 0.0
    return round(series.sum() / len(series) * 100, 1)
