import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pages.common import (
    CHANNEL_COLUMNS,
    COLORS,
    empty_guard,
    format_mu,
    format_pct,
    load_data,
    multiselect_filter,
    page_header,
    range_filter,
    response_filter,
    show_figure,
)


data = load_data()

page_header(
    "Canales y comportamiento de compra",
    "¿Por dónde compran los clientes y qué canales concentran mayor valor?",
    "Los canales describen cómo se relaciona cada cliente con la empresa. Esta página separa "
    "frecuencia de compra, navegación web y sensibilidad a descuentos.",
)

st.sidebar.markdown("### Filtros de canales")
filtered = multiselect_filter(data, "Dominant_Channel", "Canal dominante", "channel_main")
filtered = multiselect_filter(
    filtered,
    "Spending_Segment",
    "Segmento de gasto",
    "channel_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtered = multiselect_filter(
    filtered,
    "Income_Segment",
    "Segmento de ingreso",
    "channel_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtered = range_filter(
    filtered,
    "NumDealsPurchases",
    "Compras con descuento",
    "channel_deals",
    integer=True,
)
filtered = range_filter(
    filtered,
    "NumWebVisitsMonth",
    "Visitas web mensuales",
    "channel_visits",
    integer=True,
)
filtered = multiselect_filter(
    filtered, "Dominant_Category", "Categoría dominante", "channel_category"
)
filtered = response_filter(filtered, "channel_response")
empty_guard(filtered)

metrics = st.columns(6)
metrics[0].metric("Compras web", f"{filtered['NumWebPurchases'].mean():.2f}")
metrics[1].metric("Compras catálogo", f"{filtered['NumCatalogPurchases'].mean():.2f}")
metrics[2].metric("Compras tienda", f"{filtered['NumStorePurchases'].mean():.2f}")
metrics[3].metric("Visitas web", f"{filtered['NumWebVisitsMonth'].mean():.2f}")
metrics[4].metric("Compras con descuento", f"{filtered['NumDealsPurchases'].mean():.2f}")
metrics[5].metric(
    "Clientes multicanal",
    format_pct(filtered["Channel_Segment"].eq("Multicanal").mean() * 100, 1),
)

channel_average = pd.DataFrame(
    {
        "Canal": list(CHANNEL_COLUMNS.values()),
        "Compras promedio": [filtered[column].mean() for column in CHANNEL_COLUMNS],
    }
)
left, right = st.columns(2)
with left:
    channel_bar = px.bar(
        channel_average,
        x="Canal",
        y="Compras promedio",
        color="Canal",
        text="Compras promedio",
        color_discrete_sequence=[COLORS["secondary"], COLORS["accent"], COLORS["primary"]],
        title="Compras promedio por canal",
    )
    channel_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    channel_bar.update_layout(showlegend=False)
    show_figure(channel_bar)

with right:
    spend_channel = px.box(
        filtered,
        x="Dominant_Channel",
        y="Total_Spending",
        color="Dominant_Channel",
        points=False,
        title="Gasto por canal dominante",
        labels={"Dominant_Channel": "Canal", "Total_Spending": "Gasto total (MU)"},
    )
    spend_channel.update_layout(showlegend=False)
    show_figure(spend_channel)

left, right = st.columns(2)
with left:
    web_scatter = px.scatter(
        filtered,
        x="NumWebVisitsMonth",
        y="NumWebPurchases",
        color="Spending_Segment",
        opacity=0.55,
        title="Visitas web y compras web",
        labels={
            "NumWebVisitsMonth": "Visitas web en el último mes",
            "NumWebPurchases": "Compras web en dos años",
            "Spending_Segment": "Gasto",
        },
    )
    show_figure(web_scatter, legend_horizontal=True)

with right:
    catalog_scatter = px.scatter(
        filtered,
        x="NumCatalogPurchases",
        y="Total_Spending",
        color="Value_Segment",
        opacity=0.55,
        color_discrete_map={"Alto valor": COLORS["primary"], "Resto": "#AAB6BF"},
        title="Compras por catálogo y gasto total",
        labels={
            "NumCatalogPurchases": "Compras por catálogo",
            "Total_Spending": "Gasto total (MU)",
            "Value_Segment": "Valor",
        },
    )
    show_figure(catalog_scatter, legend_horizontal=True)

left, right = st.columns(2)
with left:
    deals = (
        filtered.groupby("Spending_Segment", observed=True)["NumDealsPurchases"]
        .mean()
        .rename("Compras con descuento")
        .reset_index()
    )
    deals_fig = px.bar(
        deals,
        x="Spending_Segment",
        y="Compras con descuento",
        text="Compras con descuento",
        color_discrete_sequence=[COLORS["accent"]],
        title="Uso de descuentos por segmento de gasto",
        labels={"Spending_Segment": "Segmento de gasto"},
    )
    deals_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    show_figure(deals_fig)

with right:
    spending_order = ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"]
    heat = pd.crosstab(filtered["Dominant_Channel"], filtered["Spending_Segment"])
    heat = heat.reindex(columns=spending_order, fill_value=0)
    heat_fig = go.Figure(
        go.Heatmap(
            z=heat.values,
            x=heat.columns,
            y=heat.index,
            colorscale=[[0, "#F0F3F5"], [1, COLORS["primary"]]],
            text=heat.values,
            texttemplate="%{text}",
            colorbar_title="Clientes",
        )
    )
    heat_fig.update_layout(title="Canal dominante y segmento de gasto")
    show_figure(heat_fig)

valid_ratio = filtered["Web_Purchase_Visit_Ratio"].dropna()
st.caption(
    f"Razón mediana compras/visitas web: {valid_ratio.median():.2f}. No es una tasa de "
    "conversión real: las compras cubren dos años y las visitas solo el último mes."
)
