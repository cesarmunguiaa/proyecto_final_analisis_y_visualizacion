import plotly.express as px
import streamlit as st

from pages.common import (
    COLORS,
    empty_guard,
    format_mu,
    load_data,
    multiselect_filter,
    page_header,
    range_filter,
    show_figure,
)


data = load_data()

page_header(
    "Perfil de clientes",
    "¿Quiénes conforman la base de clientes?",
    "Las variables sociodemográficas permiten contextualizar la cartera. Se muestran como "
    "descripciones de la base y no como explicaciones causales del valor comercial.",
)

st.sidebar.markdown("### Filtros de perfil")
filtered = range_filter(data, "Age", "Edad", "profile_age", integer=True)
filtered = multiselect_filter(filtered, "Education", "Nivel educativo", "profile_education")
filtered = multiselect_filter(
    filtered,
    "Marital_Status_Grouped",
    "Estado civil agrupado",
    "profile_marital",
)
filtered = range_filter(filtered, "Income", "Rango de ingreso (MU)", "profile_income")
filtered = range_filter(
    filtered,
    "Total_Dependents",
    "Número de dependientes",
    "profile_dependents",
    integer=True,
)
filtered = multiselect_filter(
    filtered, "Family_Segment", "Segmento familiar", "profile_family"
)
empty_guard(filtered)

metrics = st.columns(5)
metrics[0].metric("Clientes", f"{len(filtered):,}")
metrics[1].metric("Edad promedio", f"{filtered['Age'].mean():.1f} años")
metrics[2].metric("Edad mediana", f"{filtered['Age'].median():.0f} años")
metrics[3].metric("Ingreso promedio", format_mu(filtered["Income"].mean(), 0))
metrics[4].metric("Dependientes promedio", f"{filtered['Total_Dependents'].mean():.2f}")

left, right = st.columns([1.15, 1])
with left:
    age_fig = px.histogram(
        filtered,
        x="Age",
        nbins=24,
        color_discrete_sequence=[COLORS["primary"]],
        title="Distribución de edad histórica",
        labels={"Age": "Edad", "count": "Clientes"},
    )
    age_fig.update_layout(bargap=0.05)
    show_figure(age_fig)

with right:
    education_counts = (
        filtered["Education"].value_counts().rename_axis("Educación").reset_index(name="Clientes")
    )
    education_fig = px.bar(
        education_counts.sort_values("Clientes"),
        x="Clientes",
        y="Educación",
        orientation="h",
        text_auto=",",
        color_discrete_sequence=[COLORS["secondary"]],
        title="Composición por nivel educativo",
    )
    show_figure(education_fig)

left, right = st.columns(2)
with left:
    marital_counts = (
        filtered["Marital_Status_Grouped"]
        .value_counts()
        .rename_axis("Estado civil")
        .reset_index(name="Clientes")
    )
    marital_fig = px.bar(
        marital_counts,
        x="Estado civil",
        y="Clientes",
        text_auto=",",
        color="Estado civil",
        color_discrete_sequence=[COLORS["primary"], COLORS["secondary"], COLORS["accent"]],
        title="Estado civil reportado",
    )
    marital_fig.update_layout(showlegend=False)
    show_figure(marital_fig)

with right:
    dependent_counts = (
        filtered["Dependent_Composition"]
        .value_counts()
        .rename_axis("Composición")
        .reset_index(name="Clientes")
    )
    dependent_fig = px.pie(
        dependent_counts,
        names="Composición",
        values="Clientes",
        hole=0.58,
        color_discrete_sequence=["#7A243A", "#176B87", "#D18B47", "#769F8D"],
        title="Composición de dependientes",
    )
    dependent_fig.update_traces(textposition="inside", textinfo="percent")
    show_figure(dependent_fig, legend_horizontal=True)

st.subheader("Ingreso por grupos sociodemográficos")
left, right = st.columns(2)
with left:
    income_education = px.box(
        filtered,
        x="Education",
        y="Income",
        points=False,
        color_discrete_sequence=[COLORS["secondary"]],
        title="Ingreso por educación",
        labels={"Education": "Educación", "Income": "Ingreso (MU)"},
    )
    show_figure(income_education)

with right:
    income_family = px.box(
        filtered,
        x="Family_Segment",
        y="Income",
        points=False,
        color_discrete_sequence=[COLORS["primary"]],
        title="Ingreso por segmento familiar",
        labels={"Family_Segment": "Segmento familiar", "Income": "Ingreso (MU)"},
    )
    income_family.update_xaxes(tickangle=-15)
    show_figure(income_family)

st.caption(
    "La edad se calcula con respecto al 29 de junio de 2014, fecha máxima observada en "
    "Dt_Customer. Las categorías YOLO y Absurd se agrupan como ‘Otro / no válido’."
)
