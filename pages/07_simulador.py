import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import (
    COLORES,
    BANDERAS_ESTRATEGICAS,
    validar_no_vacio,
    resumen_financiero,
    formatear_mu,
    formatear_porcentaje,
    cargar_datos,
    filtro_multiseleccion,
    resumen_campana_original,
    encabezado_pagina,
    filtro_rango,
    mostrar_figura,
    mostrar_metricas,
    filtro_estrategico,
)


datos = cargar_datos()

encabezado_pagina(
    "Centro de decisiones y simulador",
    "¿Qué resultado histórico habría tenido una selección de clientes?",
    "Selecciona criterios disponibles antes de la campaña. El panel recalcula costo, ingreso y "
    "balance observados para comparar el grupo con el contacto masivo.",
)

st.sidebar.markdown("### Criterios de selección")
segmentos_seleccionados = st.sidebar.multiselect(
    "Segmento estratégico",
    list(BANDERAS_ESTRATEGICAS.keys()),
    key="simulador_segmentos",
)
seleccionados = filtro_multiseleccion(
    datos,
    "Income_Segment",
    "Nivel de ingreso",
    "simulador_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
seleccionados = filtro_multiseleccion(
    seleccionados,
    "Spending_Segment",
    "Nivel de gasto",
    "simulador_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
seleccionados = filtro_multiseleccion(
    seleccionados, "Dominant_Channel", "Canal dominante", "simulador_canal"
)
seleccionados = filtro_multiseleccion(
    seleccionados, "Dominant_Category", "Categoría dominante", "simulador_categoria"
)
seleccionados = filtro_rango(seleccionados, "Age", "Edad", "simulador_edad", entero=True)
seleccionados = filtro_multiseleccion(seleccionados, "Education", "Educación", "simulador_educacion")
seleccionados = filtro_multiseleccion(
    seleccionados, "Marital_Status_Grouped", "Estado civil", "simulador_estado_civil"
)
seleccionados = filtro_multiseleccion(
    seleccionados, "Family_Segment", "Segmento familiar", "simulador_familia"
)
seleccionados = filtro_multiseleccion(
    seleccionados,
    "Tenure_Group",
    "Antigüedad",
    "simulador_antiguedad",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
seleccionados = filtro_rango(
    seleccionados,
    "Recency",
    "Recencia",
    "simulador_recencia",
    entero=True,
)
seleccionados = filtro_rango(
    seleccionados,
    "NumDealsPurchases",
    "Compras con descuento",
    "simulador_descuentos",
    entero=True,
)
seleccionados = filtro_rango(
    seleccionados,
    "NumWebVisitsMonth",
    "Visitas web",
    "simulador_visitas",
    entero=True,
)
seleccionados = filtro_rango(
    seleccionados,
    "Accepted_Campaigns_Total",
    "Campañas anteriores aceptadas",
    "simulador_previas",
    entero=True,
)
queja = st.sidebar.selectbox(
    "Quejas",
    ["Todos", "Con queja", "Sin queja"],
    key="simulador_queja",
)
if queja == "Con queja":
    seleccionados = seleccionados[seleccionados["Complain"].eq(1)]
elif queja == "Sin queja":
    seleccionados = seleccionados[seleccionados["Complain"].eq(0)]
seleccionados = filtro_estrategico(seleccionados, segmentos_seleccionados)
validar_no_vacio(seleccionados)

masivo = resumen_campana_original(datos)
escenario = resumen_financiero(seleccionados)
categoria_principal = seleccionados["Dominant_Category"].mode().iat[0]
canal_principal = seleccionados["Dominant_Channel"].mode().iat[0]

mostrar_metricas(
    [
        {"titulo": "Clientes seleccionados", "valor": f"{escenario['clientes']:,}"},
        {"titulo": "Aceptaron", "valor": f"{escenario['aceptaron']:,}"},
        {
            "titulo": "Aceptación histórica",
            "valor": formatear_porcentaje(escenario["tasa_aceptacion"] * 100, 2),
        },
        {"titulo": "Costo estimado", "valor": formatear_mu(escenario["costo"])},
        {"titulo": "Ingreso histórico", "valor": formatear_mu(escenario["ingreso"])},
        {
            "titulo": "Balance histórico",
            "valor": formatear_mu(escenario["balance"]),
            "delta": formatear_mu(escenario["balance"] - masivo["balance"]),
        },
        {
            "titulo": "ROI histórico",
            "valor": formatear_porcentaje(escenario["roi"] * 100, 1),
        },
        {
            "titulo": "Gasto promedio",
            "valor": formatear_mu(seleccionados["Total_Spending"].mean(), 1),
        },
        {"titulo": "Categoría principal", "valor": categoria_principal},
        {"titulo": "Canal principal", "valor": canal_principal},
    ]
)

comparacion = pd.DataFrame(
    [
        {
            "Escenario": "Contacto masivo",
            "Costo": masivo["costo"],
            "Ingreso": masivo["ingreso"],
            "Balance": masivo["balance"],
        },
        {
            "Escenario": "Selección actual",
            "Costo": escenario["costo"],
            "Ingreso": escenario["ingreso"],
            "Balance": escenario["balance"],
        },
    ]
).melt(id_vars="Escenario", var_name="Concepto", value_name="MU")

izquierda, derecha = st.columns([1.15, 1])
with izquierda:
    figura_comparacion = px.bar(
        comparacion,
        x="Escenario",
        y="MU",
        color="Concepto",
        barmode="group",
        text="MU",
        color_discrete_map={
            "Costo": COLORES["negativo"],
            "Ingreso": COLORES["positivo"],
            "Balance": COLORES["primario"],
        },
        title="Contacto masivo frente a la selección",
    )
    figura_comparacion.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    mostrar_figura(figura_comparacion, altura=430, leyenda_horizontal=True)

with derecha:
    filas_agrupadas = []
    for segmento, subconjunto in seleccionados.groupby("Primary_Strategic_Segment"):
        finanzas_segmento = resumen_financiero(subconjunto)
        filas_agrupadas.append(
            {
                "Segmento": segmento,
                "Clientes": len(subconjunto),
                "Gasto promedio": subconjunto["Total_Spending"].mean(),
                "Aceptación (%)": subconjunto["Response"].mean() * 100,
                "Balance (MU)": finanzas_segmento["balance"],
                "Canal": subconjunto["Dominant_Channel"].mode().iat[0],
                "Categoría": subconjunto["Dominant_Category"].mode().iat[0],
            }
        )
    prioridad = pd.DataFrame(filas_agrupadas).sort_values(
        ["Balance (MU)", "Aceptación (%)"], ascending=False
    )
    st.markdown("#### Grupos priorizados")
    st.dataframe(
        prioridad,
        hide_index=True,
        width="stretch",
        column_config={
            "Gasto promedio": st.column_config.NumberColumn(format="%.1f MU"),
            "Aceptación (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Balance (MU)": st.column_config.NumberColumn(format="%.0f MU"),
        },
    )

cuadrante = px.scatter(
    prioridad,
    x="Aceptación (%)",
    y="Gasto promedio",
    size="Clientes",
    color="Balance (MU)",
    text="Segmento",
    color_continuous_scale=[[0, COLORES["negativo"]], [0.5, "#E9ECEF"], [1, COLORES["positivo"]]],
    color_continuous_midpoint=0,
    title="Matriz de priorización del escenario",
    labels={"Gasto promedio": "Gasto promedio (MU)"},
)
cuadrante.add_vline(x=seleccionados["Response"].mean() * 100, line_dash="dot")
cuadrante.add_hline(y=seleccionados["Total_Spending"].mean(), line_dash="dot")
cuadrante.update_traces(textposition="top center")
mostrar_figura(cuadrante, altura=450)

with st.expander("Ver clientes de la selección"):
    tabla_clientes = seleccionados[
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
    st.dataframe(tabla_clientes, hide_index=True, width="stretch", height=420)

st.warning(
    "Este simulador es retrospectivo: usa la respuesta observada para evaluar el grupo, pero no "
    "predice quién aceptará una campaña futura. Por esa razón, Response no se ofrece como filtro "
    "de selección; hacerlo introduciría fuga de información."
)
