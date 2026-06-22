import streamlit as st

from pages.common import inject_css


st.set_page_config(
    page_title="iFood | Analítica de clientes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

st.sidebar.markdown("## iFood Analytics")
st.sidebar.caption("Análisis histórico · montos en MU")

navegacion = st.navigation(
    [
        st.Page(
            "pages/01_resumen_ejecutivo.py",
            title="Resumen ejecutivo",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "pages/02_perfil_clientes.py",
            title="Perfil de clientes",
            icon=":material/groups:",
        ),
        st.Page(
            "pages/03_valor_consumo.py",
            title="Valor y consumo",
            icon=":material/payments:",
        ),
        st.Page(
            "pages/04_canales.py",
            title="Canales de compra",
            icon=":material/storefront:",
        ),
        st.Page(
            "pages/05_campanas.py",
            title="Campañas",
            icon=":material/campaign:",
        ),
        st.Page(
            "pages/06_segmentos.py",
            title="Segmentos estratégicos",
            icon=":material/category:",
        ),
        st.Page(
            "pages/07_simulador.py",
            title="Centro de decisiones",
            icon=":material/tune:",
        ),
    ]
)

navegacion.run()
