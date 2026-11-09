"""LipidLens Plotly template. Use:
    import lipidlens_plotly            # registers the template
    fig.update_layout(template="lipidlens")
Evidence rule is the same as in lipidlens_viz.py:
  validated = filled marker, solid line; internal = grey square with dark edge;
  predicted = hollow marker ('circle-open'), dashed line ('dash'); illustrative = add_stamp(fig)
"""
import plotly.graph_objects as go
import plotly.io as pio

INK, PAPER, GRID, MUTED = "#1B211E", "#FBFAF6", "#D2D6D1", "#4F5853"
COLORWAY = ["#1F3A2B", "#3B7DA6", "#C99A3A", "#A7BFAE"]
SEQ = [[0, "#F3F5EF"], [0.33, "#B3C6B5"], [0.66, "#4C6D56"], [1, "#1E3B2A"]]
DIV = [[0, "#2F6283"], [0.25, "#9DBBD2"], [0.5, "#F3F5EF"], [0.75, "#E2C27A"], [1, "#A06A12"]]

pio.templates["lipidlens"] = go.layout.Template(layout=dict(
    font=dict(family="Archivo, 'Noto Sans SC', Arial, sans-serif", size=13, color=INK),
    paper_bgcolor=PAPER, plot_bgcolor=PAPER, colorway=COLORWAY,
    title=dict(x=0, xanchor="left", font=dict(size=17)),
    xaxis=dict(showgrid=False, linecolor=MUTED, ticks="outside", tickcolor=MUTED, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=GRID, linecolor=MUTED, ticks="outside", tickcolor=MUTED, zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2),
    colorscale=dict(sequential=SEQ, diverging=DIV),
    margin=dict(l=60, r=24, t=80, b=60)))

def measured(x, y, name="Measured, internal", validated=False):
    return go.Scatter(x=x, y=y, name=name, mode="markers",
                      marker=dict(symbol="circle" if validated else "square", size=9,
                                  color=COLORWAY[0] if validated else "#B4BAB5", line=dict(color=INK, width=1)))

def predicted(x, y, name="Predicted", line=False):
    return go.Scatter(x=x, y=y, name=name, mode="lines" if line else "markers",
                      line=dict(color=COLORWAY[1], dash="dash", width=2),
                      marker=dict(symbol="circle-open", size=10, color=COLORWAY[1], line=dict(width=2)))

def interval(x, lo, hi, name="90% prediction interval"):
    return go.Scatter(x=list(x) + list(x)[::-1], y=list(hi) + list(lo)[::-1], name=name, fill="toself",
                      fillpattern=dict(shape="/", fgcolor=COLORWAY[1], bgcolor="rgba(0,0,0,0)"),
                      line=dict(color=COLORWAY[1], dash="dot", width=1), hoverinfo="skip")

def add_stamp(fig, text="ILLUSTRATIVE DATA, NOT RESULTS"):
    fig.add_annotation(text=f"<b>{text}</b>", xref="paper", yref="paper", x=0, y=1.18, xanchor="left",
                       showarrow=False, font=dict(size=11, color=INK), bgcolor="#F2EFE3", bordercolor=INK, borderwidth=1)
    return fig

if __name__ == "__main__":
    import numpy as np
    x = np.linspace(1, 6, 30); mu = 140 - 12 * x
    fig = go.Figure([interval(x, mu - 6 - x, mu + 6 + x), predicted(x, mu, "Predicted mean", line=True),
                     measured([1.5, 2.5, 3.5], [121, 110, 98])])
    fig.update_layout(template="lipidlens", title="Prediction with uncertainty",
                      xaxis_title="Flow-rate ratio, water : ethanol", yaxis_title="Size (nm)")
    add_stamp(fig).write_html("plotly_example.html", include_plotlyjs="cdn")
    print("wrote plotly_example.html")
