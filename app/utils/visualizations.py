"""
visualizations.py
--------------------
Reusable Plotly chart builders for vitals trend data. Kept separate
from the page files so the same chart logic can be reused across the
Patient dashboard (Phase 5) and Doctor dashboard (Phase 7) without
duplication.

Design decision: these functions take plain lists of VitalsRecord
dataclasses in and return a plotly.graph_objects.Figure out — no
Streamlit dependency, so they're testable and reusable outside a
Streamlit page.
"""

from typing import Optional

import plotly.graph_objects as go

from app.database.models import VitalsRecord


def build_blood_pressure_chart(records: list[VitalsRecord]) -> go.Figure:
    """
    Dual-line chart: systolic + diastolic over time, with shaded bands
    for normal/elevated/high ranges — the kind of clinical context a
    plain line chart can't convey on its own.
    """
    timestamps = [r.recorded_at for r in records]
    systolic = [r.systolic_bp for r in records]
    diastolic = [r.diastolic_bp for r in records]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=systolic, mode="lines+markers",
                              name="Systolic", line=dict(color="#d62728")))
    fig.add_trace(go.Scatter(x=timestamps, y=diastolic, mode="lines+markers",
                              name="Diastolic", line=dict(color="#1f77b4")))

    # Reference lines for standard hypertension thresholds (AHA guidance)
    fig.add_hline(y=120, line_dash="dot", line_color="green",
                  annotation_text="Normal systolic (120)", annotation_position="top left")
    fig.add_hline(y=140, line_dash="dot", line_color="orange",
                  annotation_text="High systolic (140)", annotation_position="top left")

    fig.update_layout(
        title="Blood Pressure Trend",
        xaxis_title="Date/Time",
        yaxis_title="mmHg",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60),
    )
    return fig


def build_single_metric_chart(records: list[VitalsRecord], field: str,
                               title: str, unit: str,
                               normal_range: Optional[tuple[float, float]] = None,
                               color: str = "#2ca02c") -> go.Figure:
    """
    Generic single-line trend chart for any one numeric vitals field
    (heart_rate, glucose_level, weight_kg, temperature_c, oxygen_saturation).
    Skips None values so gaps in a patient's submission history don't
    break the line.
    """
    points = [(r.recorded_at, getattr(r, field)) for r in records if getattr(r, field) is not None]
    timestamps = [p[0] for p in points]
    values = [float(p[1]) for p in points]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=values, mode="lines+markers",
                              name=title, line=dict(color=color)))

    if normal_range is not None:
        fig.add_hrect(y0=normal_range[0], y1=normal_range[1],
                       fillcolor="green", opacity=0.08, line_width=0,
                       annotation_text="Normal range", annotation_position="top left")

    fig.update_layout(
        title=f"{title} Trend",
        xaxis_title="Date/Time",
        yaxis_title=unit,
        margin=dict(t=60),
    )
    return fig
