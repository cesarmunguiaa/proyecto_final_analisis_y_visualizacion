# Análisis iFood

Proyecto de análisis exploratorio y dashboard interactivo del caso iFood CRM.

El notebook es la fuente de verdad: limpia `data/ifood.csv`, crea las variables analíticas y exporta `data/ifood_dashboard.csv`. Streamlit solo filtra, agrega y presenta ese resultado.

## Estructura

```text
proyecto_final/
├── app.py
├── pages/
│   ├── common.py
│   ├── 01_resumen_ejecutivo.py
│   ├── 02_perfil_clientes.py
│   ├── 03_valor_consumo.py
│   ├── 04_canales.py
│   ├── 05_campanas.py
│   ├── 06_segmentos.py
│   └── 07_simulador.py
├── data/
│   ├── ifood.csv
│   └── ifood_dashboard.csv
├── notebooks/
│   └── Analitica.ipynb
├── reporte_ifood_sin_modelo_predictivo.tex
├── DASHBOARD.md
├── requirements.txt
└── README.md
```

## Ejecución

1. Instalar las dependencias:

```powershell
pip install -r requirements.txt
```

2. Ejecutar todas las celdas de `notebooks/Analitica.ipynb` para regenerar el archivo analítico.
3. Iniciar el dashboard desde la raíz del proyecto:

```powershell
streamlit run app.py
```

No se utiliza archivo `.env`. El dashboard no necesita credenciales ni servicios externos.

## Datos y alcance

- `data/ifood.csv`: copia local del dataset original `ml_project1_data`; no debe editarse manualmente.
- `data/ifood_dashboard.csv`: resultado derivado por el notebook.
- Los montos se muestran en MU, porque la divisa no está documentada.
- Los resultados de campañas y del simulador son retrospectivos; no constituyen predicciones.

Las nuevas variables y sus reglas están documentadas en [DASHBOARD.md](DASHBOARD.md).
