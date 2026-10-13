# Variables para el análisis de satisfacción/desempeño del vendedor — Olist

> Nota: el dataset no tiene una encuesta directa al vendedor (como sí existe `review_score` para el cliente).
> Por eso, la "satisfacción del vendedor" se construye como una **variable proxy**, agregando por `seller_id`
> el promedio de `review_score` que reciben sus pedidos, junto con sus tiempos de cumplimiento y reclamos.

## Cuadro 1: Variables del dataset

| Variable | Tabla | Rol en desempeño/satisfacción del vendedor |
|---|---|---|
| `seller_id` | sellers/items | Llave para agregar todas las métricas por vendedor |
| `review_score` (promedio por seller_id) | reviews | **Variable objetivo proxy**: satisfacción que genera el vendedor |
| `review_comment_message` | reviews | Texto de quejas específicas relacionadas al vendedor (envío, producto) |
| `order_purchase_timestamp` | orders | Inicio del ciclo, base para calcular tiempos de despacho |
| `order_approved_at` | orders | Tiempo entre compra y aprobación (no depende del vendedor, pero afecta el ciclo) |
| `order_delivered_carrier_date` | orders | **Clave**: qué tan rápido el vendedor despachó el pedido |
| `order_delivered_customer_date` | orders | Fecha real de entrega al cliente |
| `order_estimated_delivery_date` | orders | Promesa de entrega, referencia para medir cumplimiento |
| `order_status` | orders | % de cancelados o no disponibles por vendedor |
| `shipping_limit_date` | order_items | **Clave**: plazo interno que tenía el vendedor para despachar |
| `order_delivered_carrier_date` vs `shipping_limit_date` | orders/items | Si el vendedor cumplió su propio plazo (derivada de cumplimiento) |
| `price` | order_items | Precio de los productos que vende (rango de mercado) |
| `freight_value` | order_items | Costo de envío asociado a sus productos |
| `payment_value` | payments | Volumen de ventas del vendedor |
| `product_category_name` | products | Categoría en la que opera (algunas tienen más quejas por naturaleza) |
| `product_photos_qty` | products | Calidad de la publicación (más fotos = menos reclamos por expectativa) |
| `product_name_lenght` / `product_description_lenght` | products | Calidad de la descripción del producto publicado |
| `seller_state` / `seller_city` | sellers | Ubicación del vendedor (afecta tiempos de entrega) |
| `customer_state` / `customer_city` | customers | Región de sus clientes (mercados más/menos exigentes o lejanos) |
| `geolocation_lat` / `geolocation_lng` | geolocation | Distancia promedio del vendedor a sus clientes |

## Cuadro 2: Variables derivadas más potentes (se calculan agregando por seller_id)

| Derivada | Cómo se calcula | Por qué importa |
|---|---|---|
| Review score promedio del vendedor | Promedio de `review_score` de todos los pedidos del seller_id | Métrica central de satisfacción generada |
| % de despachos tardíos | % de pedidos donde `order_delivered_carrier_date` > `shipping_limit_date` | Mide cumplimiento del vendedor con su propio plazo |
| Tiempo promedio de despacho | `order_delivered_carrier_date` − `order_purchase_timestamp` | Rapidez operativa del vendedor |
| % de pedidos cancelados/no disponibles | % de `order_status` en canceled/unavailable por seller_id | Indicador de confiabilidad del vendedor |
| Volumen total de ventas | Suma de `payment_value` por seller_id | Tamaño/relevancia del vendedor |
| Distancia promedio a sus clientes | lat/lng seller vs lat/lng customer (geolocation) | Vendedores muy alejados de sus clientes tienden a peor desempeño logístico |
| Ratio flete/precio promedio | `freight_value` / `price` promedio por seller_id | Si sus envíos se perciben como caros |
