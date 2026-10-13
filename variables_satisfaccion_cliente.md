# Variables para el análisis de satisfacción del cliente — Olist

## Cuadro 1: Variables del dataset

| Variable | Tabla | Rol en satisfacción |
|---|---|---|
| `review_score` | reviews | **Variable objetivo** (1-5 estrellas) |
| `review_comment_message` | reviews | Texto para análisis de sentimiento |
| `order_purchase_timestamp` | orders | Inicio del ciclo, base para calcular tiempos |
| `order_approved_at` | orders | Rapidez de aprobación del pago |
| `order_delivered_carrier_date` | orders | Rapidez de despacho del vendedor |
| `order_delivered_customer_date` | orders | Fecha real de entrega |
| `order_estimated_delivery_date` | orders | Promesa de entrega (clave para calcular retraso) |
| `order_status` | orders | Cancelados/no disponibles = insatisfacción directa |
| `shipping_limit_date` | order_items | Si el vendedor cumplió su plazo interno |
| `price` | order_items | Precio del producto |
| `freight_value` | order_items | Costo de envío (frustración si es alto vs precio) |
| `payment_type` | payments | Método de pago, posible correlación con experiencia |
| `payment_installments` | payments | Nº de cuotas, perfil de expectativa del cliente |
| `payment_value` | payments | Monto total pagado |
| `product_category_name` | products | Categorías con más/menos quejas |
| `product_weight_g` / `_length_cm` / `_height_cm` / `_width_cm` | products | Productos grandes/pesados → más riesgo de daño |
| `product_photos_qty` | products | Más fotos = expectativas mejor manejadas |
| `product_name_lenght` / `product_description_lenght` | products | Descripción pobre → expectativas mal manejadas |
| `customer_state` / `customer_city` | customers | Región del cliente (logística desigual en Brasil) |
| `seller_state` / `seller_city` | sellers | Región del vendedor |
| `seller_id` | sellers/items | Permite detectar vendedores con mal desempeño |
| `geolocation_lat` / `geolocation_lng` | geolocation | Calcular distancia seller-customer (predictor fuerte) |

## Cuadro 2: Variables derivadas más potentes (no vienen listas, se calculan)

| Derivada | Cómo se calcula | Por qué importa |
|---|---|---|
| Días de retraso | `order_delivered_customer_date` − `order_estimated_delivery_date` | El predictor más fuerte de mala calificación |
| Tiempo total de entrega | `order_delivered_customer_date` − `order_purchase_timestamp` | Percepción general de rapidez |
| Distancia seller-customer | lat/lng de ambos (geolocation) | A mayor distancia, más riesgo de retraso |
| Ratio flete/precio | `freight_value` / `price` | Envío "caro" percibido |
