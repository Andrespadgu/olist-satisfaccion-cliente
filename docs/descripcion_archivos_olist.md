# Descripción de los archivos del dataset Olist y sus tipos de datos

Basado en el `.head()` y el `.info()` de cada archivo CSV cargado.

---

## 1. `olist_orders_dataset.csv`
**De qué habla:** es la tabla central del dataset. Un registro por cada pedido realizado, con su estado y todas las fechas del ciclo de vida del pedido (compra, aprobación, despacho, entrega, entrega estimada).

- **Filas:** 99,441 | **Columnas:** 8

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `order_id` | object | 99,441 | Completo |
| `customer_id` | object | 99,441 | Completo |
| `order_status` | object | 99,441 | Completo |
| `order_purchase_timestamp` | object | 99,441 | Completo (fecha guardada como texto, no datetime) |
| `order_approved_at` | object | 99,281 | ~160 valores nulos |
| `order_delivered_carrier_date` | object | 97,658 | ~1,783 valores nulos (pedidos aún no despachados/cancelados) |
| `order_delivered_customer_date` | object | 96,476 | ~2,965 valores nulos (pedidos aún no entregados/cancelados) |
| `order_estimated_delivery_date` | object | 99,441 | Completo |

**Nota:** todas las columnas de fecha están como `object` (texto), no como `datetime`. Habrá que convertirlas con `pd.to_datetime()` antes de calcular tiempos de entrega o retrasos.

---

## 2. `product_category_name_translation.csv`
**De qué habla:** tabla puente muy pequeña que traduce el nombre de la categoría del producto de portugués a inglés. Se usa para unir con `olist_products_dataset.csv`.

- **Filas:** 71 | **Columnas:** 2

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `product_category_name` | object | 71 | Completo |
| `product_category_name_english` | object | 71 | Completo |

---

## 3. `olist_geolocation_dataset.csv`
**De qué habla:** contiene coordenadas de latitud/longitud asociadas a prefijos de código postal en Brasil. Es la tabla más grande del dataset y permite calcular distancias entre clientes y vendedores.

- **Filas:** 1,000,163 | **Columnas:** 5

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `geolocation_zip_code_prefix` | int64 | 1,000,163 | Completo |
| `geolocation_lat` | float64 | 1,000,163 | Completo |
| `geolocation_lng` | float64 | 1,000,163 | Completo |
| `geolocation_city` | object | 1,000,163 | Completo |
| `geolocation_state` | object | 1,000,163 | Completo |

**Nota:** un mismo `zip_code_prefix` puede tener múltiples filas (varias coordenadas dentro del mismo prefijo), por lo que suele resumirse (promedio de lat/lng) antes de unirlo con otras tablas.

---

## 4. `olist_order_payments_dataset.csv`
**De qué habla:** un registro por cada transacción de pago realizada sobre un pedido (un pedido puede tener más de un pago si se combinaron métodos).

- **Filas:** 103,886 | **Columnas:** 5

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `order_id` | object | 103,886 | Completo |
| `payment_sequential` | int64 | 103,886 | Completo |
| `payment_type` | object | 103,886 | Completo |
| `payment_installments` | int64 | 103,886 | Completo |
| `payment_value` | float64 | 103,886 | Completo |

---

## 5. `olist_products_dataset.csv`
**De qué habla:** catálogo de productos, con su categoría, dimensiones físicas y datos de la publicación (longitud del nombre/descripción, cantidad de fotos).

- **Filas:** 32,951 | **Columnas:** 9

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `product_id` | object | 32,951 | Completo |
| `product_category_name` | object | 32,341 | ~610 valores nulos |
| `product_name_lenght` | float64 | 32,341 | ~610 valores nulos (coincide con categoría nula) |
| `product_description_lenght` | float64 | 32,341 | ~610 valores nulos |
| `product_photos_qty` | float64 | 32,341 | ~610 valores nulos |
| `product_weight_g` | float64 | 32,949 | 2 valores nulos |
| `product_length_cm` | float64 | 32,949 | 2 valores nulos |
| `product_height_cm` | float64 | 32,949 | 2 valores nulos |
| `product_width_cm` | float64 | 32,949 | 2 valores nulos |

---

## 6. `olist_sellers_dataset.csv`
**De qué habla:** catálogo de vendedores registrados en Olist, con su ubicación.

- **Filas:** 3,095 | **Columnas:** 4

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `seller_id` | object | 3,095 | Completo |
| `seller_zip_code_prefix` | int64 | 3,095 | Completo |
| `seller_city` | object | 3,095 | Completo |
| `seller_state` | object | 3,095 | Completo |

---

## 7. `olist_customers_dataset.csv`
**De qué habla:** catálogo de clientes, con su identificador único real (`customer_unique_id`, distinto del `customer_id` por pedido) y su ubicación.

- **Filas:** 99,441 | **Columnas:** 5

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `customer_id` | object | 99,441 | Completo |
| `customer_unique_id` | object | 99,441 | Completo |
| `customer_zip_code_prefix` | int64 | 99,441 | Completo |
| `customer_city` | object | 99,441 | Completo |
| `customer_state` | object | 99,441 | Completo |

---

## 8. `olist_order_reviews_dataset.csv`
**De qué habla:** reseñas de satisfacción que los clientes dejan por pedido, con calificación numérica y comentario opcional en texto.

- **Filas:** 99,224 | **Columnas:** 7

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `review_id` | object | 99,224 | Completo |
| `order_id` | object | 99,224 | Completo |
| `review_score` | int64 | 99,224 | Completo |
| `review_comment_title` | object | 11,568 | ~88% de valores nulos (la mayoría no pone título) |
| `review_comment_message` | object | 40,977 | ~59% de valores nulos (más de la mitad no escribe comentario) |
| `review_creation_date` | object | 99,224 | Completo |
| `review_answer_timestamp` | object | 99,224 | Completo |

---

## 9. `olist_order_items_dataset.csv`
**De qué habla:** el detalle de cada ítem/producto dentro de un pedido (un pedido puede tener varios ítems), con vendedor, precio, flete y plazo de despacho.

- **Filas:** 112,650 | **Columnas:** 7

| Columna | Tipo de dato | No nulos | Observación |
|---|---|---|---|
| `order_id` | object | 112,650 | Completo |
| `order_item_id` | int64 | 112,650 | Completo |
| `product_id` | object | 112,650 | Completo |
| `seller_id` | object | 112,650 | Completo |
| `shipping_limit_date` | object | 112,650 | Completo |
| `price` | float64 | 112,650 | Completo |
| `freight_value` | float64 | 112,650 | Completo |

---

## Resumen general

| Archivo | Filas | Columnas | Memoria aprox. |
|---|---|---|---|
| `olist_orders_dataset.csv` | 99,441 | 8 | 6.1+ MB |
| `product_category_name_translation.csv` | 71 | 2 | 1.2+ KB |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 38.2+ MB |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | 4.0+ MB |
| `olist_products_dataset.csv` | 32,951 | 9 | 2.3+ MB |
| `olist_sellers_dataset.csv` | 3,095 | 4 | 96.8+ KB |
| `olist_customers_dataset.csv` | 99,441 | 5 | 3.8+ MB |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | 5.3+ MB |
| `olist_order_items_dataset.csv` | 112,650 | 7 | 6.0+ MB |

**Notas clave para el análisis:**
- Todas las columnas de fecha llegan como `object` (texto) en los 9 archivos — es obligatorio convertirlas con `pd.to_datetime()` antes de calcular tiempos, retrasos o cualquier operación temporal.
- Las columnas con más valores nulos que requieren tratamiento son `review_comment_title`, `review_comment_message` (más de la mitad vacías, es normal en encuestas de satisfacción) y las fechas de entrega en `olist_orders_dataset.csv` (nulas cuando el pedido no llegó a esa etapa, por ejemplo pedidos cancelados).
- `olist_products_dataset.csv` tiene ~610 filas sin categoría ni datos de publicación — vale la pena decidir si se eliminan o se imputan antes de modelar.
