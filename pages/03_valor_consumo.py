import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLORS,
    PRODUCT_COLUMNS,
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
    "Valor y consumo por categorías",
    "¿Cuánto gastan los clientes y en qué productos se concentra el consumo?",
    "El gasto está distribuido de forma desigual. Esta vista distingue el valor total del cliente "
    "y la composición agregada del consumo, sin mezclar todavía el análisis de canales.",
)

st.sidebar.markdown("### Filtros de valor")
filtered = multiselect_filter(
    data,
    "Income_Segment",
    "Segmento de ingreso",
    "value_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtered = multiselect_filter(
    filtered,
    "Spending_Segment",
    "Segmento de gasto",
    "value_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
selected_categories = st.sidebar.multiselect(
    "Categorías mostradas",
    list(PRODUCT_COLUMNS.values()),
    default=list(PRODUCT_COLUMNS.values()),
    key="value_categories",
)
filtered = range_filter(filtered, "Age", "Edad", "value_age", integer=True)
filtered = multiselect_filter(filtered, "Education", "Educación", "value_education")
filtered = multiselect_filter(
    filtered, "Family_Segment", "Segmento familiar", "value_family"
)
filtered = response_filter(filtered, "value_response")
empty_guard(filtered)

product_columns = [
    column for column, label in PRODUCT_COLUMNS.items() if label in selected_categories
]
if not product_columns:
    product_columns = list(PRODUCT_COLUMNS.keys())

aggregate = filtered[list(PRODUCT_COLUMNS.keys())].sum().sort_values(ascending=False)
dominant_category = PRODUCT_COLUMNS[aggregate.index[0]]
metrics = st.columns(6)
metrics[0].metric("Gasto promedio", format_mu(filtered["Total_Spending"].mean(), 1))
metrics[1].metric("Gasto mediano", format_mu(filtered["Total_Spending"].median(), 1))
metrics[2].metric("Gasto máximo", format_mu(filtered["Total_Spending"].max(), 0))
metrics[3].metric(
    "Clientes premium",
    format_pct(filtered["Value_Segment"].eq("Alto valor").mean() * 100, 1),
)
metrics[4].metric("Categoría principal", dominant_category)
metrics[5].metric("Gasto en vinos", format_mu(filtered["MntWines"].mean(), 1))

left, right = st.columns(2)
with left:
    spending_hist = px.histogram(
        filtered,
        x="Total_Spending",
        nbins=35,
        color_discrete_sequence=[COLORS["primary"]],
        title="Distribución del gasto total",
        labels={"Total_Spending": "Gasto total (MU)", "count": "Clientes"},
    )
    show_figure(spending_hist)

with right:
    spending_income = px.box(
        filtered,
        x="Income_Segment",
        y="Total_Spending",
        category_orders={
            "Income_Segment": ["Ingreso bajo", "Ingreso medio", "Ingreso alto"]
        },
        points=False,
        color="Income_Segment",
        color_discrete_sequence=["#A9C4D0", "#4F8CA5", COLORS["primary"]],
        title="Gasto por segmento de ingreso",
        labels={"Income_Segment": "Ingreso", "Total_Spending": "Gasto total (MU)"},
    )
    spending_income.update_layout(showlegend=False)
    show_figure(spending_income)

category_stats = pd.DataFrame(
    {
        "Categoría": [PRODUCT_COLUMNS[column] for column in product_columns],
        "Gasto promedio": [filtered[column].mean() for column in product_columns],
        "Gasto total": [filtered[column].sum() for column in product_columns],
    }
).sort_values("Gasto total", ascending=False)
category_stats["Participación"] = category_stats["Gasto total"] / category_stats["Gasto total"].sum()

left, right = st.columns(2)
with left:
    average_fig = px.bar(
        category_stats.sort_values("Gasto promedio"),
        x="Gasto promedio",
        y="Categoría",
        orientation="h",
        text="Gasto promedio",
        color_discrete_sequence=[COLORS["secondary"]],
        title="Gasto promedio por categoría",
    )
    average_fig.update_traces(texttemplate="%{text:,.1f} MU", textposition="outside")
    show_figure(average_fig)

with right:
    composition_fig = px.pie(
        category_stats,
        names="Categoría",
        values="Gasto total",
        hole=0.55,
        color_discrete_sequence=["#7A243A", "#176B87", "#D18B47", "#769F8D", "#A386B5", "#C6A15B"],
        title="Composición agregada del gasto",
    )
    composition_fig.update_traces(textinfo="percent+label", textposition="inside")
    show_figure(composition_fig)

long_products = filtered[product_columns].rename(columns=PRODUCT_COLUMNS).melt(
    var_name="Categoría", value_name="Gasto"
)
left, right = st.columns([1.45, 1])
with left:
    category_box = px.box(
        long_products,
        x="Categoría",
        y="Gasto",
        points=False,
        color_discrete_sequence=[COLORS["accent"]],
        title="Dispersión del gasto por categoría",
        labels={"Gasto": "Gasto (MU)"},
    )
    show_figure(category_box)

with right:
    st.markdown("#### Ranking comercial")
    ranking = category_stats[["Categoría", "Gasto total", "Participación"]].copy()
    ranking["Gasto total"] = ranking["Gasto total"].round(0)
    ranking["Participación"] = (ranking["Participación"] * 100).round(2)
    st.dataframe(
        ranking,
        hide_index=True,
        width="stretch",
        column_config={
            "Gasto total": st.column_config.NumberColumn(format="%,.0f MU"),
            "Participación": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
    st.caption(
        "La participación se calcula con sumas agregadas. No es el promedio de porcentajes "
        "individuales por cliente."
    )
