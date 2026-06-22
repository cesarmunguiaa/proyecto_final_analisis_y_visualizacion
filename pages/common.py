from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "ifood_dashboard.csv"

COLORS = {
    "primary": "#7A243A",
    "secondary": "#176B87",
    "accent": "#D18B47",
    "positive": "#287D5A",
    "negative": "#B23A48",
    "muted": "#708090",
    "light": "#EEF2F5",
}

PRODUCT_COLUMNS = OrderedDict(
    [
        ("MntWines", "Vinos"),
        ("MntMeatProducts", "Carnes"),
        ("MntFruits", "Frutas"),
        ("MntFishProducts", "Pescado"),
        ("MntSweetProducts", "Dulces"),
        ("MntGoldProds", "Gold"),
    ]
)

CHANNEL_COLUMNS = OrderedDict(
    [
        ("NumWebPurchases", "Web"),
        ("NumCatalogPurchases", "Catálogo"),
        ("NumStorePurchases", "Tienda"),
    ]
)

CAMPAIGN_COLUMNS = OrderedDict(
    [
        ("AcceptedCmp1", "Campaña 1"),
        ("AcceptedCmp2", "Campaña 2"),
        ("AcceptedCmp3", "Campaña 3"),
        ("AcceptedCmp4", "Campaña 4"),
        ("AcceptedCmp5", "Campaña 5"),
        ("Response", "Última campaña"),
    ]
)

STRATEGIC_FLAGS = OrderedDict(
    [
        ("Nuevo de alto valor", "Is_Early_High_Value"),
        ("Premium", "Is_Premium"),
        ("Alto ingreso, bajo gasto", "Is_High_Income_Low_Spending"),
        ("Web curioso", "Is_Web_Curious"),
        ("Inactivo o frío", "Is_Cold"),
        ("Leal", "Is_Loyal"),
        ("Sensible a descuentos", "Is_Discount_Sensitive"),
        ("Multicanal", "Is_Multichannel"),
    ]
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "No existe data/ifood_dashboard.csv. Ejecuta primero notebooks/Analitica.ipynb."
        )
    data = pd.read_csv(DATA_PATH, parse_dates=["Dt_Customer"])
    required = {
        "Income_Segment",
        "Spending_Segment",
        "Dominant_Channel",
        "Dominant_Category",
        "Primary_Strategic_Segment",
        "PCA_PC1",
        "PCA_PC2",
        "Campaign_Total_Contacts",
        "Campaign_Total_Accepted",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(
            "El archivo del dashboard está desactualizado. Faltan: " + ", ".join(missing)
        )
    return data


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{ --primary: {COLORS['primary']}; --secondary: {COLORS['secondary']}; }}
        .stApp {{ background: #F7F8FA; }}
        .block-container {{ max-width: 1480px; padding-top: 1.8rem; padding-bottom: 3rem; }}
        h1 {{ color: #1F2933; letter-spacing: -0.03em; }}
        h2, h3 {{ color: #293845; }}
        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #E3E8EC;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            box-shadow: 0 3px 12px rgba(27, 39, 51, 0.04);
        }}
        [data-testid="stMetricLabel"] {{ color: #5D6B78; }}
        [data-testid="stSidebar"] {{ border-right: 1px solid #E4E8EC; }}
        .story-box {{
            background: #FFFFFF;
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 0.9rem 1.1rem;
            margin: 0.2rem 0 1.2rem 0;
            color: #35414B;
        }}
        .small-note {{ color: #667784; font-size: 0.88rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, question: str, story: str) -> None:
    st.title(title)
    st.caption(question)
    st.markdown(f'<div class="story-box">{story}</div>', unsafe_allow_html=True)


def format_mu(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f} MU"


def format_pct(value: float, decimals: int = 1) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}%"


def finance_summary(data: pd.DataFrame) -> dict[str, float]:
    clients = len(data)
    accepted = int(data["Response"].sum()) if clients else 0
    contact_cost = float(data["Z_CostContact"].iloc[0]) if clients else 3.0
    response_revenue = float(data["Z_Revenue"].iloc[0]) if clients else 11.0
    cost = clients * contact_cost
    revenue = accepted * response_revenue
    balance = revenue - cost
    return {
        "clients": clients,
        "accepted": accepted,
        "acceptance_rate": accepted / clients if clients else np.nan,
        "cost": cost,
        "revenue": revenue,
        "balance": balance,
        "roi": balance / cost if cost else np.nan,
    }


def original_campaign_summary(data: pd.DataFrame) -> dict[str, float]:
    contacts = int(data["Campaign_Total_Contacts"].iloc[0])
    accepted = int(data["Campaign_Total_Accepted"].iloc[0])
    contact_cost = float(data["Z_CostContact"].iloc[0])
    response_revenue = float(data["Z_Revenue"].iloc[0])
    cost = contacts * contact_cost
    revenue = accepted * response_revenue
    balance = revenue - cost
    return {
        "clients": contacts,
        "accepted": accepted,
        "acceptance_rate": accepted / contacts,
        "cost": cost,
        "revenue": revenue,
        "balance": balance,
        "roi": balance / cost,
    }


def style_figure(fig, height: int = 390, legend_horizontal: bool = False):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=55, b=30),
        font=dict(family="Arial", color="#33414C"),
        title_font=dict(size=17),
        hoverlabel=dict(bgcolor="white"),
    )
    if legend_horizontal:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    return fig


def show_figure(fig, height: int = 390, legend_horizontal: bool = False) -> None:
    st.plotly_chart(
        style_figure(fig, height=height, legend_horizontal=legend_horizontal),
        width="stretch",
        config={"displayModeBar": False},
    )


def multiselect_filter(
    data: pd.DataFrame,
    column: str,
    label: str,
    key: str,
    options: list | None = None,
) -> pd.DataFrame:
    available = options or sorted(data[column].dropna().unique().tolist())
    selected = st.sidebar.multiselect(label, available, key=key)
    return data[data[column].isin(selected)] if selected else data


def range_filter(
    data: pd.DataFrame,
    column: str,
    label: str,
    key: str,
    integer: bool = False,
) -> pd.DataFrame:
    series = data[column].dropna()
    if series.empty:
        return data
    minimum = int(series.min()) if integer else float(series.min())
    maximum = int(series.max()) if integer else float(series.max())
    if minimum == maximum:
        st.sidebar.caption(f"{label}: {minimum}")
        return data
    step = 1 if integer else max((maximum - minimum) / 100, 1.0)
    selected = st.sidebar.slider(
        label,
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        step=step,
        key=key,
    )
    return data[data[column].between(selected[0], selected[1])]


def response_filter(data: pd.DataFrame, key: str) -> pd.DataFrame:
    selection = st.sidebar.selectbox(
        "Respuesta a la última campaña",
        ["Todos", "Aceptó", "No aceptó"],
        key=key,
    )
    if selection == "Aceptó":
        return data[data["Response"].eq(1)]
    if selection == "No aceptó":
        return data[data["Response"].eq(0)]
    return data


def strategic_filter(data: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    if not selected:
        return data
    mask = pd.Series(False, index=data.index)
    for segment in selected:
        mask |= data[STRATEGIC_FLAGS[segment]].astype(bool)
    return data[mask]


def strategic_summary(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for segment, flag in STRATEGIC_FLAGS.items():
        subset = data[data[flag].astype(bool)]
        if subset.empty:
            continue
        financial = finance_summary(subset)
        rows.append(
            {
                "Segmento": segment,
                "Clientes": len(subset),
                "Gasto promedio": subset["Total_Spending"].mean(),
                "Gasto mediano": subset["Total_Spending"].median(),
                "Aceptación (%)": subset["Response"].mean() * 100,
                "Balance (MU)": financial["balance"],
                "Canal principal": subset["Dominant_Channel"].mode().iat[0],
                "Categoría principal": subset["Dominant_Category"].mode().iat[0],
                "Antigüedad promedio": subset["Customer_Tenure_Days"].mean(),
                "Recencia promedio": subset["Recency"].mean(),
            }
        )
    return pd.DataFrame(rows)


def empty_guard(data: pd.DataFrame) -> None:
    if data.empty:
        st.warning("No hay clientes que cumplan la combinación actual de filtros.")
        st.stop()


def finance_waterfall(data: pd.DataFrame, title: str, summary: dict[str, float] | None = None):
    finance = summary or finance_summary(data)
    fig = go.Figure(
        go.Waterfall(
            x=["Costo", "Ingreso", "Balance"],
            y=[-finance["cost"], finance["revenue"], finance["balance"]],
            measure=["relative", "relative", "total"],
            text=[
                format_mu(-finance["cost"]),
                format_mu(finance["revenue"]),
                format_mu(finance["balance"]),
            ],
            textposition="outside",
            connector={"line": {"color": "#A7B1BA"}},
            increasing={"marker": {"color": COLORS["positive"]}},
            decreasing={"marker": {"color": COLORS["negative"]}},
            totals={"marker": {"color": COLORS["primary"]}},
        )
    )
    fig.update_layout(title=title, yaxis_title="MU", showlegend=False)
    return fig
