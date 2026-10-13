# Mapeo de variables a los 11 conceptos de análisis — Olist

> Solo se incluyen las variables ya validadas como útiles para satisfacción del cliente y del vendedor.
> Una variable puede aplicar a varios conceptos, o a ninguno si los 11 conceptos no la requieren.

## Cuadro de mapeo

| Variable | Origen | Conceptos aplicables |
|---|---|---|
| `review_score` | Cliente | Probabilidad condicional, Teorema de Bayes, Independencia y Correlación, Prior y Posterior, Entropía cruzada, Divergencia KL |
| `order_purchase_timestamp` | Cliente | Probabilidad condicional, Teorema de Bayes, Verosimilitud/MLE, Independencia y Correlación (base para calcular tiempo de entrega) |
| `order_delivered_customer_date` | Cliente | Probabilidad condicional, Teorema de Bayes, Verosimilitud/MLE, Independencia y Correlación (base para calcular tiempo/retraso de entrega) |
| `order_estimated_delivery_date` | Cliente | Probabilidad condicional, Teorema de Bayes, Verosimilitud/MLE, Independencia y Correlación (base para calcular días de retraso) |
| Días de retraso (derivada) | Cliente | Probabilidad condicional, Teorema de Bayes, Independencia y Correlación, Entropía cruzada |
| Tiempo total de entrega (derivada) | Cliente | Probabilidad condicional, Teorema de Bayes, Verosimilitud/MLE, Independencia y Correlación, Entropía cruzada |
| `order_delivered_carrier_date` | Vendedor | Prior y Posterior (calcular tiempo de despacho del vendedor) |
| `shipping_limit_date` | Vendedor | Prior y Posterior (calcular % de despachos tardíos) |
| `order_status` | Vendedor | Prior y Posterior (calcular % de cancelaciones) |
| `price` | Cliente/Vendedor | Distribuciones paramétricas, Esperanza y Varianza, Entropía cruzada |
| `freight_value` | Cliente/Vendedor | Verosimilitud/MLE, Distribuciones paramétricas, Entropía cruzada |
| Ratio flete/precio (derivada) | Cliente/Vendedor | Distribuciones paramétricas, Entropía cruzada |
| `payment_type` | Cliente | Independencia y Correlación, Entropía |
| `payment_value` | Cliente/Vendedor | Esperanza y Varianza, Entropía cruzada |
| `product_category_name_english` | Cliente/Vendedor | Esperanza y Varianza, Independencia y Correlación, Entropía, Divergencia KL |
| `product_weight_g` / `_length_cm` / `_height_cm` / `_width_cm` | Cliente | Distribuciones paramétricas |
| `customer_state` / `customer_city` | Cliente | Esperanza y Varianza, Divergencia KL |
| `seller_id` | Vendedor | Prior y Posterior, Entropía cruzada |
| Review score promedio por vendedor (derivada) | Vendedor | Teorema de Bayes, Prior y Posterior, Entropía cruzada, Divergencia KL |
| % despachos tardíos (derivada) | Vendedor | Prior y Posterior, Entropía cruzada |
| % cancelados (derivada) | Vendedor | Prior y Posterior, Entropía cruzada |
| Volumen de ventas (derivada) | Vendedor | Esperanza y Varianza, Prior y Posterior |
| `order_approved_at` | Cliente | Ninguno |
| `payment_installments` | Cliente | Ninguno |
| `product_photos_qty` | Cliente | Ninguno |
| `product_name_lenght` / `product_description_lenght` | Cliente | Ninguno |
| `review_comment_message` | Cliente | Ninguno (requiere NLP, no estadística clásica) |
| `seller_state` / `seller_city` | Vendedor | Ninguno |
| `geolocation_lat` / `geolocation_lng` | Cliente/Vendedor | Ninguno |
| Distancia seller-customer (derivada) | Cliente/Vendedor | Ninguno |

## Notas
- Las variables marcadas como **"Ninguno"** sí son útiles para el análisis general de satisfacción (como ya se definió antes), pero ninguno de los 11 conceptos estadísticos de la imagen las necesita de forma directa.
- Concepto 9 (Entropía cruzada / clasificador) es el que más variables acepta, porque cualquier feature numérica o categórica relevante puede alimentar un modelo de regresión logística que prediga reseña positiva/negativa.
- Las variables base de fechas (`order_purchase_timestamp`, `order_delivered_customer_date`, `order_estimated_delivery_date`) casi siempre se usan de forma indirecta, a través de las variables derivadas (tiempo de entrega, días de retraso).
