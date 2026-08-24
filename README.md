# Análisis de satisfacción del cliente en Olist

Análisis estadístico-probabilístico de qué factores explican la **satisfacción del cliente**
(y el comportamiento operativo del vendedor) en el marketplace brasileño **Olist**, a partir de
~96.000 pedidos entregados entre 2016 y 2018.

El resultado principal es el **informe ejecutivo** (`outputs/reports/informe_ejecutivo_olist.pdf`)
y todo el código para reproducirlo desde cero está en este repositorio: **cada cifra citada en el
informe se recalcula y se verifica automáticamente** al correr `reproducir_informe.py`.

---

## Hallazgos principales

1. **Cumplir la fecha prometida es el factor #1.** Un pedido tardío tiene ~6× más riesgo de mala
   calificación: P(1–2★ | tarde) = 54% vs. 9% a tiempo. El daño es asimétrico (cada día de retraso
   resta ~0,16★; adelantarse casi no suma).
2. **El número de ítems por pedido es la causa silenciosa.** A tiempo, los detractores pasan de
   7,5% (1 ítem) a ~32% (5+). Es la primera causa **no logística** y hoy explica solo ~1,1% de la
   varianza *porque* el 90% de los pedidos son de un ítem; escala si la canasta crece.
3. **El vendedor controla poco (~11–14%) de su calificación:** el resto depende del transportador
   y del producto. Su desempeño lo explica sobre todo el volumen.
4. **Pago, flete y categoría no mueven la satisfacción** (V de Cramér ≈ 0,018): no son palancas.

Los 11 conceptos de probabilidad/estadística usados (probabilidad condicional, Bayes, MLE,
distribuciones paramétricas, esperanza/varianza, correlación, prior/posterior, entropía, entropía
cruzada, divergencia KL, χ²) están detallados en el Anexo A del informe. Metodología: solo pruebas
**no paramétricas** (ninguna variable pasó los tests de normalidad) y decisión por **tamaño de
efecto**, no por p-valor.

---

## Cómo reproducir

Requisitos: **Python 3.10+**.

```bash
# 1) Instalar dependencias
pip install -r requirements.txt

# 2) Descargar el dataset de Olist y colocar los 9 CSV en data/raw/
#    (instrucciones en data/raw/README.md)

# 3) Ejecutar todo el pipeline y verificar las 64 cifras del informe
python reproducir_informe.py
```

Al terminar imprime una tabla `OK/FALLA` y `TOTAL: 64/64 verificaciones OK`. Sale con código
distinto de 0 si algo no cuadra.

- `python reproducir_informe.py --verify` verifica los JSON ya generados sin recalcular.
- El pipeline **núcleo** (limpieza/derivación → inferencia → comportamiento → simulaciones) produce
  todas las cifras citadas usando **solo** `data/raw/`. Los pasos opcionales
  (normalidad/categóricas/encoding) se omiten automáticamente si no están los `data/processed/*_clean.csv`.

---

## Estructura

```
reproducir_informe.py        Orquesta el pipeline y verifica cada cifra del informe.
build_derivadas.py           Limpieza + derivación: raw -> tablas analíticas maestras.
analisis_inferencial.py      Los 11 conceptos estadísticos + hipótesis (Anexo A, §1-2).
analisis_comportamiento.py   Comportamiento operativo del vendedor (§4).
montecarlo_items.py          Simulaciones: permutación + bootstrap + cluster bootstrap (§3).
pruebas_normalidad.py        (opcional) Justifica el uso de pruebas no paramétricas.
analisis_categoricas.py      (opcional) Análisis de variables categóricas.
encoding_features.py         (opcional) Ingeniería de features / encoding.
docs/                        Diccionario de variables y mapeo a los 11 conceptos.
outputs/reports/             Informe ejecutivo (PDF + LaTeX).
data/raw/                    Aquí van los 9 CSV de Olist (no versionados; ver su README).
```

---

## Datos y licencia

- **Datos:** *Brazilian E-Commerce Public Dataset by Olist* (Kaggle), licencia **CC BY-NC-SA 4.0**
  (uso no comercial, con atribución a Olist). No se redistribuyen en este repo.
- **Código:** libre para uso educativo y de investigación.

*Nota: todos los resultados son asociaciones observacionales, no relaciones causales.*
