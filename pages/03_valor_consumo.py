import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLORES,
    COLUMNAS_PRODUCTOS,
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
    "Valor y consumo por categorías",
    "¿Cuánto gastan los clientes y en qué productos se concentra el consumo?",
    "El gasto está distribuido de forma desigual. Esta vista distingue el valor total del cliente "
    "y la composición agregada del consumo, sin mezclar todavía el análisis de canales.",
)

st.sidebar.markdown("### Filtros de valor")
filtrados = filtro_multiseleccion(
    datos,
    "Income_Segment",
    "Segmento de ingreso",
    "valor_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Spending_Segment",
    "Segmento de gasto",
    "valor_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
categorias_seleccionadas = st.sidebar.multiselect(
    "Categorías mostradas",
    list(COLUMNAS_PRODUCTOS.values()),
    default=list(COLUMNAS_PRODUCTOS.values()),
    key="valor_categorias",
)
filtrados = filtro_rango(filtrados, "Age", "Edad", "valor_edad", entero=True)
filtrados = filtro_multiseleccion(filtrados, "Education", "Educación", "valor_educacion")
filtrados = filtro_multiseleccion(
    filtrados, "Family_Segment", "Segmento familiar", "valor_familia"
)
filtrados = filtro_respuesta(filtrados, "valor_respuesta")
validar_no_vacio(filtrados)

columnas_productos = [
    columna for columna, etiqueta in COLUMNAS_PRODUCTOS.items() if etiqueta in categorias_seleccionadas
]
if not columnas_productos:
    columnas_productos = list(COLUMNAS_PRODUCTOS.keys())

agregado = filtrados[list(COLUMNAS_PRODUCTOS.keys())].sum().sort_values(ascending=False)
categoria_dominante = COLUMNAS_PRODUCTOS[agregado.index[0]]
mostrar_metricas(
    [
        {
            "titulo": "Gasto promedio",
            "valor": formatear_mu(filtrados["Total_Spending"].mean(), 1),
        },
        {
            "titulo": "Gasto mediano",
            "valor": formatear_mu(filtrados["Total_Spending"].median(), 1),
        },
        {
            "titulo": "Gasto máximo",
            "valor": formatear_mu(filtrados["Total_Spending"].max(), 0),
        },
        {
            "titulo": "Clientes premium",
            "valor": formatear_porcentaje(
                filtrados["Value_Segment"].eq("Alto valor").mean() * 100,
                1,
            ),
        },
        {"titulo": "Categoría principal", "valor": categoria_dominante},
        {
            "titulo": "Gasto en vinos",
            "valor": formatear_mu(filtrados["MntWines"].mean(), 1),
        },
    ]
)

izquierda, derecha = st.columns(2)
with izquierda:
    histograma_gasto = px.histogram(
        filtrados,
        x="Total_Spending",
        nbins=35,
        color_discrete_sequence=[COLORES["primario"]],
        title="Distribución del gasto total",
        labels={"Total_Spending": "Gasto total (MU)", "count": "Clientes"},
    )
    mostrar_figura(histograma_gasto)

with derecha:
    gasto_ingreso = px.box(
        filtrados,
        x="Income_Segment",
        y="Total_Spending",
        category_orders={
            "Income_Segment": ["Ingreso bajo", "Ingreso medio", "Ingreso alto"]
        },
        points=False,
        color="Income_Segment",
        color_discrete_sequence=["#A9C4D0", "#4F8CA5", COLORES["primario"]],
        title="Gasto por segmento de ingreso",
        labels={"Income_Segment": "Ingreso", "Total_Spending": "Gasto total (MU)"},
    )
    gasto_ingreso.update_layout(showlegend=False)
    mostrar_figura(gasto_ingreso)

estadisticas_categorias = pd.DataFrame(
    {
        "Categoría": [COLUMNAS_PRODUCTOS[columna] for columna in columnas_productos],
        "Gasto promedio": [filtrados[columna].mean() for columna in columnas_productos],
        "Gasto total": [filtrados[columna].sum() for columna in columnas_productos],
    }
).sort_values("Gasto total", ascending=False)
estadisticas_categorias["Participación"] = estadisticas_categorias["Gasto total"] / estadisticas_categorias["Gasto total"].sum()

izquierda, derecha = st.columns(2)
with izquierda:
    figura_promedios = px.bar(
        estadisticas_categorias.sort_values("Gasto promedio"),
        x="Gasto promedio",
        y="Categoría",
        orientation="h",
        text="Gasto promedio",
        color_discrete_sequence=[COLORES["secundario"]],
        title="Gasto promedio por categoría",
    )
    figura_promedios.update_traces(texttemplate="%{text:,.1f} MU", textposition="outside")
    mostrar_figura(figura_promedios)

with derecha:
    figura_composicion = px.pie(
        estadisticas_categorias,
        names="Categoría",
        values="Gasto total",
        hole=0.55,
        color_discrete_sequence=["#7A243A", "#176B87", "#D18B47", "#769F8D", "#A386B5", "#C6A15B"],
        title="Composición agregada del gasto",
    )
    figura_composicion.update_traces(textinfo="percent+label", textposition="inside")
    mostrar_figura(figura_composicion)

productos_largos = filtrados[columnas_productos].rename(columns=COLUMNAS_PRODUCTOS).melt(
    var_name="Categoría", value_name="Gasto"
)
izquierda, derecha = st.columns([1.45, 1])
with izquierda:
    caja_categorias = px.box(
        productos_largos,
        x="Categoría",
        y="Gasto",
        points=False,
        color_discrete_sequence=[COLORES["acento"]],
        title="Dispersión del gasto por categoría",
        labels={"Gasto": "Gasto (MU)"},
    )
    mostrar_figura(caja_categorias)

with derecha:
    st.markdown("#### Ranking comercial")
    clasificacion = estadisticas_categorias[["Categoría", "Gasto total", "Participación"]].copy()
    clasificacion["Gasto total"] = clasificacion["Gasto total"].round(0)
    clasificacion["Participación"] = (clasificacion["Participación"] * 100).round(2)
    st.dataframe(
        clasificacion,
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
