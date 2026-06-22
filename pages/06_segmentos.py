import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pages.common import (
    COLORS,
    STRATEGIC_FLAGS,
    empty_guard,
    format_mu,
    format_pct,
    load_data,
    multiselect_filter,
    page_header,
    range_filter,
    show_figure,
    strategic_filter,
    strategic_summary,
)


data = load_data()

page_header(
    "Segmentos estratégicos de clientes",
    "¿Qué grupos son más importantes para la estrategia comercial?",
    "Los segmentos convierten patrones descriptivos en cohortes comparables. No son clases "
    "exclusivas: una persona puede ser, por ejemplo, premium, multicanal y leal al mismo tiempo.",
)

st.sidebar.markdown("### Filtros de segmentos")
selected_segments = st.sidebar.multiselect(
    "Segmento estratégico",
    list(STRATEGIC_FLAGS.keys()),
    key="segments_selected",
)
filtered = multiselect_filter(
    data,
    "Income_Segment",
    "Nivel de ingreso",
    "segments_income",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtered = multiselect_filter(
    filtered,
    "Spending_Segment",
    "Nivel de gasto",
    "segments_spending",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtered = multiselect_filter(
    filtered, "Dominant_Channel", "Canal dominante", "segments_channel"
)
filtered = multiselect_filter(
    filtered, "Dominant_Category", "Categoría dominante", "segments_category"
)
filtered = multiselect_filter(
    filtered,
    "Tenure_Group",
    "Antigüedad",
    "segments_tenure",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
filtered = range_filter(filtered, "Recency", "Recencia", "segments_recency", integer=True)
filtered = strategic_filter(filtered, selected_segments)
empty_guard(filtered)

summary = strategic_summary(filtered)
metrics = st.columns(5)
metrics[0].metric("Clientes visibles", f"{len(filtered):,}")
metrics[1].metric("Gasto promedio", format_mu(filtered["Total_Spending"].mean(), 1))
metrics[2].metric("Aceptación", format_pct(filtered["Response"].mean() * 100, 2))
metrics[3].metric("Canal principal", filtered["Dominant_Channel"].mode().iat[0])
metrics[4].metric("Categoría principal", filtered["Dominant_Category"].mode().iat[0])

st.subheader("Comparación de cohortes")
display_summary = summary.copy()
for column in ["Gasto promedio", "Gasto mediano", "Aceptación (%)", "Balance (MU)"]:
    display_summary[column] = display_summary[column].round(2)
st.dataframe(
    display_summary,
    hide_index=True,
    width="stretch",
    column_config={
        "Gasto promedio": st.column_config.NumberColumn(format="%.2f MU"),
        "Gasto mediano": st.column_config.NumberColumn(format="%.2f MU"),
        "Aceptación (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Balance (MU)": st.column_config.NumberColumn(format="%.0f MU"),
        "Antigüedad promedio": st.column_config.NumberColumn(format="%.0f días"),
        "Recencia promedio": st.column_config.NumberColumn(format="%.1f días"),
    },
)

left, right = st.columns(2)
with left:
    spending_fig = px.bar(
        summary.sort_values("Gasto promedio"),
        x="Gasto promedio",
        y="Segmento",
        orientation="h",
        text="Gasto promedio",
        color="Aceptación (%)",
        color_continuous_scale=[[0, "#DCE5EA"], [1, COLORS["primary"]]],
        title="Gasto promedio por segmento",
    )
    spending_fig.update_traces(texttemplate="%{text:,.0f} MU", textposition="outside")
    show_figure(spending_fig)

with right:
    response_fig = px.bar(
        summary.sort_values("Aceptación (%)"),
        x="Aceptación (%)",
        y="Segmento",
        orientation="h",
        text="Aceptación (%)",
        color_discrete_sequence=[COLORS["positive"]],
        title="Aceptación histórica por segmento",
    )
    response_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    show_figure(response_fig)


def segment_mix(column: str) -> pd.DataFrame:
    records = []
    for segment, flag in STRATEGIC_FLAGS.items():
        subset = filtered[filtered[flag].astype(bool)]
        if subset.empty:
            continue
        shares = subset[column].value_counts(normalize=True).mul(100)
        for category, share in shares.items():
            records.append({"Segmento": segment, "Categoría": category, "Porcentaje": share})
    return pd.DataFrame(records)


left, right = st.columns(2)
with left:
    category_mix = segment_mix("Dominant_Category")
    category_pivot = category_mix.pivot(
        index="Segmento", columns="Categoría", values="Porcentaje"
    ).fillna(0)
    category_heat = go.Figure(
        go.Heatmap(
            z=category_pivot.values,
            x=category_pivot.columns,
            y=category_pivot.index,
            colorscale=[[0, "#F2F4F6"], [1, COLORS["primary"]]],
            colorbar_title="%",
            text=category_pivot.values,
            texttemplate="%{text:.0f}%",
        )
    )
    category_heat.update_layout(title="Categoría dominante por segmento")
    show_figure(category_heat)

with right:
    channel_mix = segment_mix("Dominant_Channel")
    channel_pivot = channel_mix.pivot(
        index="Segmento", columns="Categoría", values="Porcentaje"
    ).fillna(0)
    channel_heat = go.Figure(
        go.Heatmap(
            z=channel_pivot.values,
            x=channel_pivot.columns,
            y=channel_pivot.index,
            colorscale=[[0, "#F2F4F6"], [1, COLORS["secondary"]]],
            colorbar_title="%",
            text=channel_pivot.values,
            texttemplate="%{text:.0f}%",
        )
    )
    channel_heat.update_layout(title="Canal dominante por segmento")
    show_figure(channel_heat)

left, right = st.columns([1.25, 1])
with left:
    pca_fig = px.scatter(
        filtered,
        x="PCA_PC1",
        y="PCA_PC2",
        color="Primary_Strategic_Segment",
        opacity=0.55,
        hover_data=["Total_Spending", "Income", "Response"],
        title="PCA exploratorio por segmento primario",
        labels={
            "PCA_PC1": "Componente principal 1",
            "PCA_PC2": "Componente principal 2",
            "Primary_Strategic_Segment": "Segmento primario",
        },
    )
    show_figure(pca_fig, height=450, legend_horizontal=True)

with right:
    quadrant = px.scatter(
        summary,
        x="Aceptación (%)",
        y="Gasto promedio",
        size="Clientes",
        color="Segmento",
        text="Segmento",
        title="Matriz de priorización",
        labels={"Gasto promedio": "Gasto promedio (MU)"},
    )
    quadrant.add_vline(x=filtered["Response"].mean() * 100, line_dash="dot")
    quadrant.add_hline(y=filtered["Total_Spending"].mean(), line_dash="dot")
    quadrant.update_traces(textposition="top center")
    quadrant.update_layout(showlegend=False)
    show_figure(quadrant, height=450)

st.caption(
    "El PCA resume 59.06% de la varianza de seis variables y no prueba la existencia de "
    "clusters. El segmento primario usa una prioridad documentada solo para colorear puntos; "
    "las métricas de cohortes conservan el solapamiento real."
)
