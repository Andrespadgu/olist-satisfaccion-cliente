import pandas as pd
import numpy as np

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
report = """# ANALISIS-VARIABLES-CATEGORICAS.md

Fecha de análisis: 2026-08-21

## Objetivo

Identificar todas las variables categóricas en los datasets procesados y evaluar
la viabilidad y estrategia de encoding para análisis estadístico y modelado.

---

## Resumen ejecutivo

Se realizará un análisis de:
1. Ubicación y cantidad de variables categóricas
2. Cardinalidad (valores únicos) de cada variable
3. Distribución de frecuencias
4. Estrategia de encoding recomendada

---

"""

# Diccionario para guardar resultados
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

total_categoricas = 0
total_filas = 0

for dataset_name, df in datasets.items():
    report += f"\n---\n\n## {dataset_name}\n\n"

    # Identificar columnas categóricas (object type, principalmente)
    categorical_cols = df.select_dtypes(include=['object']).columns

    if len(categorical_cols) == 0:
        report += "**No hay variables categóricas** (solo numéricas o flags binarios)\n\n"
        continue

    report += f"**Variables categóricas encontradas:** {len(categorical_cols)}\n"
    report += f"**Total de filas:** {len(df):,}\n\n"

    total_categoricas += len(categorical_cols)
    total_filas = max(total_filas, len(df))

    # Tabla resumen
    report += "| Variable | Tipo | Valores únicos | % Nulos | Cardinalidad | Recomendación |\n"
    report += "|----------|------|----------------|---------|--------------|---------------|\n"

    for col in categorical_cols:
        unique_count = df[col].nunique()
        null_pct = (df[col].isnull().sum() / len(df)) * 100
        null_count = df[col].isnull().sum()

        # Determinar tipo y recomendación
        if unique_count <= 2:
            tipo = "Binaria"
            recomendacion = "Label Encoding (0/1) o Direct"
        elif unique_count <= 10:
            tipo = "Ordinal (baja card.)"
            recomendacion = "One-Hot Encoding o Label"
        elif unique_count <= 100:
            tipo = "Nominal (med. card.)"
            recomendacion = "One-Hot (si pocas nulas) o Target Encoding"
        else:
            tipo = "Nominal (alta card.)"
            recomendacion = "Target Encoding o Embedding"

        report += f"| {col} | {tipo} | {unique_count} | {null_pct:.2f}% | "
        report += f"{'Alta' if unique_count > 100 else 'Media' if unique_count > 10 else 'Baja'} | {recomendacion} |\n"

    # Detalles por columna
    report += "\n### Detalles:\n\n"

    for col in categorical_cols:
        report += f"#### {col}\n"

        unique_count = df[col].nunique()
        null_count = df[col].isnull().sum()

        report += f"- **Valores únicos:** {unique_count}\n"
        report += f"- **Nulos:** {null_count} ({(null_count/len(df))*100:.2f}%)\n"

        # Top valores
        top_values = df[col].value_counts().head(10)

        report += f"- **Distribución (top 10):**\n"

        for val, freq in top_values.items():
            pct = (freq / len(df)) * 100
            report += f"  - {val}: {freq:,} ({pct:.2f}%)\n"

        # Recomendación detallada
        report += f"\n- **Recomendación de encoding:**\n"

        if unique_count <= 2:
            report += f"  - **Tipo:** Variable binaria\n"
            report += f"  - **Método:** Label Encoding (0/1) o Direct mapping\n"
            report += f"  - **Código:** `pd.factorize(df['{col}'])[0]` o manual mapping\n"

        elif unique_count <= 10:
            report += f"  - **Tipo:** Baja cardinalidad\n"
            report += f"  - **Método 1:** One-Hot Encoding (recomendado para regresión)\n"
            report += f"  - **Código:** `pd.get_dummies(df['{col}'])`\n"
            report += f"  - **Método 2:** Label Encoding (para tree-based)\n"
            report += f"  - **Código:** `pd.factorize(df['{col}'])[0]`\n"

        elif unique_count <= 100:
            report += f"  - **Tipo:** Cardinalidad media\n"
            report += f"  - **Método 1 (si pocas nulas):** One-Hot (producirá {unique_count} columnas)\n"
            report += f"  - **Código:** `pd.get_dummies(df['{col}'])`\n"
            report += f"  - **Método 2 (mejor):** Target Encoding\n"
            report += f"  - **Idea:** Reemplazar por promedio de target (review_score) por categoría\n"

        else:
            report += f"  - **Tipo:** Alta cardinalidad (riesgo de overfitting)\n"
            report += f"  - **Método 1 (mejor):** Target Encoding\n"
            report += f"  - **Idea:** Reemplazar por promedio de target (review_score) por categoría\n"
            report += f"  - **Método 2:** Embedding (para redes neuronales)\n"
            report += f"  - **Método 3:** Frecuency Encoding\n"
            report += f"  - **NO recomendado:** One-Hot (crearía {unique_count} columnas = maldición de dimensionalidad)\n"

        report += f"\n"

# Resumen global
report += "\n---\n\n## RESUMEN GLOBAL\n\n"

report += f"**Total de variables categóricas en todos los datasets:** {total_categoricas}\n\n"

report += """### Estrategia general de encoding:

#### 1. Variables binarias (0-2 valores únicos)
- **Método:** Label Encoding directo
- **Herramienta:** `pd.factorize()` o manual mapping
- **Ventajas:** Sin aumento de dimensionalidad, funciona bien con árboles y regresión
- **Ejemplo:**
  ```python
  df['variable_binaria'] = pd.factorize(df['variable_binaria'])[0]
  ```

#### 2. Baja cardinalidad (3-10 valores únicos)
- **Mejor método:** One-Hot Encoding (para regresión lineal)
- **Alternativa:** Label Encoding (para tree-based models)
- **Herramienta:** `pd.get_dummies()`
- **Ejemplo:**
  ```python
  df_encoded = pd.get_dummies(df[['order_status']], prefix='status')
  df = pd.concat([df, df_encoded], axis=1)
  df.drop('order_status', axis=1, inplace=True)
  ```

#### 3. Cardinalidad media (11-100 valores únicos)
- **Mejor método:** One-Hot Encoding O Target Encoding
  - One-Hot: Si interpretabilidad es crítica (regresión con business rules)
  - Target Encoding: Si dimensionalidad es problema (muchas categorías)
- **Herramientas:** `pd.get_dummies()` o manual Target Encoding
- **Ejemplo Target Encoding:**
  ```python
  target_means = df.groupby('product_category')['review_score'].mean()
  df['product_category_encoded'] = df['product_category'].map(target_means)
  ```

#### 4. Alta cardinalidad (>100 valores únicos)
- **Mejor método:** Target Encoding (riesgo de overfitting mínimo)
- **Alternativa:** Embedding (para redes neuronales)
- **NO usar:** One-Hot Encoding (maldición de dimensionalidad)
- **Ejemplo:**
  ```python
  # Target encoding para seller_id u order_id
  target_means = df.groupby('seller_id')['review_score'].mean()
  df['seller_score'] = df['seller_id'].map(target_means)
  ```

---

### Consideraciones importantes:

1. **Variables objetivo:**
   - `review_score`: Ya es numérica (1-5), usar directamente

2. **Variables de ID (no codificar directamente):**
   - `order_id`, `customer_id`, `seller_id`, `product_id`
   - Usar en contexto: aggregations, joins
   - O usar Target Encoding si es predictor

3. **Timestamps:**
   - Convertir a datetime primero: `pd.to_datetime()`
   - Extraer features: año, mes, día, día de semana, hora
   - O usar como tiempo transcurrido desde referencia

4. **Ubicación:**
   - `customer_state`, `seller_state`: Usar One-Hot o Label
   - `geolocation_lat`, `geolocation_lng`: Ya numéricas, pueden normalizarse

5. **Riesgo de data leakage:**
   - Si usas Target Encoding, SIEMPRE separar train/test primero
   - Calcular means SOLO en training set
   - Aplicar a test set con `map()`

---

## Recomendación para siguiente paso

Se recomienda:
1. Decidir entre regresión lineal (requiere One-Hot) o tree-based (permite Label)
2. Implementar encoding según estrategia elegida
3. Crear matriz numérica final para análisis estadístico
4. Validar ausencia de multicolinealidad (VIF) si regresión
5. Proceder a análisis inferencial (tests de hipótesis, modelado)
"""

# Guardar reporte
with open("ANALISIS-VARIABLES-CATEGORICAS.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Análisis de variables categóricas completado")
print(f"Reporte guardado: ANALISIS-VARIABLES-CATEGORICAS.md")
print(f"\nTotal de variables categóricas encontradas: {total_categoricas}")
