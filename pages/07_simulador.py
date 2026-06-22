import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLORS,
    STRATEGIC_FLAGS,
    empty_guard,
    finance_summary,
    format_mu,
    format_pct,
    load_data,
    multiselect_filter,
    original_campaign_summary,
    page_header,
    range_filter,
    show_figure,
    strategic_filter,
)


data = load_data()

page_header(
    "Centro de decisiones y simulador",
    "¿Qué resultado histórico habría tenido una selección de clientes?",
    "Selecciona criterios disponibles antes de la campaña. El panel recalcula costo, ingreso y "
    "balance observados para comparar el grupo con el contacto masivo.",
)

st.sidebar.markdown("### Criterios de selección")
selected_segments = st.sidebar.multiselect(
    "Segmento estratégico",
    list(STRATEGIC_FLAGS.keys()),
    key="sim_segments",
)
selected = multiselect_filter(
    data,
    "Income_Segment",
    "Nivel de ingreso",
    "sim_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
selected = multiselect_filter(
    selected,
    "Spending_Segment",
    "Nivel de gasto",
    "sim_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
selected = multiselect_filter(
    selected, "Dominant_Channel", "Canal dominante", "sim_channel"
)
selected = multiselect_filter(
    selected, "Dominant_Category", "Categoría dominante", "sim_category"
)
selected = range_filter(selected, "Age", "Edad", "sim_age", integer=True)
selected = multiselect_filter(selected, "Education", "Educación", "sim_education")
selected = multiselect_filter(
    selected, "Marital_Status_Grouped", "Estado civil", "sim_marital"
)
selected = multiselect_filter(
    selected, "Family_Segment", "Segmento familiar", "sim_family"
)
selected = multiselect_filter(
    selected,
    "Tenure_Group",
    "Antigüedad",
    "sim_tenure",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
selected = range_filter(selected, "Recency", "Recencia", "sim_recency", integer=True)
selected = range_filter(
    selected,
    "NumDealsPurchases",
    "Compras con descuento",
    "sim_deals",
    integer=True,
)
selected = range_filter(
    selected,
    "NumWebVisitsMonth",
    "Visitas web",
    "sim_visits",
    integer=True,
)
selected = range_filter(
    selected,
    "Accepted_Campaigns_Total",
    "Campañas anteriores aceptadas",
    "sim_previous",
    integer=True,
)
complaint = st.sidebar.selectbox(
    "Quejas",
    ["Todos", "Con queja", "Sin queja"],
    key="sim_complaint",
)
if complaint == "Con queja":
    selected = selected[selected["Complain"].eq(1)]
elif complaint == "Sin queja":
    selected = selected[selected["Complain"].eq(0)]
selected = strategic_filter(selected, selected_segments)
empty_guard(selected)

massive = original_campaign_summary(data)
scenario = finance_summary(selected)
category_main = selected["Dominant_Category"].mode().iat[0]
channel_main = selected["Dominant_Channel"].mode().iat[0]

first_row = st.columns(5)
first_row[0].metric("Clientes seleccionados", f"{scenario['clients']:,}")
first_row[1].metric("Aceptaron", f"{scenario['accepted']:,}")
first_row[2].metric(
    "Aceptación histórica", format_pct(scenario["acceptance_rate"] * 100, 2)
)
first_row[3].metric("Costo estimado", format_mu(scenario["cost"]))
first_row[4].metric("Ingreso histórico", format_mu(scenario["revenue"]))

second_row = st.columns(5)
second_row[0].metric(
    "Balance histórico",
    format_mu(scenario["balance"]),
    delta=format_mu(scenario["balance"] - massive["balance"]),
)
second_row[1].metric("ROI histórico", format_pct(scenario["roi"] * 100, 1))
second_row[2].metric("Gasto promedio", format_mu(selected["Total_Spending"].mean(), 1))
second_row[3].metric("Categoría principal", category_main)
second_row[4].metric("Canal principal", channel_main)

comparison = pd.DataFrame(
    [
        {
            "Escenario": "Contacto masivo",
            "Costo": massive["cost"],
            "Ingreso": massive["revenue"],
            "Balance": massive["balance"],
        },
        {
            "Escenario": "Selección actual",
            "Costo": scenario["cost"],
            "Ingreso": scenario["revenue"],
            "Balance": scenario["balance"],
        },
    ]
).melt(id_vars="Escenario", var_name="Concepto", value_name="MU")

left, right = st.columns([1.15, 1])
with left:
    comparison_fig = px.bar(
        comparison,
        x="Escenario",
        y="MU",
        color="Concepto",
        barmode="group",
        text="MU",
        color_discrete_map={
            "Costo": COLORS["negative"],
            "Ingreso": COLORS["positive"],
            "Balance": COLORS["primary"],
        },
        title="Contacto masivo frente a la selección",
    )
    comparison_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    show_figure(comparison_fig, height=430, legend_horizontal=True)

with right:
    grouped_rows = []
    for segment, subset in selected.groupby("Primary_Strategic_Segment"):
        segment_finance = finance_summary(subset)
        grouped_rows.append(
            {
                "Segmento": segment,
                "Clientes": len(subset),
                "Gasto promedio": subset["Total_Spending"].mean(),
                "Aceptación (%)": subset["Response"].mean() * 100,
                "Balance (MU)": segment_finance["balance"],
                "Canal": subset["Dominant_Channel"].mode().iat[0],
                "Categoría": subset["Dominant_Category"].mode().iat[0],
            }
        )
    priority = pd.DataFrame(grouped_rows).sort_values(
        ["Balance (MU)", "Aceptación (%)"], ascending=False
    )
    st.markdown("#### Grupos priorizados")
    st.dataframe(
        priority,
        hide_index=True,
        width="stretch",
        column_config={
            "Gasto promedio": st.column_config.NumberColumn(format="%.1f MU"),
            "Aceptación (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Balance (MU)": st.column_config.NumberColumn(format="%.0f MU"),
        },
    )

quadrant = px.scatter(
    priority,
    x="Aceptación (%)",
    y="Gasto promedio",
    size="Clientes",
    color="Balance (MU)",
    text="Segmento",
    color_continuous_scale=[[0, COLORS["negative"]], [0.5, "#E9ECEF"], [1, COLORS["positive"]]],
    color_continuous_midpoint=0,
    title="Matriz de priorización del escenario",
    labels={"Gasto promedio": "Gasto promedio (MU)"},
)
quadrant.add_vline(x=selected["Response"].mean() * 100, line_dash="dot")
quadrant.add_hline(y=selected["Total_Spending"].mean(), line_dash="dot")
quadrant.update_traces(textposition="top center")
show_figure(quadrant, height=450)

with st.expander("Ver clientes de la selección"):
    client_table = selected[
        [
            "ID",
            "Age",
            "Income",
            "Total_Spending",
            "Spending_Segment",
            "Dominant_Channel",
            "Dominant_Category",
            "Accepted_Campaigns_Total",
            "Response",
            "Primary_Strategic_Segment",
        ]
    ].sort_values("Total_Spending", ascending=False)
    st.dataframe(client_table, hide_index=True, width="stretch", height=420)

st.warning(
    "Este simulador es retrospectivo: usa la respuesta observada para evaluar el grupo, pero no "
    "predice quién aceptará una campaña futura. Por esa razón, Response no se ofrece como filtro "
    "de selección; hacerlo introduciría fuga de información."
)
