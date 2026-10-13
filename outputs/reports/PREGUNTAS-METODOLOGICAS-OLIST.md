# Tres preguntas sobre el método — respondidas con nuestros datos

Respuestas a las preguntas de defensa del análisis, aterrizadas en lo que **encontramos** y en
**cómo lo encontramos** (todas las cifras son reproducibles con `reproducir_informe.py`).

---

## 1. ¿Por qué el Teorema de Bayes y no solo la probabilidad condicional? ¿Qué aportó invertir la probabilidad?

**Lo que ya nos daba la probabilidad condicional (dirección "hacia adelante").**
Calculamos P(reseña mala | llegó tarde): de cada 100 pedidos tardíos, **54** reciben 1–2★
(`P(≤2★|tarde)=0,54`), frente a solo **9** entre los que llegan a tiempo. Eso responde una
pregunta *predictiva*: "si un pedido va a llegar tarde, ¿qué tan probable es que enoje al
cliente?". Útil para anticipar, pero **no** responde la pregunta operativa del día a día.

**Por qué necesitábamos Bayes (dirección "hacia atrás", diagnóstica).**
La pregunta que de verdad importa cuando entra una queja es la inversa: *"me llegó una reseña de
1★, ¿qué probabilidad hay de que detrás haya un retraso?"*. Esa es P(tarde | 1★), y **no** se lee
de la anterior: para invertirla hay que meter la **tasa base** (el *prior*) de que un pedido
llegue tarde, que en Olist es de apenas **8%** (`P(tarde)=0,0799`).

Aplicando Bayes con nuestras verosimilitudes —`P(1★|tarde)=0,46` y `P(1★|a tiempo)=0,066`— la
creencia se actualiza así:

> prior 8% → **posterior P(tarde | 1★) = 38%** (`0,3786`), un **lift de 4,7×**.

**Qué aportó invertir la probabilidad (y que no teníamos antes):**
- **Corrige la falacia de la tasa base.** Es tentador leer "54% de los tardíos se quejan" como si
  "la mayoría de las quejas fueran por retraso". Falso: como llegar tarde es raro (8%), aun así
  solo el **38%** de las 1★ tienen retraso detrás. Bayes evita esa confusión de direcciones.
- **Convierte el hallazgo en una regla accionable.** Una 1★ multiplica por **4,7** la sospecha de
  problema logístico frente al pedido promedio. Eso justifica la recomendación del informe:
  **auditoría logística automática ante cada 1★** — porque ahí es donde más "rinde" mirar.
- **Cuantifica cuánta información aporta la señal.** Pasar de 8% a 38% es el *tamaño del salto de
  aprendizaje* que produce ver una reseña pésima; la probabilidad condicional sola no expresa esa
  actualización de creencia.

*Cómo lo encontramos:* concepto 1 (probabilidad condicional) y concepto 2 (Bayes) en
`analisis_inferencial.py` → `resultados.json` (`c1_prob_cond`, `c2_bayes`).

---

## 2. Al ajustar una distribución al tiempo de entrega y al flete, ¿qué evidencia numérica descartó a la alternativa?

Para cada variable ajustamos por **máxima verosimilitud (MLE)** varias distribuciones candidatas
(log-normal, gamma, Weibull, exponencial) y las comparamos con **dos criterios numéricos**:

- **AIC** (Criterio de Información de Akaike): premia el ajuste y penaliza la complejidad; **menor
  = mejor**. La diferencia de AIC (ΔAIC) es la evidencia clave para descartar.
- **Estadístico KS** (Kolmogorov–Smirnov): distancia máxima entre la distribución teórica y la
  real; **menor = más pegada a los datos**.

**Flete (`freight_value`).** Ganó **log-normal**; la principal alternativa era **gamma**:

| Distribución | AIC | KS |
|---|---|---|
| **log-normal (elegida)** | **704.710** | **0,111** |
| gamma | 725.273 | 0,156 |
| Weibull | 749.592 | 0,161 |
| exponencial | 782.404 | 0,301 |

La descartamos por una **ΔAIC ≈ 20.563 a favor de la log-normal** — una diferencia enorme (como
referencia, una ΔAIC > 10 ya se considera evidencia decisiva). El KS lo confirma: 0,111 vs 0,156.

**Tiempo de entrega (`tiempo_entrega_dias`).** También ganó **log-normal** sobre **gamma**:

| Distribución | AIC | KS |
|---|---|---|
| **log-normal (elegida)** | **639.313** | **0,032** |
| gamma | 642.970 | 0,041 |
| Weibull | 651.410 | 0,061 |

Aquí la ΔAIC ≈ **3.658** y el KS 0,032 vs 0,041: la gamma quedó descartada por peor AIC **y** peor
KS a la vez (el precio, por consistencia, también salió log-normal: KS 0,029 vs 0,100 de gamma).

**En una frase:** no descartamos "a ojo", sino por **AIC** (con diferencias de miles de puntos,
no de decimales) respaldado por el **KS**. La log-normal gana en las dos métricas, y tiene sentido:
tiempos y montes de flete son positivos y con cola larga a la derecha, justo la forma log-normal.

*Cómo lo encontramos:* conceptos 3 (MLE/verosimilitud) y 4 (distribuciones paramétricas) en
`analisis_inferencial.py` → `resultados.json` (`c3_mle_freight`, `c4_distribuciones`).

---

## 3. Si método de pago y categoría de producto NO fueran independientes, ¿qué significaría para Olist?

**Cómo lo medimos.** Usamos el mismo marco de independencia del informe (χ² + **V de Cramér**,
que normaliza el χ² a una escala 0–1 de *fuerza* de asociación, para no dejarnos engañar por el
tamaño de muestra). Al cruzar **método de pago × categoría de producto** sobre 96.490 pedidos:

> χ² = 917, p ≈ 0 (dependencia estadísticamente **significativa**), pero **V de Cramér = 0,056**
> → una asociación **débil**. En la práctica: son *casi* independientes, con un matiz real.

El matiz se ve en los datos: `computers_accessories` se paga con **boleto** más que el promedio
(25,8% vs 19,9% global) y con menos tarjeta (69,6% vs 75,5%), mientras categorías como
`bed_bath_table` van a **crédito** en un 78%.

**Qué significaría —en términos de negocio— que NO fueran independientes** (que es justo lo que
insinúa ese V > 0):

- **El mix de pago depende de qué se compra.** No puedes diseñar "una" estrategia de checkout
  global: cada familia de producto tiene su propio patrón de pago. Categorías caras
  (electrónica, muebles) empujan al **parcelamento** (cuotas con tarjeta) y al boleto; categorías
  baratas/impulso se pagan al contado.
- **Exposición financiera y de riesgo distinta por categoría.** Si el parcelamento se concentra en
  ciertas categorías, ahí se concentran el **costo de financiación**, las tasas de **aprobación/
  rechazo** y el **riesgo de fraude o de impago del boleto**. Dependencia = poder segmentar y
  gestionar ese riesgo por categoría.
- **Palanca de conversión.** Si el pago no es independiente de la categoría, ofrecer el medio de
  pago correcto (p. ej. más cuotas en tickets altos, Pix con descuento en baratos) puede subir la
  conversión **justo donde importa** — una oportunidad que se pierde si asumes independencia.
- **Contraste importante con lo que sí hallamos.** El pago **sí** es prácticamente independiente de
  la *satisfacción* (pago × reseña: **V = 0,018**, efecto nulo). Es decir: el método de pago se
  relaciona un poco con *qué* se compra, pero **nada** con *qué tan contento* queda el cliente. Por
  eso el informe recomienda **no** invertir en medios de pago como palanca de satisfacción, aunque
  sí puedan optimizarse por categoría como palanca de **conversión**.

*Cómo lo encontramos:* concepto 11 (χ² e independencia / V de Cramér). El cruce pago × reseña está
en `resultados.json` (`c11_chi2_pay_review`, V=0,018); el cruce pago × categoría lo calculamos con
el mismo método sobre `analitico_cliente.csv` (χ²=917, V=0,056).

---

*Nota: todas las cifras son asociaciones observacionales (no causales), datos Olist 2016–2018.*
