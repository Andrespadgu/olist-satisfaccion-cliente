import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Cargar datos procesados
orders = pd.read_csv("data/processed/olist_orders_clean.csv")
geolocation = pd.read_csv("data/processed/olist_geolocation_clean.csv")
payments = pd.read_csv("data/processed/olist_order_payments_clean.csv")
products = pd.read_csv("data/processed/olist_products_clean.csv")
sellers = pd.read_csv("data/processed/olist_sellers_clean.csv")
customers = pd.read_csv("data/processed/olist_customers_clean.csv")
reviews = pd.read_csv("data/processed/olist_order_reviews_clean.csv")
order_items = pd.read_csv("data/processed/olist_order_items_clean.csv")

# Inicializar reporte
report = """# PRUEBAS-NORMALIDAD.md

Fecha de pruebas: 2026-08-21

## Objetivo

Aplicar pruebas de normalidad (Shapiro-Wilk y Anderson-Darling) a todas las columnas numéricas
de cada dataset para identificar qué distribuciones siguen los datos.

**Importancia**: Las pruebas estadísticas posteriores (tests de hipótesis, ANOVA, regresión)
asumen normalidad en los residuos. Identificar desviaciones es crítico.

## Metodología

### Pruebas aplicadas:

1. **Shapiro-Wilk**:
   - Null hypothesis: Los datos siguen distribución normal
   - p-value > 0.05 → No rechaza normalidad
   - p-value < 0.05 → Rechaza normalidad
   - Mejor para: n < 5000
   - Para muestras > 5000: se usa muestra aleatoria de 5000

2. **Anderson-Darling**:
   - Null hypothesis: Los datos siguen distribución normal
   - Más sensible para detectar desviaciones (especialmente en colas)
   - Statistic > critical_value → Rechaza normalidad
   - Mejor para: muestras grandes

3. **Identificación de distribuciones alternativas**:
   - Log-normal: Shapiro-Wilk sobre log(x) para x > 0
   - Exponencial: Para datos positivos asimétricos
   - Gamma: Para datos positivos con forma variable
   - Uniforme: Para datos con distribución rectangular

---

"""

# Diccionario para guardar resultados
resultados = {}

# Función para probar normalidad
def test_normalidad(series, col_name, dataset_name):
    series = series.dropna()

    if len(series) == 0:
        return None

    result = {
        'columna': col_name,
        'dataset': dataset_name,
        'n': len(series),
        'media': series.mean(),
        'mediana': series.median(),
        'desv_std': series.std(),
        'asimetria': series.skew(),
        'curtosis': series.kurtosis(),
    }

    # Shapiro-Wilk
    if len(series) > 5000:
        sample = series.sample(n=5000, random_state=42)
        sw_stat, sw_pval = stats.shapiro(sample)
        result['shapiro_nota'] = f"(muestra de 5000 de {len(series)})"
    else:
        sw_stat, sw_pval = stats.shapiro(series)
        result['shapiro_nota'] = ""

    result['shapiro_stat'] = sw_stat
    result['shapiro_pval'] = sw_pval
    result['shapiro_normal'] = "SI" if sw_pval > 0.05 else "NO"

    # Anderson-Darling
    ad_result = stats.anderson(series)
    result['anderson_stat'] = ad_result.statistic
    result['anderson_crit_5pct'] = ad_result.critical_values[2]  # 5% level
    result['anderson_normal'] = "SI" if ad_result.statistic < ad_result.critical_values[2] else "NO"

    # Probar otras distribuciones
    distribucion_alternativa = None

    # Log-normal (solo si todos los valores > 0)
    if (series > 0).all():
        log_series = np.log(series)
        _, log_pval = stats.shapiro(log_series.sample(min(5000, len(log_series))))
        if log_pval > 0.05:
            distribucion_alternativa = f"Log-normal (p={log_pval:.4f})"

    # Exponencial (solo si positivos)
    if (series > 0).all() and distribucion_alternativa is None:
        # Fit exponencial
        loc, scale = stats.expon.fit(series)
        ks_stat, ks_pval = stats.kstest(series, lambda x: stats.expon.cdf(x, loc, scale))
        if ks_pval > 0.05:
            distribucion_alternativa = f"Exponencial (p={ks_pval:.4f})"

    result['distribucion_alternativa'] = distribucion_alternativa

    return result

# Procesar cada dataset
datasets = {
    'olist_orders_clean.csv': orders,
    'olist_geolocation_clean.csv': geolocation,
    'olist_order_payments_clean.csv': payments,
    'olist_products_clean.csv': products,
    'olist_sellers_clean.csv': sellers,
    'olist_customers_clean.csv': customers,
    'olist_order_reviews_clean.csv': reviews,
    'olist_order_items_clean.csv': order_items,
}

for dataset_name, df in datasets.items():
    report += f"\n---\n\n## {dataset_name}\n\n"

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        report += "**No hay columnas numéricas**\n\n"
        continue

    report += f"**Columnas numéricas:** {len(numeric_cols)}\n\n"

    # Tabla de resultados
    report += "| Columna | N | Media | Mediana | Asimetría | Shapiro-Wilk | Anderson-Darling | Distribución |\n"
    report += "|---------|---|-------|---------|-----------|--------------|------------------|---------------|\n"

    results_list = []

    for col in numeric_cols:
        result = test_normalidad(df[col], col, dataset_name)

        if result is None:
            continue

        results_list.append(result)

        # Fila de tabla
        normalidad = "✓ Normal" if result['shapiro_normal'] == "SI" and result['anderson_normal'] == "SI" else "✗ No-normal"

        distribucion_alt = result['distribucion_alternativa'] if result['distribucion_alternativa'] else "Normal"

        report += f"| {col} | {result['n']} | {result['media']:.2f} | {result['mediana']:.2f} | {result['asimetria']:.3f} | "
        report += f"p={result['shapiro_pval']:.2e} | stat={result['anderson_stat']:.2f} | {distribucion_alt} |\n"

    # Detalles por columna
    report += "\n### Detalles:\n\n"

    for result in results_list:
        col = result['columna']
        report += f"#### {col}\n"
        report += f"- **N:** {result['n']}\n"
        report += f"- **Estadísticas descriptivas:**\n"
        report += f"  - Media: {result['media']:.4f}\n"
        report += f"  - Mediana: {result['mediana']:.4f}\n"
        report += f"  - Desv. Std: {result['desv_std']:.4f}\n"
        report += f"  - Asimetría (skewness): {result['asimetria']:.4f}\n"
        report += f"  - Curtosis (kurtosis): {result['curtosis']:.4f}\n"

        report += f"- **Shapiro-Wilk Test** {result['shapiro_nota']}:\n"
        report += f"  - Statistic: {result['shapiro_stat']:.6f}\n"
        report += f"  - p-value: {result['shapiro_pval']:.2e}\n"
        report += f"  - **Resultado:** {result['shapiro_normal']} (normalidad)\n"

        report += f"- **Anderson-Darling Test:**\n"
        report += f"  - Statistic: {result['anderson_stat']:.4f}\n"
        report += f"  - Critical value (5%): {result['anderson_crit_5pct']:.4f}\n"
        report += f"  - **Resultado:** {result['anderson_normal']} (normalidad)\n"

        if result['distribucion_alternativa']:
            report += f"- **Distribución detectada:** {result['distribucion_alternativa']}\n"

        # Interpretación
        report += f"- **Interpretación:**\n"

        if result['asimetria'] > 1 or result['asimetria'] < -1:
            report += f"  - Asimetría fuerte ({'derecha' if result['asimetria'] > 0 else 'izquierda'})\n"
        elif result['asimetria'] > 0.5 or result['asimetria'] < -0.5:
            report += f"  - Asimetría moderada ({'derecha' if result['asimetria'] > 0 else 'izquierda'})\n"

        if result['curtosis'] > 3:
            report += f"  - Colas pesadas (leptocúrtica)\n"
        elif result['curtosis'] < -1:
            report += f"  - Colas ligeras (platicúrtica)\n"

        report += f"\n"

# Resumen general
report += "\n---\n\n## RESUMEN GENERAL\n\n"

normal_count = 0
nonnormal_count = 0

for dataset_name, df in datasets.items():
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        result = test_normalidad(df[col], col, dataset_name)

        if result is None:
            continue

        if result['shapiro_normal'] == "SI" and result['anderson_normal'] == "SI":
            normal_count += 1
        else:
            nonnormal_count += 1

total = normal_count + nonnormal_count
pct_normal = (normal_count / total * 100) if total > 0 else 0

report += f"**Variables numéricas totales:** {total}\n"
report += f"- **Normales:** {normal_count} ({pct_normal:.1f}%)\n"
report += f"- **No-normales:** {nonnormal_count} ({100 - pct_normal:.1f}%)\n\n"

report += "### Implicaciones para análisis estadístico:\n\n"
report += "1. **Variables normales**: Pueden usar pruebas paramétricas (t-test, ANOVA, regresión lineal)\n"
report += "2. **Variables no-normales**: Usar pruebas no-paramétricas (Mann-Whitney, Kruskal-Wallis) o transformaciones\n"
report += "3. **Transformaciones recomendadas**:\n"
report += "   - Asimetría derecha: log(x), sqrt(x), 1/x\n"
report += "   - Asimetría izquierda: x^2, x^3\n"
report += "   - Distribuciones extremas: Box-Cox transform\n\n"

# Guardar reporte
with open("PRUEBAS-NORMALIDAD.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Pruebas de normalidad completadas")
print(f"Reporte guardado: PRUEBAS-NORMALIDAD.md")
print(f"\nResumen: {normal_count} variables normales, {nonnormal_count} no-normales ({pct_normal:.1f}%)")
