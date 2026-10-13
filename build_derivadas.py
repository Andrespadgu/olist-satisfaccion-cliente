# -*- coding: utf-8 -*-
"""
Construye dos datasets analiticos maestros para Olist:
  1) data/processed/analitico_cliente.csv   (un registro por order con review)
  2) data/processed/analitico_vendedor.csv  (un registro por seller_id)

NOTA METODOLOGICA CRITICA
-------------------------
Los archivos data/processed/*_clean.csv NO contienen las llaves de union ni los
zip prefixes necesarios para este trabajo (el paso de limpieza previo elimino
order_id, product_id, customer_zip_code_prefix, seller_zip_code_prefix como
"variables que no sirven"). Sin esas columnas es IMPOSIBLE:
  - unir orders <-> items <-> payments <-> reviews (falta order_id)
  - unir items <-> products (falta product_id)
  - calcular distancia haversine (faltan zip prefixes -> geolocation)

Por eso se leen los CSV de data/raw/ en MODO SOLO LECTURA (no se modifican nunca)
para recuperar esas llaves, y se REPLICAN las decisiones de limpieza documentadas
en LIMPIEZA-DATOS-PROGRESO.md (p.ej. eliminar productos sin categoria, conservar
multipagos, mantener nulos de fechas como NaN). Esto mantiene trazabilidad total.
"""
import pandas as pd
import numpy as np

RAW = r"C:/Users/ANDRES/Desktop/Maquinas no supervisadas/data/raw"
OUT = r"C:/Users/ANDRES/Desktop/Maquinas no supervisadas/data/processed"

DATE_COLS_ORDERS = [
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

report = {}

# ---------------------------------------------------------------------------
# 1. CARGA (solo lectura) + conversion de fechas
# ---------------------------------------------------------------------------
orders = pd.read_csv(f"{RAW}/olist_orders_dataset.csv")
for c in DATE_COLS_ORDERS:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")

items = pd.read_csv(f"{RAW}/olist_order_items_dataset.csv")
items["shipping_limit_date"] = pd.to_datetime(items["shipping_limit_date"], errors="coerce")

payments = pd.read_csv(f"{RAW}/olist_order_payments_dataset.csv")
products = pd.read_csv(f"{RAW}/olist_products_dataset.csv")
reviews = pd.read_csv(f"{RAW}/olist_order_reviews_dataset.csv")
customers = pd.read_csv(f"{RAW}/olist_customers_dataset.csv")
sellers = pd.read_csv(f"{RAW}/olist_sellers_dataset.csv")
geo = pd.read_csv(f"{RAW}/olist_geolocation_dataset.csv")
transl = pd.read_csv(f"{RAW}/product_category_name_translation.csv")

# ---------------------------------------------------------------------------
# 2. REPLICAR DECISIONES DE LIMPIEZA DOCUMENTADAS
# ---------------------------------------------------------------------------
# Products: eliminar filas sin categoria (decision Paso 3). Traducir a ingles.
n_prod_antes = len(products)
products = products.merge(transl, on="product_category_name", how="left")
products = products[products["product_category_name"].notna()].copy()
report["products_filas_sin_categoria_eliminadas"] = n_prod_antes - len(products)

# Reviews: puede haber >1 review por order en raw. Nos quedamos con la mas
# reciente por order_id (review_answer_timestamp) para tener 1 review por order.
reviews["review_answer_timestamp"] = pd.to_datetime(reviews["review_answer_timestamp"], errors="coerce")
n_rev_antes = len(reviews)
reviews = (reviews.sort_values("review_answer_timestamp")
                  .drop_duplicates(subset="order_id", keep="last"))
report["reviews_duplicados_por_order_eliminados"] = n_rev_antes - len(reviews)

# ---------------------------------------------------------------------------
# 3. GEOLOCALIZACION: promedio lat/lng por zip_code_prefix
# ---------------------------------------------------------------------------
geo_avg = (geo.groupby("geolocation_zip_code_prefix")
              .agg(lat=("geolocation_lat", "mean"),
                   lng=("geolocation_lng", "mean"))
              .reset_index())

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

# ---------------------------------------------------------------------------
# 4. AGREGADOS AUXILIARES POR ORDER
# ---------------------------------------------------------------------------
# Pagos por order: sumar payment_value (multipago), y tomar el payment_type
# del pago de mayor valor como tipo principal.
pay_sum = payments.groupby("order_id")["payment_value"].sum().rename("payment_value")
pay_type = (payments.sort_values("payment_value")
                    .drop_duplicates("order_id", keep="last")
                    .set_index("order_id")["payment_type"].rename("payment_type"))
pay_inst = payments.groupby("order_id")["payment_installments"].max().rename("payment_installments")
pay_agg = pd.concat([pay_sum, pay_type, pay_inst], axis=1).reset_index()

# Items por order: un pedido puede tener varios items/productos/vendedores.
# ITEM PRINCIPAL = order_item_id == 1 (primer item). Ademas agregamos price y
# freight sumados a nivel order (valor total del pedido) para el ratio.
items_sorted = items.sort_values(["order_id", "order_item_id"])
item_principal = items_sorted.drop_duplicates("order_id", keep="first")[
    ["order_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"]
].copy()
item_totales = items.groupby("order_id").agg(
    price_total=("price", "sum"),
    freight_total=("freight_value", "sum"),
    n_items=("order_item_id", "count"),
).reset_index()

# ---------------------------------------------------------------------------
# 5. DATASET NIVEL CLIENTE
# ---------------------------------------------------------------------------
df = orders.merge(reviews[["order_id", "review_score", "review_comment_message"]],
                  on="order_id", how="inner")  # solo orders con review

df = df.merge(item_principal, on="order_id", how="left")
df = df.merge(item_totales, on="order_id", how="left")
df = df.merge(pay_agg, on="order_id", how="left")

# product category (ingles) via product_id del item principal
df = df.merge(products[["product_id", "product_category_name_english"]],
              on="product_id", how="left")

# customer + seller state y zip
df = df.merge(customers[["customer_id", "customer_state", "customer_zip_code_prefix"]],
              on="customer_id", how="left")
df = df.merge(sellers[["seller_id", "seller_state", "seller_zip_code_prefix"]],
              on="seller_id", how="left")

# geo del cliente y del vendedor
df = df.merge(geo_avg.rename(columns={"geolocation_zip_code_prefix": "customer_zip_code_prefix",
                                      "lat": "cust_lat", "lng": "cust_lng"}),
              on="customer_zip_code_prefix", how="left")
df = df.merge(geo_avg.rename(columns={"geolocation_zip_code_prefix": "seller_zip_code_prefix",
                                      "lat": "sell_lat", "lng": "sell_lng"}),
              on="seller_zip_code_prefix", how="left")

# --- DERIVADAS ---
df["dias_retraso"] = (df["order_delivered_customer_date"] -
                      df["order_estimated_delivery_date"]).dt.total_seconds() / 86400.0
df["tiempo_entrega_dias"] = (df["order_delivered_customer_date"] -
                             df["order_purchase_timestamp"]).dt.total_seconds() / 86400.0
# ratio flete/precio: usamos totales del pedido; evitar division por cero
df["ratio_flete_precio"] = np.where(df["price_total"] > 0,
                                    df["freight_total"] / df["price_total"], np.nan)
df["distancia_seller_customer_km"] = haversine(df["cust_lat"], df["cust_lng"],
                                               df["sell_lat"], df["sell_lng"])

# columnas expuestas price / freight (del item principal, como pide el enunciado)
cliente_cols = [
    "order_id", "review_score", "review_comment_message",
    "dias_retraso", "tiempo_entrega_dias", "ratio_flete_precio",
    "distancia_seller_customer_km",
    "price", "freight_value", "price_total", "freight_total", "n_items",
    "payment_value", "payment_type", "payment_installments",
    "product_category_name_english",
    "customer_state", "seller_state", "order_status",
    "order_purchase_timestamp", "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
analitico_cliente = df[cliente_cols].copy()
analitico_cliente.to_csv(f"{OUT}/analitico_cliente.csv", index=False)

report["cliente_filas"] = len(analitico_cliente)
report["cliente_nulos_zip_sin_geo_cliente"] = int(df["cust_lat"].isna().sum())
report["cliente_nulos_zip_sin_geo_seller"] = int(df["sell_lat"].isna().sum())
report["cliente_nulos_por_col_derivada"] = {
    c: f"{analitico_cliente[c].isna().mean()*100:.2f}%"
    for c in ["dias_retraso", "tiempo_entrega_dias", "ratio_flete_precio",
              "distancia_seller_customer_km", "payment_value",
              "product_category_name_english"]
}

# ---------------------------------------------------------------------------
# 6. DATASET NIVEL VENDEDOR
# ---------------------------------------------------------------------------
# Base a nivel item-order-seller (un seller puede aparecer en muchos orders).
si = items.merge(orders, on="order_id", how="left")
si = si.merge(reviews[["order_id", "review_score"]], on="order_id", how="left")
si = si.merge(pay_sum.reset_index(), on="order_id", how="left")
si = si.merge(customers[["customer_id", "customer_zip_code_prefix"]],
              on="customer_id", how="left")
si = si.merge(sellers[["seller_id", "seller_zip_code_prefix"]],
              on="seller_id", how="left")
si = si.merge(geo_avg.rename(columns={"geolocation_zip_code_prefix": "customer_zip_code_prefix",
                                      "lat": "c_lat", "lng": "c_lng"}),
              on="customer_zip_code_prefix", how="left")
si = si.merge(geo_avg.rename(columns={"geolocation_zip_code_prefix": "seller_zip_code_prefix",
                                      "lat": "s_lat", "lng": "s_lng"}),
              on="seller_zip_code_prefix", how="left")

# derivadas a nivel item para luego promediar por seller
# solo cuenta como tardio/no-tardio si hay fecha de carrier; si es NaN -> NaN
si["despacho_tardio"] = np.where(
    si["order_delivered_carrier_date"].isna(), np.nan,
    (si["order_delivered_carrier_date"] > si["shipping_limit_date"]).astype(float))
si["tiempo_despacho_dias"] = (si["order_delivered_carrier_date"] -
                              si["order_purchase_timestamp"]).dt.total_seconds() / 86400.0
si["cancelado"] = si["order_status"].isin(["canceled", "unavailable"])
si["ratio_flete_precio"] = np.where(si["price"] > 0, si["freight_value"] / si["price"], np.nan)
si["dist_km"] = haversine(si["c_lat"], si["c_lng"], si["s_lat"], si["s_lng"])

# payment_value por order lo dividimos entre nro de items del order para no
# contar el mismo pago varias veces al agregar por seller (aproximacion de
# asignacion proporcional del ticket a cada item/vendedor del pedido).
items_por_order = items.groupby("order_id")["order_item_id"].count().rename("n_items_order")
si = si.merge(items_por_order.reset_index(), on="order_id", how="left")
si["payment_value_item"] = si["payment_value"] / si["n_items_order"]

grp = si.groupby("seller_id")
analitico_vendedor = pd.DataFrame({
    "review_score_promedio": grp["review_score"].mean(),
    "pct_despachos_tardios": grp["despacho_tardio"].mean() * 100,
    "tiempo_despacho_promedio_dias": grp["tiempo_despacho_dias"].mean(),
    "pct_cancelados": grp["cancelado"].mean() * 100,
    "volumen_ventas": grp["payment_value_item"].sum(),
    "ratio_flete_precio_promedio": grp["ratio_flete_precio"].mean(),
    "distancia_promedio_a_clientes": grp["dist_km"].mean(),
    "n_pedidos": grp["order_id"].nunique(),
}).reset_index()

# adjuntar seller_state para contexto
analitico_vendedor = analitico_vendedor.merge(
    sellers[["seller_id", "seller_state"]], on="seller_id", how="left")

analitico_vendedor.to_csv(f"{OUT}/analitico_vendedor.csv", index=False)

report["vendedor_filas"] = len(analitico_vendedor)
report["vendedor_nulos_por_col_derivada"] = {
    c: f"{analitico_vendedor[c].isna().mean()*100:.2f}%"
    for c in ["review_score_promedio", "pct_despachos_tardios",
              "tiempo_despacho_promedio_dias", "pct_cancelados",
              "volumen_ventas", "ratio_flete_precio_promedio",
              "distancia_promedio_a_clientes"]
}

# ---------------------------------------------------------------------------
# 7. REPORTE
# ---------------------------------------------------------------------------
print("=" * 70)
print("REPORTE DE CONSTRUCCION DE DERIVADAS")
print("=" * 70)
import json
print(json.dumps(report, indent=2, ensure_ascii=False))

print("\n--- CLIENTE: describe derivadas ---")
print(analitico_cliente[["dias_retraso", "tiempo_entrega_dias",
                         "ratio_flete_precio", "distancia_seller_customer_km"]].describe())
print("\n--- VENDEDOR: describe ---")
print(analitico_vendedor[["review_score_promedio", "pct_despachos_tardios",
                          "tiempo_despacho_promedio_dias", "pct_cancelados",
                          "n_pedidos"]].describe())
