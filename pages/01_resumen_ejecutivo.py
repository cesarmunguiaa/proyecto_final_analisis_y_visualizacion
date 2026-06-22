import plotly.express as px
import streamlit as st

from pages.common import (
    COLORES,
    validar_no_vacio,
    resumen_financiero,
    grafica_resultado_financiero,
    formatear_mu,
    formatear_porcentaje,
    cargar_datos,
    filtro_multiseleccion,
    resumen_campana_original,
    encabezado_pagina,
    filtro_respuesta,
    mostrar_figura,
    mostrar_metricas,
    resumen_estrategico,
)


datos = cargar_datos()

encabezado_pagina(
    "Resumen ejecutivo",
    "¿Cuál es el problema comercial?",
    "La campaña masiva tuvo un balance histórico negativo. El objetivo del dashboard es "
    "identificar grupos con mayor valor y mejor respuesta para evaluar una selección más eficiente.",
)

st.sidebar.markdown("### Filtros del resumen")
filtrados = filtro_multiseleccion(
    datos,
    "Spending_Segment",
    "Segmento de gasto",
    "resumen_gasto",
    ["Gasto bajo", "Gasto medio-bajo", "Gasto medio-alto", "Gasto alto"],
)
filtrados = filtro_multiseleccion(
    filtrados,
    "Income_Segment",
    "Segmento de ingreso",
    "resumen_ingreso",
    ["Ingreso bajo", "Ingreso medio", "Ingreso alto"],
)
filtrados = filtro_multiseleccion(
    filtrados, "Dominant_Channel", "Canal dominante", "resumen_canal"
)
filtrados = filtro_respuesta(filtrados, "resumen_respuesta")
filtrados = filtro_multiseleccion(
    filtrados,
    "Tenure_Group",
    "Segmento de antigüedad",
    "resumen_antiguedad",
    ["Nuevo", "Reciente", "Estable", "Leal"],
)
validar_no_vacio(filtrados)

es_muestra_completa = filtrados.index.equals(datos.index)
finanzas = resumen_campana_original(datos) if es_muestra_completa else resumen_financiero(filtrados)
mostrar_metricas(
    [
        {"titulo": "Clientes analizados", "valor": f"{len(filtrados):,}"},
        {"titulo": "Contactos evaluados", "valor": f"{finanzas['clientes']:,}"},
        {
            "titulo": "Gasto promedio",
            "valor": formatear_mu(filtrados["Total_Spending"].mean(), 1),
        },
        {
            "titulo": "Gasto mediano",
            "valor": formatear_mu(filtrados["Total_Spending"].median(), 1),
        },
        {
            "titulo": "Tasa de aceptación",
            "valor": formatear_porcentaje(finanzas["tasa_aceptacion"] * 100, 2),
        },
        {"titulo": "Aceptaron", "valor": f"{finanzas['aceptaron']:,}"},
        {"titulo": "Costo histórico", "valor": formatear_mu(finanzas["costo"])},
        {"titulo": "Ingreso histórico", "valor": formatear_mu(finanzas["ingreso"])},
        {
            "titulo": "Balance / ROI",
            "valor": formatear_mu(finanzas["balance"]),
            "delta": formatear_porcentaje(finanzas["roi"] * 100, 1),
            "color_delta": "normal" if finanzas["roi"] >= 0 else "inverse",
        },
        {
            "titulo": "Muestra excluida",
            "valor": f"{finanzas['clientes'] - len(filtrados):,}",
        },
    ]
)

st.caption(
    "Sin filtros, las finanzas corresponden a los 2,240 contactos originales; el gasto y los "
    "segmentos usan los 2,237 registros válidos. Al filtrar, las finanzas se recalculan sobre "
    "la selección visible."
)

izquierda, derecha = st.columns(2)
with izquierda:
    conteo_respuestas = (
        filtrados["Response"]
        .map({0: "No aceptó", 1: "Aceptó"})
        .value_counts()
        .rename_axis("Respuesta")
        .reset_index(name="Clientes")
    )
    figura_respuestas = px.bar(
        conteo_respuestas,
        x="Respuesta",
        y="Clientes",
        color="Respuesta",
        category_orders={"Respuesta": ["No aceptó", "Aceptó"]},
        color_discrete_map={"Aceptó": COLORES["positivo"], "No aceptó": COLORES["atenuado"]},
        title="Respuesta a la última campaña",
        labels={"Clientes": "Número de clientes"},
    )
    figura_respuestas.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: %{y:,.0f} clientes<extra></extra>",
    )
    figura_respuestas.update_layout(
        showlegend=False,
        yaxis_rangemode="tozero",
        yaxis_tickformat=",",
    )
    mostrar_figura(figura_respuestas)

with derecha:
    mostrar_figura(
        grafica_resultado_financiero(
            filtrados,
            "Resultado histórico del contacto",
            finanzas,
        )
    )

st.subheader("Segmentos con mayor gasto promedio")
clasificacion = resumen_estrategico(filtrados).sort_values("Gasto promedio", ascending=False).head(5)
figura_clasificacion = px.bar(
    clasificacion.sort_values("Gasto promedio"),
    x="Gasto promedio",
    y="Segmento",
    orientation="h",
    text="Gasto promedio",
    color="Aceptación (%)",
    color_continuous_scale=[[0, "#DCE5EA"], [1, COLORES["primario"]]],
    title="Valor promedio y aceptación histórica",
)
figura_clasificacion.update_traces(texttemplate="%{text:,.0f} MU", textposition="outside")
figura_clasificacion.update_layout(coloraxis_colorbar_title="Aceptación %")
mostrar_figura(figura_clasificacion, altura=360)
st.caption(
    "Los segmentos estratégicos son cohortes descriptivas y pueden solaparse; un cliente puede "
    "pertenecer a más de una."
)
