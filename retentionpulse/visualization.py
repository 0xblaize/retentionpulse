from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .analyzer import AnalysisResult
from .suggestions import format_timestamp


SAFE = "#9BEF9B"
RISK = "#FF7D73"
SURFACE = "#0B1222"
INK = "#EDF4FF"
MUTED = "#8E9BB4"
GRID = "rgba(165,190,255,.12)"


def timeline_figure(result: AnalysisResult) -> go.Figure:
    rows = []
    for sample, score in zip(result.samples, result.motion_scores):
        is_risk = any(segment.start <= sample.timestamp < segment.end for segment in result.static_segments)
        rows.append(
            {
                "timestamp": sample.timestamp,
                "risk": "Static-shot risk" if is_risk else "Normal motion",
                "motion_score": round(score, 4),
            }
        )
    data = pd.DataFrame(rows)
    figure = go.Figure()
    for label, color, symbol in (("Normal motion", SAFE, "square"), ("Static-shot risk", RISK, "diamond")):
        subset = data[data["risk"] == label]
        figure.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=[1] * len(subset),
                mode="markers",
                name=label,
                marker={"color": color, "size": 17, "symbol": symbol, "line": {"color": SURFACE, "width": 2}},
                customdata=subset[["motion_score"]],
                hovertemplate="%{x:.1f}s<br>%{fullData.name}<br>Motion score: %{customdata[0]:.4f}<extra></extra>",
            )
        )
    for segment in result.static_segments:
        figure.add_vrect(
            x0=segment.start,
            x1=segment.end,
            fillcolor=RISK,
            opacity=0.08,
            line={"color": RISK, "width": 1, "dash": "dot"},
            layer="below",
        )
    figure.update_layout(
        title={"text": "Visual retention risk timeline", "font": {"size": 18, "color": INK}},
        height=250,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"color": INK, "family": "Space Grotesk, sans-serif"},
        xaxis={"title": "Video time", "tickformat": "%M:%S", "rangemode": "tozero", "gridcolor": GRID, "zerolinecolor": GRID},
        yaxis={"visible": False, "range": [0.5, 1.5]},
        legend={"orientation": "h", "y": 1.18, "x": 0, "font": {"color": MUTED}},
        margin={"l": 20, "r": 20, "t": 90, "b": 45},
        hovermode="closest",
    )
    return figure


def segment_table(result: AnalysisResult) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Risk": "Static-shot risk",
                "Start": format_timestamp(segment.start),
                "End": format_timestamp(segment.end),
                "Duration": f"{segment.duration:.1f}s",
                "Confidence": f"{segment.confidence:.0%}",
            }
            for segment in result.static_segments
        ]
    )
