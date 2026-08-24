# data/raw/ — dataset crudo de Olist

Esta carpeta debe contener los **9 CSV originales** del *Brazilian E-Commerce Public
Dataset by Olist*. No se versionan en el repositorio (son públicos y pesados); descárgalos
una sola vez y colócalos aquí.

## Cómo obtenerlos

1. Ve a Kaggle: **Brazilian E-Commerce Public Dataset by Olist**
   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Descarga el ZIP y descomprímelo.
3. Copia estos 9 archivos dentro de `data/raw/` (con exactamente estos nombres):

```
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

El pipeline lee estos archivos en **modo solo lectura**: nunca se modifican.

> Licencia del dataset: CC BY-NC-SA 4.0 (uso no comercial, con atribución a Olist).
