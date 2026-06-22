import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pages.common import (
    COLUMNAS_CANALES,
    COLORES,
    validar_no_vacio,
    formatear_mu,
    formatear_porcentaje,
    cargar_datos,
    filtro_multiseleccion,
    encabezado_pagina,
    filtro_rango,
    filtro_respuesta,
    mostrar_figura,
    mostrar_metricas,
)


datos = cargar_datos()

encabezado_pagina(
    "Canales y comportamiento de compra",
    "¿Por dónde compran los clientes y qué canales concentran mayor valor?",
    "Los canales describen cómo se relaciona cada cliente con la empresa. Esta página separa "
    "frecuencia de compra, navegación web y sensibilidad a descuentos.",
)

st.sidebar.markdown("### Filtros de canales")
filtrados = filtro_multiseleccion(datos, "Dominant_Channel", "Canal dominante", "canal_principal")
filtrados = filtro_multiseleccion(
    filtrados,
    "Spending_Segment",
    "Segmento de gasto",
    "canal_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Income_Segment",
    "Segmento de ingreso",
    "canal_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtrados = filtro_rango(
    filtrados,
    "NumDealsPurchases",
    "Compras con descuento",
    "canal_descuentos",
    entero=True,
)
filtrados = filtro_rango(
    filtrados,
    "NumWebVisitsMonth",
    "Visitas web mensuales",
    "canal_visitas",
    entero=True,
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Category", "Categoría dominante", "canal_categoria"
)
filtrados = filtro_respuesta(filtrados, "canal_respuesta")
validar_no_vacio(filtrados)

mostrar_metricas(
    [
        {"titulo": "Compras web", "valor": f"{filtrados['NumWebPurchases'].mean():.2f}"},
        {
            "titulo": "Compras catálogo",
            "valor": f"{filtrados['NumCatalogPurchases'].mean():.2f}",
        },
        {
            "titulo": "Compras tienda",
            "valor": f"{filtrados['NumStorePurchases'].mean():.2f}",
        },
        {"titulo": "Visitas web", "valor": f"{filtrados['NumWebVisitsMonth'].mean():.2f}"},
        {
            "titulo": "Compras con descuento",
            "valor": f"{filtrados['NumDealsPurchases'].mean():.2f}",
        },
        {
            "titulo": "Clientes multicanal",
            "valor": formatear_porcentaje(
                filtrados["Channel_Segment"].eq("Multicanal").mean() * 100,
                1,
            ),
        },
    ]
)

promedio_canales = pd.DataFrame(
    {
        "Canal": list(COLUMNAS_CANALES.values()),
        "Compras promedio": [filtrados[columna].mean() for columna in COLUMNAS_CANALES],
    }
)
izquierda, derecha = st.columns(2)
with izquierda:
    barras_canales = px.bar(
        promedio_canales,
        x="Canal",
        y="Compras promedio",
        color="Canal",
        text="Compras promedio",
        color_discrete_sequence=[COLORES["secundario"], COLORES["acento"], COLORES["primario"]],
        title="Compras promedio por canal",
    )
    barras_canales.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    barras_canales.update_layout(showlegend=False)
    mostrar_figura(barras_canales)

with derecha:
    gasto_canal = px.box(
        filtrados,
        x="Dominant_Channel",
        y="Total_Spending",
        color="Dominant_Channel",
        points=False,
        title="Gasto por canal dominante",
        labels={"Dominant_Channel": "Canal", "Total_Spending": "Gasto total (MU)"},
    )
    gasto_canal.update_layout(showlegend=False)
    mostrar_figura(gasto_canal)

izquierda, derecha = st.columns(2)
with izquierda:
    dispersion_web = px.scatter(
        filtrados,
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
    mostrar_figura(dispersion_web, leyenda_horizontal=True)

with derecha:
    dispersion_catalogo = px.scatter(
        filtrados,
        x="NumCatalogPurchases",
        y="Total_Spending",
        color="Value_Segment",
        opacity=0.55,
        color_discrete_map={"Alto valor": COLORES["primario"], "Resto": "#AAB6BF"},
        title="Compras por catálogo y gasto total",
        labels={
            "NumCatalogPurchases": "Compras por catálogo",
            "Total_Spending": "Gasto total (MU)",
            "Value_Segment": "Valor",
        },
    )
    mostrar_figura(dispersion_catalogo, leyenda_horizontal=True)

izquierda, derecha = st.columns(2)
with izquierda:
    descuentos = (
        filtrados.groupby("Spending_Segment", observed=True)["NumDealsPurchases"]
        .mean()
        .rename("Compras con descuento")
        .reset_index()
    )
    figura_descuentos = px.bar(
        descuentos,
        x="Spending_Segment",
        y="Compras con descuento",
        text="Compras con descuento",
        color_discrete_sequence=[COLORES["acento"]],
        title="Uso de descuentos por segmento de gasto",
        labels={"Spending_Segment": "Segmento de gasto"},
    )
    figura_descuentos.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    mostrar_figura(figura_descuentos)

with derecha:
    orden_gasto = ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"]
    matriz = pd.crosstab(filtrados["Dominant_Channel"], filtrados["Spending_Segment"])
    matriz = matriz.reindex(columns=orden_gasto, fill_value=0)
    figura_matriz = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=matriz.columns,
            y=matriz.index,
            colorscale=[[0, "#F0F3F5"], [1, COLORES["primario"]]],
            text=matriz.values,
            texttemplate="%{text}",
            colorbar_title="Clientes",
        )
    )
    figura_matriz.update_layout(title="Canal dominante y segmento de gasto")
    mostrar_figura(figura_matriz)

razon_valida = filtrados["Web_Purchase_Visit_Ratio"].dropna()
st.caption(
    f"Razón mediana compras/visitas web: {razon_valida.median():.2f}. No es una tasa de "
    "conversión real: las compras cubren dos años y las visitas solo el último mes."
)
