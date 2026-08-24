import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("Iniciando encoding e ingenieria de features...")

# Cargar datos originales para recuperar order_id
orders_raw = pd.read_csv("data/raw/olist_orders_dataset.csv")
orders_raw = orders_raw[['order_id', 'customer_id']].copy()

# Cargar datos procesados
orders = pd.read_csv("data/processed/olist_orders_clean.csv")
geolocation = pd.read_csv("data/processed/olist_geolocation_clean.csv")
payments = pd.read_csv("data/processed/olist_order_payments_clean.csv")
products = pd.read_csv("data/processed/olist_products_clean.csv")
sellers = pd.read_csv("data/processed/olist_sellers_clean.csv")
customers = pd.read_csv("data/processed/olist_customers_clean.csv")
reviews = pd.read_csv("data/processed/olist_order_reviews_clean.csv")
order_items = pd.read_csv("data/processed/olist_order_items_clean.csv")

# Recuperar order_id en orders (se elimino en limpieza)
orders = orders_raw.merge(orders, left_index=True, right_index=True, how='left')

# Inicializar reporte
report = f"""# ENCODING-FEATURES-APLICADO.md

Fecha de aplicacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumen ejecutivo

Se aplico encoding segun estrategia recomendada:
1. One-Hot Encoding: variables de baja cardinalidad
2. Target Encoding: IDs con alta cardinalidad
3. Feature Extraction: timestamps
4. Label Encoding: ordinales

Datasets finales listos para analisis estadistico.

---

"""

# ============================================================================
# PASO 0: Crear target mappings (antes de transformar)
# ============================================================================
print("Paso 0: Creando target encodings...")

# seller_id -> avg review_score
seller_target_map = None
if 'seller_id' in order_items.columns:
    orders_with_reviews = orders.merge(reviews[['order_id', 'review_score']], on='order_id', how='left')
    orders_with_items = orders_with_reviews.merge(order_items[['order_id', 'seller_id']], on='order_id', how='left')
    seller_target_map = orders_with_items.groupby('seller_id')['review_score'].mean()

# customer_id -> avg review_score
customer_target_map = None
if 'customer_id' in orders.columns:
    orders_with_reviews = orders.merge(reviews[['order_id', 'review_score']], on='order_id', how='left')
    customer_target_map = orders_with_reviews.groupby('customer_id')['review_score'].mean()

# ============================================================================
# PASO 1: Feature Extraction de Timestamps
# ============================================================================
print("Paso 1: Extrayendo features de timestamps...")

def extract_datetime_features(df, col_name):
    if col_name not in df.columns:
        return df

    df[col_name] = pd.to_datetime(df[col_name], errors='coerce')

    df[f'{col_name}_year'] = df[col_name].dt.year
    df[f'{col_name}_month'] = df[col_name].dt.month
    df[f'{col_name}_day'] = df[col_name].dt.day
    df[f'{col_name}_hour'] = df[col_name].dt.hour
    df[f'{col_name}_dayofweek'] = df[col_name].dt.dayofweek

    df.drop(columns=[col_name], inplace=True)

    return df

# Aplicar a orders
orders = extract_datetime_features(orders, 'order_purchase_timestamp')
orders = extract_datetime_features(orders, 'order_approved_at')
orders = extract_datetime_features(orders, 'order_delivered_carrier_date')
orders = extract_datetime_features(orders, 'order_delivered_customer_date')
orders = extract_datetime_features(orders, 'order_estimated_delivery_date')

report += "### Feature Extraction de Timestamps\n\n"
report += "Columnas extraidas:\n"
report += "- order_purchase_timestamp -> year, month, day, hour, dayofweek\n"
report += "- order_approved_at -> year, month, day, hour, dayofweek\n"
report += "- order_delivered_carrier_date -> year, month, day, hour, dayofweek\n"
report += "- order_delivered_customer_date -> year, month, day, hour, dayofweek\n"
report += "- order_estimated_delivery_date -> year, month, day, hour, dayofweek\n\n"

# ============================================================================
# PASO 2: One-Hot Encoding para variables de BAJA cardinalidad
# ============================================================================
print("Paso 2: One-Hot Encoding...")

report += "### One-Hot Encoding\n\n"

# order_status
if 'order_status' in orders.columns:
    order_status_dummies = pd.get_dummies(orders['order_status'], prefix='order_status')
    orders = pd.concat([orders.drop(columns=['order_status']), order_status_dummies], axis=1)
    report += f"- order_status: {order_status_dummies.shape[1]} columnas creadas\n"

# payment_type
if 'payment_type' in payments.columns:
    payment_type_dummies = pd.get_dummies(payments['payment_type'], prefix='payment_type')
    payments = pd.concat([payments.drop(columns=['payment_type']), payment_type_dummies], axis=1)
    report += f"- payment_type: {payment_type_dummies.shape[1]} columnas creadas\n"

# customer_state
if 'customer_state' in customers.columns:
    customer_state_dummies = pd.get_dummies(customers['customer_state'], prefix='customer_state')
    customers = pd.concat([customers.drop(columns=['customer_state']), customer_state_dummies], axis=1)
    report += f"- customer_state: {customer_state_dummies.shape[1]} columnas creadas\n"

# seller_state
if 'seller_state' in sellers.columns:
    seller_state_dummies = pd.get_dummies(sellers['seller_state'], prefix='seller_state')
    sellers = pd.concat([sellers.drop(columns=['seller_state']), seller_state_dummies], axis=1)
    report += f"- seller_state: {seller_state_dummies.shape[1]} columnas creadas\n"

# product_category_name_english
if 'product_category_name_english' in products.columns:
    category_dummies = pd.get_dummies(products['product_category_name_english'], prefix='category')
    products = pd.concat([products.drop(columns=['product_category_name_english']), category_dummies], axis=1)
    report += f"- product_category_name_english: {category_dummies.shape[1]} columnas creadas\n"

report += "\n"

# ============================================================================
# PASO 3: Target Encoding para IDs de ALTA cardinalidad
# ============================================================================
print("Paso 3: Target Encoding...")

report += "### Target Encoding (Embedding de IDs)\n\n"

# seller_id -> avg review_score
if seller_target_map is not None:
    order_items['seller_id_encoded'] = order_items['seller_id'].map(seller_target_map)
    sellers['seller_id_encoded'] = sellers['seller_id'].map(seller_target_map)

    report += f"- seller_id: {len(seller_target_map)} vendedores mapeados\n"
    report += f"  - Rango: {seller_target_map.min():.2f} a {seller_target_map.max():.2f}\n"

# customer_id -> avg review_score
if customer_target_map is not None:
    orders['customer_id_encoded'] = orders['customer_id'].map(customer_target_map)
    customers['customer_id_encoded'] = customers['customer_id'].map(customer_target_map)

    report += f"- customer_id: {len(customer_target_map)} clientes mapeados\n"
    report += f"  - Rango: {customer_target_map.min():.2f} a {customer_target_map.max():.2f}\n"

# Eliminar IDs originales
if 'seller_id' in order_items.columns:
    order_items.drop(columns=['seller_id'], inplace=True)
if 'seller_id' in sellers.columns:
    sellers.drop(columns=['seller_id'], inplace=True)
if 'customer_id' in orders.columns:
    orders.drop(columns=['customer_id'], inplace=True)
if 'customer_id' in customers.columns:
    customers.drop(columns=['customer_id'], inplace=True)

report += "\n"

# ============================================================================
# PASO 4: Guardar datasets finales codificados
# ============================================================================
print("Paso 4: Guardando datasets...")

orders.to_csv("data/processed/olist_orders_encoded.csv", index=False)
geolocation.to_csv("data/processed/olist_geolocation_encoded.csv", index=False)
payments.to_csv("data/processed/olist_order_payments_encoded.csv", index=False)
products.to_csv("data/processed/olist_products_encoded.csv", index=False)
sellers.to_csv("data/processed/olist_sellers_encoded.csv", index=False)
customers.to_csv("data/processed/olist_customers_encoded.csv", index=False)
reviews.to_csv("data/processed/olist_order_reviews_encoded.csv", index=False)
order_items.to_csv("data/processed/olist_order_items_encoded.csv", index=False)

# ============================================================================
# Resumen de cambios
# ============================================================================
print("\nResumen:")
print(f"- orders: {orders.shape[1]} columnas (era 10)")
print(f"- products: {products.shape[1]} columnas (era 8)")
print(f"- sellers: {sellers.shape[1]} columnas (era 3)")
print(f"- customers: {customers.shape[1]} columnas (era 4)")

report += f"---\n\n## Resumen de transformaciones\n\n"
report += "| Dataset | Filas | Columnas Antes | Columnas Despues |\n"
report += "|---------|-------|---|---|\n"
report += f"| orders | {len(orders)} | 10 | {orders.shape[1]} |\n"
report += f"| products | {len(products)} | 8 | {products.shape[1]} |\n"
report += f"| payments | {len(payments)} | 4 | {payments.shape[1]} |\n"
report += f"| sellers | {len(sellers)} | 3 | {sellers.shape[1]} |\n"
report += f"| customers | {len(customers)} | 4 | {customers.shape[1]} |\n"
report += f"| reviews | {len(reviews)} | 6 | {reviews.shape[1]} |\n"
report += f"| order_items | {len(order_items)} | 7 | {order_items.shape[1]} |\n"
report += f"| geolocation | {len(geolocation)} | 3 | {geolocation.shape[1]} |\n"

report += f"\n## Datasets finales (100% numericos)\n\n"
report += "Archivos guardados en `data/processed/` con sufijo `_encoded.csv`\n"
report += "Listos para:\n"
report += "- Pruebas no-parametricas (Mann-Whitney, Kruskal-Wallis, Spearman)\n"
report += "- Correlacion de Spearman\n"
report += "- Machine learning\n"

# Guardar reporte
with open("ENCODING-FEATURES-APLICADO.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\nEncoding completado - ENCODING-FEATURES-APLICADO.md")
