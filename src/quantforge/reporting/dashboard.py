"""Exploratory read-only HTML report, not the promised V4 production dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def write_demo_dashboard(
    forecasts: pd.DataFrame,
    paths: pd.DataFrame,
    out: Path,
    *,
    label: str,
) -> None:
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Portfolio wealth, net of rebalance costs", "One-day predicted loss budget versus realized loss"),
        shared_xaxes=True,
        vertical_spacing=0.11,
    )
    for strategy, frame in paths.groupby("strategy"):
        fig.add_trace(
            go.Scatter(x=frame["date"], y=frame["wealth"], name=strategy, mode="lines"),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=forecasts["date"],
            y=-forecasts["realized_return"],
            name="Realized loss",
            mode="lines",
            line={"width": 1, "color": "#8f8f9c"},
        ),
        row=2,
        col=1,
    )
    for field in ("historical_var", "normal_var", "ewma_normal_var"):
        fig.add_trace(
            go.Scatter(x=forecasts["date"], y=forecasts[field], name=field, mode="lines"),
            row=2,
            col=1,
        )
    fig.update_layout(
        template="plotly_white",
        title=f"QuantForge | {label}",
        height=850,
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.12},
        margin={"l": 65, "r": 30, "t": 85, "b": 70},
    )
    fig.update_yaxes(title_text="Wealth (initial $1)", row=1, col=1)
    fig.update_yaxes(title_text="Daily loss fraction", row=2, col=1)
    fig.add_annotation(
        text="Offline simulation is NOT an empirical historical result" if label.startswith("SIMULATED") else "Research preview; inspect source conventions and biases",
        x=0.5,
        y=1.065,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 11, "color": "#9a2929"},
    )
    fig.write_html(str(out), include_plotlyjs=True, full_html=True)
