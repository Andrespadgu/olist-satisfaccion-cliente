# Variables que no sirven para el análisis de satisfacción — Olist

| Variable | Tabla | Por qué no sirve |
|---|---|---|
| `order_id` | orders | Identificador único, un valor distinto por fila — no tiene poder predictivo, solo sirve para hacer los `join` entre tablas. |
| `review_id` | reviews | Igual que arriba: identificador único, cero valor explicativo. |
| `product_id` | products | Identificador único del producto; no dice nada por sí mismo (lo que importa es la categoría, peso, dimensiones, etc., no el ID). |
| `customer_id` | orders/customers | Cambia en cada pedido del mismo cliente (por diseño de anonimización), así que no permite ni identificar comportamiento repetido ni predecir nada — para eso está `customer_unique_id`, y ni ese es predictivo por sí solo, solo sirve para agrupar. |
| `payment_sequential` | payments | Es solo un número de secuencia cuando el pago se dividió en varios métodos; no mide monto, tiempo ni experiencia — es metadata técnica del registro, no un indicador de satisfacción. |
| `review_comment_title` | reviews | La mayoría de las reseñas llegan sin título (campo casi siempre vacío); su aporte real es marginal comparado con `review_comment_message`. |
| `geolocation_city` / `geolocation_state` | geolocation | Son redundantes: ya tienes `customer_city/state` y `seller_city/state` directamente en sus propias tablas — usar esta tabla solo aporta valor por la latitud/longitud, no por ciudad/estado repetidos. |
| `product_category_name` (versión en portugués) | products | No aporta nada adicional una vez que tienes `product_category_name_english` — es la misma información, solo cambia el idioma; usar ambas sería duplicar la variable. |
| `customer_zip_code_prefix` / `seller_zip_code_prefix` como variable categórica directa | customers/sellers | Por sí solos (sin cruzarlos con `geolocation` para sacar distancia o mapear región), tienen demasiados valores únicos — meterlos crudos en un modelo genera ruido/overfitting en vez de señal. Su valor real está en derivar distancia, no en usarlos tal cual. |

## Idea general

Las variables que no sirven son las que caen en una de estas tres categorías:

1. **Identificadores puros** (IDs únicos) — no tienen varianza explicativa, solo sirven para unir tablas.
2. **Redundantes** — ya existe otra columna que dice lo mismo (ej. categoría en dos idiomas, ciudad repetida en geolocation).
3. **Metadata técnica del registro** (como `payment_sequential`) — describe cómo se guardó el dato, no la experiencia del cliente o vendedor.
