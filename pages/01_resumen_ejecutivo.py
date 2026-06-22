import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLORS,
    empty_guard,
    finance_summary,
    finance_waterfall,
    format_mu,
    format_pct,
    load_data,
    multiselect_filter,
    original_campaign_summary,
    page_header,
    response_filter,
    show_figure,
    strategic_summary,
)


data = load_data()

page_header(
    "Resumen ejecutivo",
    "¿Cuál es el problema comercial?",
    "La campaña masiva tuvo un balance histórico negativo. El objetivo del dashboard es "
    "identificar grupos con mayor valor y mejor respuesta para evaluar una selección más eficiente.",
)

st.sidebar.markdown("### Filtros del resumen")
filtered = multiselect_filter(
    data,
    "Spending_Segment",
    "Segmento de gasto",
    "exec_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtered = multiselect_filter(
    filtered,
    "Income_Segment",
    "Segmento de ingreso",
    "exec_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtered = multiselect_filter(
    filtered, "Dominant_Channel", "Canal dominante", "exec_channel"
)
filtered = response_filter(filtered, "exec_response")
filtered = multiselect_filter(
    filtered,
    "Tenure_Group",
    "Segmento de antigüedad",
    "exec_tenure",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
empty_guard(filtered)

is_full_sample = filtered.index.equals(data.index)
finance = original_campaign_summary(data) if is_full_sample else finance_summary(filtered)
first_row = st.columns(5)
first_row[0].metric("Clientes analizados", f"{len(filtered):,}")
first_row[1].metric("Contactos evaluados", f"{finance['clients']:,}")
first_row[2].metric("Gasto promedio", format_mu(filtered["Total_Spending"].mean(), 1))
first_row[3].metric("Gasto mediano", format_mu(filtered["Total_Spending"].median(), 1))
first_row[4].metric(
    "Tasa de aceptación", format_pct(finance["acceptance_rate"] * 100, 2)
)

second_row = st.columns(5)
second_row[0].metric("Aceptaron", f"{finance['accepted']:,}")
second_row[1].metric("Costo histórico", format_mu(finance["cost"]))
second_row[2].metric("Ingreso histórico", format_mu(finance["revenue"]))
second_row[3].metric(
    "Balance / ROI",
    format_mu(finance["balance"]),
    delta=format_pct(finance["roi"] * 100, 1),
    delta_color="normal" if finance["roi"] >= 0 else "inverse",
)
second_row[4].metric("Muestra excluida", f"{finance['clients'] - len(filtered):,}")

st.caption(
    "Sin filtros, las finanzas corresponden a los 2,240 contactos originales; el gasto y los "
    "segmentos usan los 2,237 registros válidos. Al filtrar, las finanzas se recalculan sobre "
    "la selección visible."
)

left, right = st.columns(2)
with left:
    response_counts = (
        filtered["Response"]
        .map({0: "No aceptó", 1: "Aceptó"})
        .value_counts()
        .rename_axis("Respuesta")
        .reset_index(name="Clientes")
    )
    response_fig = px.bar(
        response_counts,
        x="Respuesta",
        y="Clientes",
        color="Respuesta",
        text_auto=",",
        color_discrete_map={"Aceptó": COLORS["positive"], "No aceptó": COLORS["muted"]},
        title="Respuesta a la última campaña",
    )
    response_fig.update_layout(showlegend=False)
    show_figure(response_fig)

with right:
    show_figure(finance_waterfall(filtered, "Resultado histórico del contacto", finance))

st.subheader("Segmentos con mayor gasto promedio")
ranking = strategic_summary(filtered).sort_values("Gasto promedio", ascending=False).head(5)
ranking_fig = px.bar(
    ranking.sort_values("Gasto promedio"),
    x="Gasto promedio",
    y="Segmento",
    orientation="h",
    text="Gasto promedio",
    color="Aceptación (%)",
    color_continuous_scale=[[0, "#DCE5EA"], [1, COLORS["primary"]]],
    title="Valor promedio y aceptación histórica",
)
ranking_fig.update_traces(texttemplate="%{text:,.0f} MU", textposition="outside")
ranking_fig.update_layout(coloraxis_colorbar_title="Aceptación %")
show_figure(ranking_fig, height=360)
st.caption(
    "Los segmentos estratégicos son cohortes descriptivas y pueden solaparse; un cliente puede "
    "pertenecer a más de una."
)
