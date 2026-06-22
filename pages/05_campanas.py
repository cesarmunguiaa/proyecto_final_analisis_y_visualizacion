import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLUMNAS_CAMPANAS,
    COLORES,
    validar_no_vacio,
    resumen_financiero,
    formatear_mu,
    formatear_porcentaje,
    cargar_datos,
    filtro_multiseleccion,
    encabezado_pagina,
    filtro_respuesta,
    mostrar_figura,
    mostrar_metricas,
)


datos = cargar_datos()

encabezado_pagina(
    "Respuesta histórica a campañas",
    "¿Qué tipo de clientes aceptaron campañas y qué tan rentable fue contactarlos?",
    "Esta vista compara respuestas históricas. Los resultados describen lo ocurrido en la muestra; "
    "no representan una predicción de respuesta futura.",
)

st.sidebar.markdown("### Filtros de campañas")
campanas_seleccionadas = st.sidebar.multiselect(
    "Campañas mostradas",
    list(COLUMNAS_CAMPANAS.values()),
    default=list(COLUMNAS_CAMPANAS.values()),
    key="campanas_mostradas",
)
filtrados = filtro_respuesta(datos, "campana_respuesta")
filtrados = filtro_multiseleccion(
    filtrados,
    "Spending_Segment",
    "Segmento de gasto",
    "campana_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Income_Segment",
    "Segmento de ingreso",
    "campana_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Channel", "Canal dominante", "campana_canal"
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Tenure_Group",
    "Segmento de antigüedad",
    "campana_antiguedad",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Category", "Categoría dominante", "campana_categoria"
)
queja = st.sidebar.selectbox(
    "Quejas",
    ["Todos", "Con queja", "Sin queja"],
    key="campana_queja",
)
if queja == "Con queja":
    filtrados = filtrados[filtrados["Complain"].eq(1)]
elif queja == "Sin queja":
    filtrados = filtrados[filtrados["Complain"].eq(0)]
validar_no_vacio(filtrados)

finanzas = resumen_financiero(filtrados)
mostrar_metricas(
    [
        {"titulo": "Clientes", "valor": f"{len(filtrados):,}"},
        {
            "titulo": "Aceptación última campaña",
            "valor": formatear_porcentaje(finanzas["tasa_aceptacion"] * 100, 2),
        },
        {"titulo": "Aceptaron última", "valor": f"{finanzas['aceptaron']:,}"},
        {
            "titulo": "Aceptaciones previas",
            "valor": f"{int(filtrados['Accepted_Campaigns_Total'].sum()):,}",
        },
        {"titulo": "Balance histórico", "valor": formatear_mu(finanzas["balance"])},
        {
            "titulo": "Quejas",
            "valor": formatear_porcentaje(filtrados["Complain"].mean() * 100, 2),
        },
    ]
)

filas_campanas = []
for columna, etiqueta in COLUMNAS_CAMPANAS.items():
    if etiqueta in campanas_seleccionadas:
        filas_campanas.append(
            {
                "Campaña": etiqueta,
                "Aceptaciones": int(filtrados[columna].sum()),
                "Tasa (%)": filtrados[columna].mean() * 100,
            }
        )
datos_campanas = pd.DataFrame(filas_campanas)
if not datos_campanas.empty:
    figura_campanas = px.bar(
        datos_campanas,
        x="Campaña",
        y="Tasa (%)",
        text="Tasa (%)",
        color="Campaña",
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="Tasa de aceptación por campaña",
    )
    figura_campanas.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    figura_campanas.update_layout(showlegend=False)
    mostrar_figura(figura_campanas)
else:
    st.info("Selecciona al menos una campaña para mostrar la comparación.")

def respuesta_por(columna: str, etiqueta: str):
    resultado = (
        filtrados.groupby(columna, observed=True)["Response"]
        .agg(Clientes="size", Aceptación="mean")
        .reset_index()
    )
    resultado["Aceptación (%)"] = resultado["Aceptación"] * 100
    figura = px.bar(
        resultado,
        x=columna,
        y="Aceptación (%)",
        text="Aceptación (%)",
        color=columna,
        title=f"Aceptación por {etiqueta}",
        labels={columna: etiqueta},
    )
    figura.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    figura.update_layout(showlegend=False)
    return figura


izquierda, centro, derecha = st.columns(3)
with izquierda:
    mostrar_figura(respuesta_por("Spending_Segment", "gasto"), altura=370)
with centro:
    mostrar_figura(respuesta_por("Income_Segment", "ingreso"), altura=370)
with derecha:
    mostrar_figura(respuesta_por("Dominant_Channel", "canal"), altura=370)

izquierda, derecha = st.columns(2)
with izquierda:
    datos_caja_respuesta = filtrados.assign(
        Respuesta=filtrados["Response"].map({0: "No aceptó", 1: "Aceptó"})
    )
    caja_respuesta = px.box(
        datos_caja_respuesta,
        x="Respuesta",
        y="Total_Spending",
        color="Respuesta",
        points=False,
        color_discrete_map={"Aceptó": COLORES["positivo"], "No aceptó": COLORES["atenuado"]},
        title="Gasto total según respuesta",
        labels={"Total_Spending": "Gasto total (MU)"},
    )
    caja_respuesta.update_layout(showlegend=False)
    mostrar_figura(caja_respuesta)

with derecha:
    filas_financieras = []
    for segmento, subconjunto in filtrados.groupby("Spending_Segment", observed=True):
        finanzas_segmento = resumen_financiero(subconjunto)
        filas_financieras.extend(
            [
                {"Segmento": segmento, "Concepto": "Costo", "MU": finanzas_segmento["costo"]},
                {"Segmento": segmento, "Concepto": "Ingreso", "MU": finanzas_segmento["ingreso"]},
                {"Segmento": segmento, "Concepto": "Balance", "MU": finanzas_segmento["balance"]},
            ]
        )
    datos_financieros = pd.DataFrame(filas_financieras)
    figura_finanzas = px.bar(
        datos_financieros,
        x="Segmento",
        y="MU",
        color="Concepto",
        barmode="group",
        color_discrete_map={
            "Costo": COLORES["negativo"],
            "Ingreso": COLORES["positivo"],
            "Balance": COLORES["primario"],
        },
        title="Costo, ingreso y balance por gasto",
    )
    mostrar_figura(figura_finanzas, leyenda_horizontal=True)

st.caption(
    "Costo = clientes contactados × 3 MU; ingreso = respuestas positivas × 11 MU. "
    "La comparación segmentada es retrospectiva y no controla por otras variables."
)
