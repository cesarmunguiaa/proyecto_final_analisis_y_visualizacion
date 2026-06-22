import plotly.express as px
import streamlit as st

from pages.common import (
    COLORES,
    validar_no_vacio,
    formatear_mu,
    cargar_datos,
    filtro_multiseleccion,
    encabezado_pagina,
    filtro_rango,
    mostrar_figura,
    mostrar_metricas,
)


datos = cargar_datos()

encabezado_pagina(
    "Perfil de clientes",
    "¿Quiénes conforman la base de clientes?",
    "Las variables sociodemográficas permiten contextualizar la cartera. Se muestran como "
    "descripciones de la base y no como explicaciones causales del valor comercial.",
)

st.sidebar.markdown("### Filtros de perfil")
filtrados = filtro_rango(datos, "Age", "Edad", "perfil_edad", entero=True)
filtrados = filtro_multiseleccion(filtrados, "Education", "Nivel educativo", "perfil_educacion")
filtrados = filtro_multiseleccion(
    filtrados,
    "Marital_Status_Grouped",
    "Estado civil agrupado",
    "perfil_estado_civil",
)
filtrados = filtro_rango(filtrados, "Income", "Rango de ingreso (MU)", "perfil_ingreso")
filtrados = filtro_rango(
    filtrados,
    "Total_Dependents",
    "Número de dependientes",
    "perfil_dependientes",
    entero=True,
)
filtrados = filtro_multiseleccion(
    filtrados, "Family_Segment", "Segmento familiar", "perfil_familia"
)
validar_no_vacio(filtrados)

mostrar_metricas(
    [
        {"titulo": "Clientes", "valor": f"{len(filtrados):,}"},
        {"titulo": "Edad promedio", "valor": f"{filtrados['Age'].mean():.1f} años"},
        {"titulo": "Edad mediana", "valor": f"{filtrados['Age'].median():.0f} años"},
        {
            "titulo": "Ingreso promedio",
            "valor": formatear_mu(filtrados["Income"].mean(), 0),
        },
        {
            "titulo": "Dependientes promedio",
            "valor": f"{filtrados['Total_Dependents'].mean():.2f}",
        },
    ]
)

izquierda, derecha = st.columns([1.15, 1])
with izquierda:
    figura_edades = px.histogram(
        filtrados,
        x="Age",
        nbins=24,
        color_discrete_sequence=[COLORES["primario"]],
        title="Distribución de edad histórica",
        labels={"Age": "Edad", "count": "Clientes"},
    )
    figura_edades.update_layout(bargap=0.05)
    mostrar_figura(figura_edades)

with derecha:
    conteo_educacion = (
        filtrados["Education"].value_counts().rename_axis("Educación").reset_index(name="Clientes")
    )
    figura_educacion = px.bar(
        conteo_educacion.sort_values("Clientes"),
        x="Clientes",
        y="Educación",
        orientation="h",
        text_auto=",",
        color_discrete_sequence=[COLORES["secundario"]],
        title="Composición por nivel educativo",
    )
    mostrar_figura(figura_educacion)

izquierda, derecha = st.columns(2)
with izquierda:
    conteo_estado_civil = (
        filtrados["Marital_Status_Grouped"]
        .value_counts()
        .rename_axis("Estado civil")
        .reset_index(name="Clientes")
    )
    figura_estado_civil = px.bar(
        conteo_estado_civil,
        x="Estado civil",
        y="Clientes",
        text_auto=",",
        color="Estado civil",
        color_discrete_sequence=[COLORES["primario"], COLORES["secundario"], COLORES["acento"]],
        title="Estado civil reportado",
    )
    figura_estado_civil.update_layout(showlegend=False)
    mostrar_figura(figura_estado_civil)

with derecha:
    conteo_dependientes = (
        filtrados["Dependent_Composition"]
        .value_counts()
        .rename_axis("Composición")
        .reset_index(name="Clientes")
    )
    figura_dependientes = px.pie(
        conteo_dependientes,
        names="Composición",
        values="Clientes",
        hole=0.58,
        color_discrete_sequence=["#7A243A", "#176B87", "#D18B47", "#769F8D"],
        title="Composición de dependientes",
    )
    figura_dependientes.update_traces(textposition="inside", textinfo="percent")
    mostrar_figura(figura_dependientes, leyenda_horizontal=True)

st.subheader("Ingreso por grupos sociodemográficos")
izquierda, derecha = st.columns(2)
with izquierda:
    ingreso_educacion = px.box(
        filtrados,
        x="Education",
        y="Income",
        points=False,
        color_discrete_sequence=[COLORES["secundario"]],
        title="Ingreso por educación",
        labels={"Education": "Educación", "Income": "Ingreso (MU)"},
    )
    mostrar_figura(ingreso_educacion)

with derecha:
    ingreso_familia = px.box(
        filtrados,
        x="Family_Segment",
        y="Income",
        points=False,
        color_discrete_sequence=[COLORES["primario"]],
        title="Ingreso por segmento familiar",
        labels={"Family_Segment": "Segmento familiar", "Income": "Ingreso (MU)"},
    )
    ingreso_familia.update_xaxes(tickangle=-15)
    mostrar_figura(ingreso_familia)

st.caption(
    "La edad se calcula con respecto al 29 de junio de 2014, fecha máxima observada en "
    "Dt_Customer. Las categorías YOLO y Absurd se agrupan como ‘Otro / no válido’."
)
