import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    CAMPAIGN_COLUMNS,
    COLORS,
    empty_guard,
    finance_summary,
    format_mu,
    format_pct,
    load_data,
    multiselect_filter,
    page_header,
    response_filter,
    show_figure,
)


data = load_data()

page_header(
    "Respuesta histórica a campañas",
    "¿Qué tipo de clientes aceptaron campañas y qué tan rentable fue contactarlos?",
    "Esta vista compara respuestas históricas. Los resultados describen lo ocurrido en la muestra; "
    "no representan una predicción de respuesta futura.",
)

st.sidebar.markdown("### Filtros de campañas")
selected_campaigns = st.sidebar.multiselect(
    "Campañas mostradas",
    list(CAMPAIGN_COLUMNS.values()),
    default=list(CAMPAIGN_COLUMNS.values()),
    key="campaign_shown",
)
filtered = response_filter(data, "campaign_response")
filtered = multiselect_filter(
    filtered,
    "Spending_Segment",
    "Segmento de gasto",
    "campaign_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtered = multiselect_filter(
    filtered,
    "Income_Segment",
    "Segmento de ingreso",
    "campaign_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtered = multiselect_filter(
    filtered, "Dominant_Channel", "Canal dominante", "campaign_channel"
)
filtered = multiselect_filter(
    filtered,
    "Tenure_Group",
    "Segmento de antigüedad",
    "campaign_tenure",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
filtered = multiselect_filter(
    filtered, "Dominant_Category", "Categoría dominante", "campaign_category"
)
complaint = st.sidebar.selectbox(
    "Quejas",
    ["Todos", "Con queja", "Sin queja"],
    key="campaign_complaint",
)
if complaint == "Con queja":
    filtered = filtered[filtered["Complain"].eq(1)]
elif complaint == "Sin queja":
    filtered = filtered[filtered["Complain"].eq(0)]
empty_guard(filtered)

finance = finance_summary(filtered)
metrics = st.columns(6)
metrics[0].metric("Clientes", f"{len(filtered):,}")
metrics[1].metric(
    "Aceptación última campaña", format_pct(finance["acceptance_rate"] * 100, 2)
)
metrics[2].metric("Aceptaron última", f"{finance['accepted']:,}")
metrics[3].metric(
    "Aceptaciones previas", f"{int(filtered['Accepted_Campaigns_Total'].sum()):,}"
)
metrics[4].metric("Balance histórico", format_mu(finance["balance"]))
metrics[5].metric("Quejas", format_pct(filtered["Complain"].mean() * 100, 2))

campaign_rows = []
for column, label in CAMPAIGN_COLUMNS.items():
    if label in selected_campaigns:
        campaign_rows.append(
            {
                "Campaña": label,
                "Aceptaciones": int(filtered[column].sum()),
                "Tasa (%)": filtered[column].mean() * 100,
            }
        )
campaign_data = pd.DataFrame(campaign_rows)
if not campaign_data.empty:
    campaign_fig = px.bar(
        campaign_data,
        x="Campaña",
        y="Tasa (%)",
        text="Tasa (%)",
        color="Campaña",
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="Tasa de aceptación por campaña",
    )
    campaign_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    campaign_fig.update_layout(showlegend=False)
    show_figure(campaign_fig)
else:
    st.info("Selecciona al menos una campaña para mostrar la comparación.")

def response_by(column: str, label: str):
    result = (
        filtered.groupby(column, observed=True)["Response"]
        .agg(Clientes="size", Aceptación="mean")
        .reset_index()
    )
    result["Aceptación (%)"] = result["Aceptación"] * 100
    fig = px.bar(
        result,
        x=column,
        y="Aceptación (%)",
        text="Aceptación (%)",
        color=column,
        title=f"Aceptación por {label}",
        labels={column: label},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False)
    return fig


left, middle, right = st.columns(3)
with left:
    show_figure(response_by("Spending_Segment", "gasto"), height=370)
with middle:
    show_figure(response_by("Income_Segment", "ingreso"), height=370)
with right:
    show_figure(response_by("Dominant_Channel", "canal"), height=370)

left, right = st.columns(2)
with left:
    response_box_data = filtered.assign(
        Respuesta=filtered["Response"].map({0: "No aceptó", 1: "Aceptó"})
    )
    response_box = px.box(
        response_box_data,
        x="Respuesta",
        y="Total_Spending",
        color="Respuesta",
        points=False,
        color_discrete_map={"Aceptó": COLORS["positive"], "No aceptó": COLORS["muted"]},
        title="Gasto total según respuesta",
        labels={"Total_Spending": "Gasto total (MU)"},
    )
    response_box.update_layout(showlegend=False)
    show_figure(response_box)

with right:
    financial_rows = []
    for segment, subset in filtered.groupby("Spending_Segment", observed=True):
        segment_finance = finance_summary(subset)
        financial_rows.extend(
            [
                {"Segmento": segment, "Concepto": "Costo", "MU": segment_finance["cost"]},
                {"Segmento": segment, "Concepto": "Ingreso", "MU": segment_finance["revenue"]},
                {"Segmento": segment, "Concepto": "Balance", "MU": segment_finance["balance"]},
            ]
        )
    financial_data = pd.DataFrame(financial_rows)
    finance_fig = px.bar(
        financial_data,
        x="Segmento",
        y="MU",
        color="Concepto",
        barmode="group",
        color_discrete_map={
            "Costo": COLORS["negative"],
            "Ingreso": COLORS["positive"],
            "Balance": COLORS["primary"],
        },
        title="Costo, ingreso y balance por gasto",
    )
    show_figure(finance_fig, legend_horizontal=True)

st.caption(
    "Costo = clientes contactados × 3 MU; ingreso = respuestas positivas × 11 MU. "
    "La comparación segmentada es retrospectiva y no controla por otras variables."
)
