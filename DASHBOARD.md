# Dashboard de analítica iFood

## Arquitectura

El notebook `notebooks/Analitica.ipynb` concentra la limpieza y la ingeniería de variables. Al ejecutarse, exporta `data/ifood_dashboard.csv`. La aplicación de Streamlit no vuelve a limpiar ni redefine clientes; únicamente aplica filtros, agregaciones y fórmulas financieras sobre el archivo exportado.

## Variables añadidas para el dashboard

| Variable | Regla | Uso |
|---|---|---|
| `Income_Segment` | Terciles de `Income`: ingreso bajo, medio y alto. En la ejecución actual los cortes son aproximadamente 40,493 y 62,846.33 MU. | Filtros y comparación de capacidad económica. |
| `Spending_Segment` | Cuartiles de `Total_Spending`: bajo, medio-bajo, medio-alto y alto. Cortes actuales: 69, 396 y 1,045 MU. | Filtros y análisis de valor. |
| `Dependent_Composition` | Sin dependientes, con niños, con adolescentes o con ambos, a partir de `Kidhome` y `Teenhome`. | Perfil familiar. |
| `Marital_Status_Grouped` | `Married`/`Together` se agrupan como en pareja; `Single`/`Divorced`/`Widow`/`Alone` como sin pareja reportada; otros valores como no válidos. | Evita presentar categorías anómalas como estados civiles normales. |
| `Dominant_Channel` | Canal con mayor número de compras entre web, catálogo y tienda. Los máximos empatados se etiquetan como `Empate` y los clientes sin compras como `Sin compras`. | Comparación del canal principal. |
| `Channel_Segment` | Cero canales activos: sin compras; uno: monocanal; dos o tres: multicanal. | Medición del perfil multicanal. |
| `Dominant_Category` | Categoría con mayor gasto individual. Los máximos empatados se etiquetan como `Mixta`. | Afinidad de producto. |
| `Web_Purchase_Visit_Ratio` | Compras web divididas entre visitas web; queda ausente cuando las visitas son cero. | Indicador exploratorio de interacción digital. No es conversión real porque los periodos de ambas variables no coinciden. |
| `PCA_PC1`, `PCA_PC2` | Coordenadas del PCA ya calculado en el notebook. | Visualización exploratoria en la página de segmentos. |
| `Campaign_Total_Contacts`, `Campaign_Total_Accepted` | Metadatos constantes de la campaña original: 2,240 contactos y 334 respuestas. | Mantienen el resumen financiero original separado de los 2,237 registros válidos del EDA. |

## Segmentos estratégicos

Los segmentos son grupos de clientes que pueden solaparse. Las columnas booleanas permiten medir cada grupo sin obligar a que un cliente pertenezca a una sola clase.

| Etiqueta | Columna | Definición actual |
|---|---|---|
| Premium | `Is_Premium` | `Total_Spending` igual o superior al percentil 90: 1,536 MU. |
| Alto ingreso, bajo gasto | `Is_High_Income_Low_Spending` | Tercil alto de ingreso y gasto no superior a la mediana: 396 MU. |
| Multicanal | `Is_Multichannel` | Compras positivas en al menos dos canales. |
| Web curioso | `Is_Web_Curious` | Al menos 7 visitas web y como máximo 2 compras web. |
| Sensible a descuentos | `Is_Discount_Sensitive` | Al menos 3 compras con descuento, correspondiente al percentil 75 actual. |
| Leal | `Is_Loyal` | Cuartil `Leal` de antigüedad. |
| Nuevo de alto valor | `Is_Early_High_Value` | Mitad más reciente (`Nuevo` o `Reciente`) y gasto desde el percentil 95: 1,767.2 MU. |
| Inactivo o frío | `Is_Cold` | `Recency` de al menos 74 días, percentil 75 actual. |

`Strategic_Tags` concatena todos los segmentos estratégicos de cada cliente. `Primary_Strategic_Segment` asigna una sola etiqueta únicamente para colorear el PCA y construir tablas sin duplicados. Su prioridad es: nuevo de alto valor, premium, alto ingreso/bajo gasto, web curioso, inactivo, leal, sensible a descuentos, multicanal y base general. Las comparaciones analíticas de la página 6 usan las banderas solapadas, no esta etiqueta primaria.

## Cálculos dinámicos

No se almacenan como nuevas columnas porque dependen de los filtros activos:

- Costo: clientes seleccionados × 3 MU.
- Ingreso histórico: respuestas positivas × 11 MU.
- Balance: ingreso − costo.
- ROI histórico: balance / costo.
- Participación de producto: suma de la categoría / suma total del gasto de las categorías visibles.
- Canal o categoría principal de un grupo: moda dentro del conjunto filtrado.

Sin filtros, el resumen ejecutivo y la comparación masiva usan los 2,240 contactos originales. Los indicadores de gasto y segmentación usan la muestra limpia de 2,237 clientes. Cuando se aplican filtros, el costo y el ingreso se recalculan sobre los clientes válidos de la selección.

## Páginas

1. Resumen ejecutivo.
2. Perfil de clientes.
3. Valor y consumo por categorías.
4. Canales y comportamiento de compra.
5. Respuesta histórica a campañas.
6. Segmentos estratégicos.
7. Centro de decisiones y simulador.

## Limitaciones de interpretación

- El simulador reconstruye lo que habría ocurrido históricamente en el subconjunto; no predice una campaña futura.
- `Response` no se ofrece como criterio en el simulador, porque seleccionar clientes por el resultado que se desea evaluar produciría fuga de información.
- Los segmentos se definen con cuantiles de esta muestra; sus umbrales deben recalcularse si cambia el dataset.
- Las asociaciones de gasto, canales, familia y respuesta no demuestran causalidad.
