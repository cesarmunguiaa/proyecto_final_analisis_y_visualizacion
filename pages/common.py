from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


RAIZ = Path(__file__).resolve().parents[1]
RUTA_DATOS = RAIZ / "data" / "ifood_dashboard.csv"

COLORES = {
    "primario": "#7A243A",
    "secundario": "#176B87",
    "acento": "#D18B47",
    "positivo": "#287D5A",
    "negativo": "#B23A48",
    "atenuado": "#708090",
    "claro": "#EEF2F5",
}

COLUMNAS_PRODUCTOS = OrderedDict(
    [
        ("MntWines", "Vinos"),
        ("MntMeatProducts", "Carnes"),
        ("MntFruits", "Frutas"),
        ("MntFishProducts", "Pescado"),
        ("MntSweetProducts", "Dulces"),
        ("MntGoldProds", "Gold"),
    ]
)

COLUMNAS_CANALES = OrderedDict(
    [
        ("NumWebPurchases", "Web"),
        ("NumCatalogPurchases", "Catálogo"),
        ("NumStorePurchases", "Tienda"),
    ]
)

COLUMNAS_CAMPANAS = OrderedDict(
    [
        ("AcceptedCmp1", "Campaña 1"),
        ("AcceptedCmp2", "Campaña 2"),
        ("AcceptedCmp3", "Campaña 3"),
        ("AcceptedCmp4", "Campaña 4"),
        ("AcceptedCmp5", "Campaña 5"),
        ("Response", "Última campaña"),
    ]
)

BANDERAS_ESTRATEGICAS = OrderedDict(
    [
        ("Nuevo de alto valor", "Is_Early_High_Value"),
        ("Premium", "Is_Premium"),
        ("Alto ingreso, bajo gasto", "Is_High_Income_Low_Spending"),
        ("Web curioso", "Is_Web_Curious"),
        ("Inactivo o frío", "Is_Cold"),
        ("Leal", "Is_Loyal"),
        ("Sensible a descuentos", "Is_Discount_Sensitive"),
        ("Multicanal", "Is_Multichannel"),
    ]
)


@st.cache_data(show_spinner=False)
def cargar_datos() -> pd.DataFrame:
    if not RUTA_DATOS.exists():
        raise FileNotFoundError(
            "No existe data/ifood_dashboard.csv. Ejecuta primero notebooks/Analitica.ipynb."
        )
    datos = pd.read_csv(RUTA_DATOS, parse_dates=["Dt_Customer"])
    requeridas = {
        "Income_Segment",
        "Spending_Segment",
        "Dominant_Channel",
        "Dominant_Category",
        "Primary_Strategic_Segment",
        "PCA_PC1",
        "PCA_PC2",
        "Campaign_Total_Contacts",
        "Campaign_Total_Accepted",
    }
    faltantes = sorted(requeridas.difference(datos.columns))
    if faltantes:
        raise ValueError(
            "El archivo del dashboard está desactualizado. Faltan: " + ", ".join(faltantes)
        )
    return datos


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{ --primary: {COLORES['primario']}; --secondary: {COLORES['secundario']}; }}
        .stApp {{ background: #F7F8FA; }}
        .block-container {{ max-width: 1480px; padding-top: 1.8rem; padding-bottom: 3rem; }}
        h1, h1 a {{ color: #1F2933 !important; letter-spacing: -0.03em; }}
        h2, h3 {{ color: #293845; }}
        [data-testid="stMetric"] {{
            min-height: 145px;
            background: #FFFFFF;
            border: 1px solid #E3E8EC;
            border-radius: 12px;
            padding: 1.15rem 1.3rem;
            box-shadow: 0 3px 12px rgba(27, 39, 51, 0.04);
        }}
        [data-testid="stMetricLabel"] {{ color: #5D6B78; }}
        [data-testid="stMetricLabel"] p {{
            font-size: 1rem;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
        }}
        [data-testid="stMetricValue"] {{
            color: #2E3440 !important;
            font-size: 2.35rem;
        }}
        [data-testid="stSidebar"] {{ border-right: 1px solid #E4E8EC; }}
        .caja-historia {{
            background: #FFFFFF;
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 0.9rem 1.1rem;
            margin: 0.2rem 0 1.2rem 0;
            color: #35414B;
        }}
        .nota-pequena {{ color: #667784; font-size: 0.88rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def encabezado_pagina(titulo: str, pregunta: str, historia: str) -> None:
    st.title(titulo)
    st.caption(pregunta)
    st.markdown(f'<div class="caja-historia">{historia}</div>', unsafe_allow_html=True)


def formatear_mu(valor: float, decimales: int = 0) -> str:
    if pd.isna(valor):
        return "—"
    return f"{valor:,.{decimales}f} MU"


def formatear_porcentaje(valor: float, decimales: int = 1) -> str:
    if pd.isna(valor):
        return "—"
    return f"{valor:.{decimales}f}%"


def mostrar_metricas(metricas: list[dict], por_fila: int = 3) -> None:
    for inicio in range(0, len(metricas), por_fila):
        columnas = st.columns(por_fila)
        for columna, metrica in zip(columnas, metricas[inicio : inicio + por_fila]):
            columna.metric(
                metrica["titulo"],
                metrica["valor"],
                delta=metrica.get("delta"),
                delta_color=metrica.get("color_delta", "normal"),
                help=metrica.get("ayuda"),
            )


def resumen_financiero(datos: pd.DataFrame) -> dict[str, float]:
    clientes = len(datos)
    aceptaron = int(datos["Response"].sum()) if clientes else 0
    costo_contacto = float(datos["Z_CostContact"].iloc[0]) if clientes else 3.0
    ingreso_respuesta = float(datos["Z_Revenue"].iloc[0]) if clientes else 11.0
    costo = clientes * costo_contacto
    ingreso = aceptaron * ingreso_respuesta
    balance = ingreso - costo
    return {
        "clientes": clientes,
        "aceptaron": aceptaron,
        "tasa_aceptacion": aceptaron / clientes if clientes else np.nan,
        "costo": costo,
        "ingreso": ingreso,
        "balance": balance,
        "roi": balance / costo if costo else np.nan,
    }


def resumen_campana_original(datos: pd.DataFrame) -> dict[str, float]:
    contactos = int(datos["Campaign_Total_Contacts"].iloc[0])
    aceptaron = int(datos["Campaign_Total_Accepted"].iloc[0])
    costo_contacto = float(datos["Z_CostContact"].iloc[0])
    ingreso_respuesta = float(datos["Z_Revenue"].iloc[0])
    costo = contactos * costo_contacto
    ingreso = aceptaron * ingreso_respuesta
    balance = ingreso - costo
    return {
        "clientes": contactos,
        "aceptaron": aceptaron,
        "tasa_aceptacion": aceptaron / contactos,
        "costo": costo,
        "ingreso": ingreso,
        "balance": balance,
        "roi": balance / costo,
    }


def estilizar_figura(figura, altura: int = 390, leyenda_horizontal: bool = False):
    figura.update_layout(
        template="plotly_white",
        height=altura,
        margin=dict(l=20, r=20, t=55, b=30),
        font=dict(family="Arial", color="#33414C"),
        title_font=dict(size=17),
        hoverlabel=dict(bgcolor="white"),
    )
    if leyenda_horizontal:
        figura.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    return figura


def mostrar_figura(figura, altura: int = 390, leyenda_horizontal: bool = False) -> None:
    st.plotly_chart(
        estilizar_figura(
            figura,
            altura=altura,
            leyenda_horizontal=leyenda_horizontal,
        ),
        width="stretch",
        config={"displayModeBar": False},
    )


def filtro_multiseleccion(
    datos: pd.DataFrame,
    columna: str,
    etiqueta: str,
    clave: str,
    opciones: list | None = None,
) -> pd.DataFrame:
    disponibles = opciones or sorted(datos[columna].dropna().unique().tolist())
    seleccionados = st.sidebar.multiselect(etiqueta, disponibles, key=clave)
    return datos[datos[columna].isin(seleccionados)] if seleccionados else datos


def filtro_rango(
    datos: pd.DataFrame,
    columna: str,
    etiqueta: str,
    clave: str,
    entero: bool = False,
) -> pd.DataFrame:
    serie = datos[columna].dropna()
    if serie.empty:
        return datos
    minimo = int(serie.min()) if entero else float(serie.min())
    maximo = int(serie.max()) if entero else float(serie.max())
    if minimo == maximo:
        st.sidebar.caption(f"{etiqueta}: {minimo}")
        return datos
    paso = 1 if entero else max((maximo - minimo) / 100, 1.0)
    seleccion = st.sidebar.slider(
        etiqueta,
        min_value=minimo,
        max_value=maximo,
        value=(minimo, maximo),
        step=paso,
        key=clave,
    )
    return datos[datos[columna].between(seleccion[0], seleccion[1])]


def filtro_respuesta(datos: pd.DataFrame, clave: str) -> pd.DataFrame:
    seleccion = st.sidebar.selectbox(
        "Respuesta a la última campaña",
        ["Todos", "Aceptó", "No aceptó"],
        key=clave,
    )
    if seleccion == "Aceptó":
        return datos[datos["Response"].eq(1)]
    if seleccion == "No aceptó":
        return datos[datos["Response"].eq(0)]
    return datos


def filtro_estrategico(datos: pd.DataFrame, seleccionados: list[str]) -> pd.DataFrame:
    if not seleccionados:
        return datos
    mascara = pd.Series(False, index=datos.index)
    for segmento in seleccionados:
        mascara |= datos[BANDERAS_ESTRATEGICAS[segmento]].astype(bool)
    return datos[mascara]


def resumen_estrategico(datos: pd.DataFrame) -> pd.DataFrame:
    filas: list[dict] = []
    for segmento, bandera in BANDERAS_ESTRATEGICAS.items():
        subconjunto = datos[datos[bandera].astype(bool)]
        if subconjunto.empty:
            continue
        finanzas = resumen_financiero(subconjunto)
        filas.append(
            {
                "Segmento": segmento,
                "Clientes": len(subconjunto),
                "Gasto promedio": subconjunto["Total_Spending"].mean(),
                "Gasto mediano": subconjunto["Total_Spending"].median(),
                "Aceptación (%)": subconjunto["Response"].mean() * 100,
                "Balance (MU)": finanzas["balance"],
                "Canal principal": subconjunto["Dominant_Channel"].mode().iat[0],
                "Categoría principal": subconjunto["Dominant_Category"].mode().iat[0],
                "Antigüedad promedio": subconjunto["Customer_Tenure_Days"].mean(),
                "Recencia promedio": subconjunto["Recency"].mean(),
            }
        )
    return pd.DataFrame(filas)


def validar_no_vacio(datos: pd.DataFrame) -> None:
    if datos.empty:
        st.warning("No hay clientes que cumplan la combinación actual de filtros.")
        st.stop()


def grafica_resultado_financiero(
    datos: pd.DataFrame,
    titulo: str,
    resumen: dict[str, float] | None = None,
):
    finanzas = resumen or resumen_financiero(datos)
    conceptos = ["Costo", "Ingreso", "Balance"]
    valores = [-finanzas["costo"], finanzas["ingreso"], finanzas["balance"]]
    colores = [COLORES["negativo"], COLORES["positivo"], COLORES["primario"]]
    figura = go.Figure(
        go.Bar(
            x=conceptos,
            y=valores,
            marker_color=colores,
            text=[formatear_mu(valor) for valor in valores],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}: %{y:,.0f} MU<extra></extra>",
        )
    )
    limite = max(abs(valor) for valor in valores) * 1.18
    figura.update_layout(
        title=titulo,
        yaxis_title="MU",
        showlegend=False,
        yaxis_range=[-limite, limite],
        yaxis_tickformat=",",
    )
    figura.add_hline(y=0, line_color="#8795A1", line_width=1)
    return figura
