import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pages.common import (
    COLORES,
    BANDERAS_ESTRATEGICAS,
    validar_no_vacio,
    formatear_mu,
    formatear_porcentaje,
    cargar_datos,
    filtro_multiseleccion,
    encabezado_pagina,
    filtro_rango,
    mostrar_figura,
    mostrar_metricas,
    filtro_estrategico,
    resumen_estrategico,
)


datos = cargar_datos()

encabezado_pagina(
    "Segmentos estratégicos de clientes",
    "¿Qué grupos son más importantes para la estrategia comercial?",
    "Los segmentos convierten patrones descriptivos en grupos comparables. No son clases "
    "exclusivas: una persona puede ser, por ejemplo, premium, multicanal y leal al mismo tiempo.",
)

st.sidebar.markdown("### Filtros de segmentos")
segmentos_seleccionados = st.sidebar.multiselect(
    "Segmento estratégico",
    list(BANDERAS_ESTRATEGICAS.keys()),
    key="segmentos_seleccionados",
)
filtrados = filtro_multiseleccion(
    datos,
    "Income_Segment",
    "Nivel de ingreso",
    "segmentos_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Spending_Segment",
    "Nivel de gasto",
    "segmentos_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Channel", "Canal dominante", "segmentos_canal"
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Category", "Categoría dominante", "segmentos_categoria"
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Tenure_Group",
    "Antigüedad",
    "segmentos_antiguedad",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
filtrados = filtro_rango(filtrados, "Recency", "Recencia", "segmentos_recencia", entero=True)
filtrados = filtro_estrategico(filtrados, segmentos_seleccionados)
validar_no_vacio(filtrados)

resumen = resumen_estrategico(filtrados)
mostrar_metricas(
    [
        {"titulo": "Clientes visibles", "valor": f"{len(filtrados):,}"},
        {
            "titulo": "Gasto promedio",
            "valor": formatear_mu(filtrados["Total_Spending"].mean(), 1),
        },
        {
            "titulo": "Aceptación",
            "valor": formatear_porcentaje(filtrados["Response"].mean() * 100, 2),
        },
        {
            "titulo": "Canal principal",
            "valor": filtrados["Dominant_Channel"].mode().iat[0],
        },
        {
            "titulo": "Categoría principal",
            "valor": filtrados["Dominant_Category"].mode().iat[0],
        },
    ]
)

st.subheader("Comparación de segmentos")
resumen_mostrado = resumen.copy()
for columna in ["Gasto promedio", "Gasto mediano", "Aceptación (%)", "Balance (MU)"]:
    resumen_mostrado[columna] = resumen_mostrado[columna].round(2)
st.dataframe(
    resumen_mostrado,
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

izquierda, derecha = st.columns(2)
with izquierda:
    figura_gasto = px.bar(
        resumen.sort_values("Gasto promedio"),
        x="Gasto promedio",
        y="Segmento",
        orientation="h",
        text="Gasto promedio",
        color="Aceptación (%)",
        color_continuous_scale=[[0, "#DCE5EA"], [1, COLORES["primario"]]],
        title="Gasto promedio por segmento",
    )
    figura_gasto.update_traces(texttemplate="%{text:,.0f} MU", textposition="outside")
    mostrar_figura(figura_gasto)

with derecha:
    figura_respuestas = px.bar(
        resumen.sort_values("Aceptación (%)"),
        x="Aceptación (%)",
        y="Segmento",
        orientation="h",
        text="Aceptación (%)",
        color_discrete_sequence=[COLORES["positivo"]],
        title="Aceptación histórica por segmento",
    )
    figura_respuestas.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    mostrar_figura(figura_respuestas)


def mezcla_segmento(columna: str) -> pd.DataFrame:
    registros = []
    for segmento, bandera in BANDERAS_ESTRATEGICAS.items():
        subconjunto = filtrados[filtrados[bandera].astype(bool)]
        if subconjunto.empty:
            continue
        participaciones = subconjunto[columna].value_counts(normalize=True).mul(100)
        for categoria, participacion in participaciones.items():
            registros.append({"Segmento": segmento, "Categoría": categoria, "Porcentaje": participacion})
    return pd.DataFrame(registros)


izquierda, derecha = st.columns(2)
with izquierda:
    mezcla_categorias = mezcla_segmento("Dominant_Category")
    tabla_categorias = mezcla_categorias.pivot(
        index="Segmento", columns="Categoría", values="Porcentaje"
    ).fillna(0)
    mapa_categorias = go.Figure(
        go.Heatmap(
            z=tabla_categorias.values,
            x=tabla_categorias.columns,
            y=tabla_categorias.index,
            colorscale=[[0, "#F2F4F6"], [1, COLORES["primario"]]],
            colorbar_title="%",
            text=tabla_categorias.values,
            texttemplate="%{text:.0f}%",
        )
    )
    mapa_categorias.update_layout(title="Categoría dominante por segmento")
    mostrar_figura(mapa_categorias)

with derecha:
    mezcla_canales = mezcla_segmento("Dominant_Channel")
    tabla_canales = mezcla_canales.pivot(
        index="Segmento", columns="Categoría", values="Porcentaje"
    ).fillna(0)
    mapa_canales = go.Figure(
        go.Heatmap(
            z=tabla_canales.values,
            x=tabla_canales.columns,
            y=tabla_canales.index,
            colorscale=[[0, "#F2F4F6"], [1, COLORES["secundario"]]],
            colorbar_title="%",
            text=tabla_canales.values,
            texttemplate="%{text:.0f}%",
        )
    )
    mapa_canales.update_layout(title="Canal dominante por segmento")
    mostrar_figura(mapa_canales)

izquierda, derecha = st.columns([1.25, 1])
with izquierda:
    figura_pca = px.scatter(
        filtrados,
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
    mostrar_figura(figura_pca, altura=450, leyenda_horizontal=True)

with derecha:
    cuadrante = px.scatter(
        resumen,
        x="Aceptación (%)",
        y="Gasto promedio",
        size="Clientes",
        color="Segmento",
        text="Segmento",
        title="Matriz de priorización",
        labels={"Gasto promedio": "Gasto promedio (MU)"},
    )
    cuadrante.add_vline(x=filtrados["Response"].mean() * 100, line_dash="dot")
    cuadrante.add_hline(y=filtrados["Total_Spending"].mean(), line_dash="dot")
    cuadrante.update_traces(textposition="top center")
    cuadrante.update_layout(showlegend=False)
    mostrar_figura(cuadrante, altura=450)

st.caption(
    "El PCA resume 59.06% de la varianza de seis variables y no prueba la existencia de "
    "clusters. El segmento primario usa una prioridad documentada solo para colorear puntos; "
    "las métricas de los segmentos conservan el solapamiento real."
)
