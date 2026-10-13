# Lo que aprendimos de la satisfacción del cliente en Olist

*Versión sin corbata: los hallazgos que de verdad mueven la aguja, por qué importan, y
qué herramienta estadística usamos para llegar a cada uno.*

Datos: ~96.000 pedidos entregados de Olist (2016–2018). Todas las cifras de aquí están
recalculadas y verificadas por `reproducir_informe.py` (64/64 checks en verde).
Regla de la casa: decidimos por **tamaño de efecto**, no por p-valores bonitos, y usamos solo
pruebas **no paramétricas** (ninguna variable pasó los tests de normalidad).

---

## Hallazgo 1 — Cumplir la fecha prometida es, de lejos, lo que más importa

**Qué encontramos.** Si un pedido llega tarde, la probabilidad de que el cliente ponga 1 o 2
estrellas se dispara: **54%** cuando llega tarde vs **9%** cuando llega a tiempo. Es casi
**6 veces** más riesgo. Y el daño es asimétrico: cada día de retraso resta ~**0,16 estrellas**,
pero adelantarse apenas suma ~0,01 (una asimetría de **10,8×**). O sea: no te premian por ir
rápido, te castigan por cruzar la fecha prometida. El motor de esas demoras es la **distancia**
vendedor–cliente (correlación de 0,54 con el tiempo de entrega).

**Por qué importa.** Es el driver número uno de la insatisfacción y es sobre el que más palancas
de negocio existen (ETA realista, logística, alertas). El KPI central no debería ser "velocidad"
sino "cumplimiento de la promesa".

**📊 Gráficas:**
- `outputs/charts/02_H1_review_vs_retraso.png` — review medio vs días de retraso. El **"codo"
  en retraso = 0** es la firma visual: la nota se desploma justo al cruzar la fecha prometida.
- `outputs/charts/08_KL_review_atiempo_tarde.png` — las dos distribuciones de calificación
  (a tiempo vs tarde) lado a lado; se ve lo lejos que están (la divergencia KL).

**Conceptos usados:**
- **(1) Probabilidad condicional** → el 54% vs 9% es P(mala calificación | llegó tarde).
- **(2) Teorema de Bayes** → dado un review de 1 estrella, la probabilidad de que hubo retraso
  sube de un 8% base a **38%** (un *lift* de 4,7×). Sirve para diagnosticar hacia atrás.
- **(6) Independencia y correlación** → distancia ↔ tiempo de entrega (ρ = 0,54) y review ↔
  retraso (ρ = −0,18).
- **(10) Divergencia KL** → la distribución de calificaciones "a tiempo" vs "tarde" se separan
  0,81 bits: son mundos distintos, no un matiz.

---

## Hallazgo 2 — El número de ítems por pedido: el problema silencioso ⭐ (el importante)

**Qué encontramos.** A más productos en un mismo pedido, peor la calificación. Mirando **solo
pedidos que llegaron a tiempo** (para quitar el efecto del retraso), la tasa de clientes muy
molestos pasa de **7,5% con 1 ítem** a **23% con 2**, **27% con 3** y **~32% con 4 o más**. Y si
el pedido viene de **varios vendedores** en paquetes separados, el descontento salta de
**21% a 47%**. Lo confirmamos con simulación: una **prueba de permutación** (5.000 barajados)
mostró que el azar nunca produce una brecha mayor a 1,05 puntos, y la real es de **17,1 puntos**
(p < 0,0002). Un **bootstrap** estima ~**173 clientes molestos evitables por cada 10.000 pedidos**
hoy (intervalo honesto, con *cluster bootstrap* por vendedor: **156–190**).

**Por qué importa.** Es la segunda causa de insatisfacción, pero **la primera que no depende de
la logística de entrega** — o sea, se puede atacar por separado y barato (verificar completitud,
empaque, consolidar en un envío). Hoy parece pequeña (**explica solo ~1,1% de la varianza**) solo
porque el 90% de los pedidos son de un ítem; **no es una cifra fija**: escala linealmente. Si la
proporción multi-ítem crece, los detractores evitables suben de ~173 a **~513 (al 30%)** y
**~855 (al 50%)** por cada 10.000 pedidos. Es barato prevenirlo ahora y caro después.

**📊 Gráficas:**
- `outputs/charts/06_matriz_spearman.png` — matriz de correlaciones; ahí se ve el **ρ = −0,107**
  de `n_items` con la calificación (y que flete/pago/precio están en ~0).
- *Interactivas en el dashboard* (`dashboard/index.html`): la **prueba de permutación** (la
  brecha real de 17,1 pp muy fuera de la nube del azar), la **distribución bootstrap** de
  detractores evitables por 10.000 pedidos, y la **proyección** 173 → 513 → 855 según crezca el
  multi-ítem. *(Este hallazgo no tiene un PNG estático propio: sus visuales viven en el dashboard.)*

**Conceptos usados:**
- **(6) Independencia y correlación** → el efecto (ρ = −0,107) **sobrevive** al controlar por
  tiempo (correlación parcial −0,117) y es casi independiente del tiempo de entrega (ρ = −0,026):
  es un canal propio, no "tiempo disfrazado".
- **(1) Probabilidad condicional** → las tasas de detractores por número de ítems (7,5% → 32%).
- **(5) Esperanza y varianza** → el ρ² ≈ 1,1% dice cuánta *varianza* explica hoy; útil para
  entender por qué el promedio lo diluye pero el efecto condicional es enorme.
- **Simulación Monte Carlo** (permutación + bootstrap + cluster bootstrap) → probar que es real,
  medir el impacto en clientes y ponerle un intervalo de confianza creíble.

---

## Hallazgo 3 — No culpes al vendedor por lo que no controla

**Qué encontramos.** Lo que explica que un vendedor despache tarde es sobre todo su **volumen**
(correlación 0,20 con el % de despachos tardíos); la distancia y la región dan casi igual. Y al
mirar cuánto de su propia calificación depende de él, sale un **11–14%**: el resto lo ponen el
transportador y el producto.

**Por qué importa.** Si vas a poner KPIs o incentivos a los vendedores, tienen que ser sobre lo
que **sí** controlan (el % de despacho tardío), no sobre la nota final, que depende en gran parte
de la logística ajena. Penalizar al vendedor por un transportista lento es injusto y no arregla
nada.

**📊 Gráficas:**
- `outputs/charts/07_shrinkage_prior_posterior.png` — prior vs posterior por vendedor: se ve
  cómo las notas de sellers con pocos pedidos se "encogen" hacia el promedio (dejan de valer 5,0).
- `outputs/charts/05_H4_IQR_por_volumen.png` — la dispersión del desempeño **baja** al subir el
  volumen: los vendedores pequeños son el grupo impredecible; los grandes convergen.

**Conceptos usados:**
- **(6) Independencia y correlación** → volumen ↔ % tardío (ρ = 0,20); y los ρ² de sus
  comportamientos controlables (11% y 14%).
- **(7) Prior y posterior (shrinkage bayesiano)** → un vendedor con 1 solo pedido y 5 estrellas
  no "vale" 5,0; su nota se encoge hacia el promedio global (posterior ≈ **4,33**), con un
  pseudo-conteo κ = 1,92. Evita premiar/castigar por ruido de pocos pedidos.

---

## Hallazgo 4 — Dónde NO gastar energía: pago, flete y categoría

**Qué encontramos.** El método de pago prácticamente no se relaciona con la calificación
(**V de Cramér = 0,018**, es decir, efecto nulo aunque el test dé "significativo" por el tamaño
de muestra). El flete y la categoría tampoco mueven la aguja de forma práctica.

**Por qué importa.** Ahorra plata y foco: no tiene sentido lanzar iniciativas de "mejorar
satisfacción" tocando medios de pago o subsidiando flete. El retorno es cero. Mejor concentrar
todo en entrega y en el cumplimiento de pedidos multi-ítem.

**📊 Gráficas:**
- `outputs/charts/04_H3_review_por_quintil_ratio.png` — la calificación media es plana entre
  quintiles de ratio flete/precio: pagar más flete no cambia la satisfacción.
- `outputs/charts/06_matriz_spearman.png` — confirma que flete, precio y pago están todos en ~0.
- `outputs/charts/01_dist_review_scoreJ.png` — distribución en "J" de las calificaciones (contexto:
  mucha gente pone 5 y una minoría ruidosa pone 1), útil para leer todo lo anterior.

**Conceptos usados:**
- **(11) Chi² e independencia (V de Cramér)** → pago × calificación: prueba que la asociación es
  nula en la práctica (V = 0,018).
- **(8) Entropía de Shannon** → el pago casi no aporta información (1,02 bits, eficiencia 0,44):
  poca "sorpresa" que ayude a predecir la nota; la categoría de producto tiene más variedad
  (4,73 bits) pero aun así no discrimina la satisfacción.
- **(3) Verosimilitud / MLE** y **(4) Distribuciones paramétricas** → modelamos el flete y el
  precio y resultaron **log-normales** (mejor AIC; KS 0,032 y 0,029): entender su forma confirma
  que no hay una palanca escondida ahí.
- **(9) Entropía cruzada** → un clasificador de reseñas baja su *log-loss* de 0,515 a 0,471
  (−8,5%, AUC 0,66) usando sobre todo tiempo y retraso; pago/flete/categoría casi no contribuyen.
- **(10) Divergencia KL** → São Paulo vs Nordeste apenas difieren (0,03 bits): la geografía del
  pago/región no cambia la historia.

---

## Resumen: los 11 conceptos, dónde se usó cada uno

| # | Concepto | ¿Dónde nos sirvió? |
|---|----------|--------------------|
| 1 | Probabilidad condicional | H1 (54% vs 9% si llega tarde) · H2 (tasas de detractores por nº de ítems) |
| 2 | Teorema de Bayes | H1 (dado 1★, P(hubo retraso)=38%, lift 4,7×) |
| 3 | Verosimilitud / MLE | H4 (flete ~ log-normal, mejor AIC) |
| 4 | Distribuciones paramétricas | H4 (tiempo de entrega y precio son log-normales, KS 0,03) |
| 5 | Esperanza y varianza | H2 (ρ²≈1,1% de varianza explicada por ítems) · nota global E=4,09, Var=1,82 |
| 6 | Independencia y correlación | H1, H2 y H3 (el caballo de batalla: retraso, ítems, parcial, volumen) |
| 7 | Prior y posterior (shrinkage) | H3 (nota justa de vendedores con pocos pedidos: 5,0 → 4,33) |
| 8 | Entropía (Shannon) | H4 (el pago aporta poca información: 1,02 bits) |
| 9 | Entropía cruzada | H4 (clasificador de reseñas: log-loss 0,515 → 0,471) |
| 10 | Divergencia KL | H1 (a-tiempo vs tarde = 0,81 bits) · H4 (SP vs Nordeste = 0,03 bits) |
| 11 | Chi² / V de Cramér | H4 (pago × reseña: efecto nulo, V=0,018) |

**Extra (fuera de los 11, pero clave para el hallazgo estrella):** simulación **Monte Carlo** —
prueba de permutación, *bootstrap* y *cluster bootstrap* por vendedor— para demostrar que el
efecto del número de ítems es real, medir su impacto y ponerle un intervalo de confianza honesto.

---

### En una frase
> Cuida la **fecha prometida** (lo #1), vigila los **pedidos multi-ítem** antes de que crezcan
> (la palanca barata y silenciosa), sé **justo con los vendedores** (controlan poco) y **no gastes**
> en pago/flete/categoría (no mueven nada).

*Nota: son asociaciones observacionales, no causalidad. Reproducible con `reproducir_informe.py`.*
