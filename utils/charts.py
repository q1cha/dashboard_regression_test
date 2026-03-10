"""Reusable Plotly chart functions."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def accuracy_bar_chart(acc_df: pd.DataFrame, title: str = "Accuracy by Main Category") -> go.Figure:
    """Horizontal bar chart of accuracy by main_cat."""
    fig = px.bar(
        acc_df.sort_values("accuracy"),
        x="accuracy",
        y="main_cat",
        orientation="h",
        text="accuracy",
        title=title,
        labels={"accuracy": "Accuracy (%)", "main_cat": "Main Category"},
        color="accuracy",
        color_continuous_scale="RdYlGn",
        range_color=[50, 100],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        xaxis_range=[0, 105],
        coloraxis_showscale=False,
        height=max(300, len(acc_df) * 40 + 100),
    )
    return fig


def match_mismatch_stacked_bar(acc_df: pd.DataFrame, title: str = "Match vs Mismatch by Category") -> go.Figure:
    """Stacked bar chart showing match/mismatch counts."""
    df = acc_df.copy()
    df["mismatches"] = df["total"] - df["matches"]
    df = df.sort_values("total", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["main_cat"], x=df["matches"], name="Match",
        orientation="h", marker_color="#2ecc71",
        text=df["matches"].astype(int), textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=df["main_cat"], x=df["mismatches"], name="Mismatch",
        orientation="h", marker_color="#e74c3c",
        text=df["mismatches"].astype(int), textposition="inside",
    ))
    fig.update_layout(
        barmode="stack", title=title,
        xaxis_title="Count", yaxis_title="Main Category",
        height=max(300, len(df) * 40 + 100),
    )
    return fig


def confusion_heatmap(df: pd.DataFrame, true_col: str, pred_col: str, title: str = "Confusion Matrix") -> go.Figure:
    """Generate a confusion matrix heatmap."""
    ct = pd.crosstab(df[true_col], df[pred_col])
    fig = px.imshow(
        ct.values,
        x=ct.columns.tolist(),
        y=ct.index.tolist(),
        text_auto=True,
        title=title,
        labels={"x": "Predicted (Gemini)", "y": "Actual (GPT-4o post)", "color": "Count"},
        color_continuous_scale="Blues",
        aspect="auto",
    )
    fig.update_layout(height=max(400, len(ct) * 30 + 150))
    return fig


def accuracy_trend_chart(trend_data: list[dict], metric_name: str = "Category Accuracy") -> go.Figure:
    """Line chart showing accuracy across multiple runs."""
    df = pd.DataFrame(trend_data)
    fig = px.line(
        df, x="run", y="accuracy",
        title=f"{metric_name} Trend Across Runs",
        labels={"run": "Run", "accuracy": "Accuracy (%)"},
        markers=True,
    )
    fig.update_layout(yaxis_range=[0, 100])
    return fig
