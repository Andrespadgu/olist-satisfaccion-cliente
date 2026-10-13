# Informe ejecutivo — Satisfacción del cliente en Olist
**Foco:** el número de ítems por pedido como palanca de mejora · **Datos:** ~96.000 pedidos entregados (Olist 2016–2018) · **Método:** estadística no paramétrica; decisiones por tamaño de efecto, no por p-valor.

## 1. Síntesis
La satisfacción del cliente (calificación 1–5) se explica, ante todo, por **cumplir la promesa de entrega**: la demora frente a la fecha prometida es, con diferencia, el factor más importante. Sin embargo, este informe se centra en un **segundo hallazgo, menos obvio y accionable de inmediato: el número de ítems por pedido**. Es la causa de insatisfacción más fuerte una vez descontado el tiempo, opera por un **canal independiente de la logística** y hoy pasa desapercibida. Es una palanca **barata** que conviene controlar antes de que el tamaño promedio de los pedidos crezca.

## 2. El factor #1 (contexto): la demora en la entrega
- **Es el driver dominante.** Un pedido tardío tiene 5,9× más riesgo de mala calificación: **P(calificación≤2 | llega tarde) = 54%** vs **9%** si llega a tiempo.
- **El daño es asimétrico:** cada día de retraso resta ~**0,16 estrellas**, mientras que adelantarse solo suma ~0,01 (asimetría **10,8×**). Lo que importa no es la velocidad absoluta, sino **no cruzar la fecha prometida**.
- La distancia vendedor–cliente es el motor de esa demora (Spearman **ρ = 0,54**). *Recomendación permanente: gestionar el ETA y usar “cumplimiento de la promesa” como KPI central.*

## 3. Hallazgo central: el número de ítems por pedido
**Qué encontramos.** A más productos en un mismo pedido, peor tiende a ser la calificación (Spearman **ρ = −0,107**). Es la **segunda causa** de insatisfacción tras el tiempo y **la primera de origen no logístico**.

**Por qué merece atención — cuatro razones respaldadas por datos:**

1. **Es un canal independiente del tiempo de entrega.** El número de ítems **no** está correlacionado con la demora (ρ = −0,026) y su efecto **sobrevive** al controlar por tiempo (correlación parcial −0,117). No es “tiempo disfrazado”: es un problema distinto (de **cumplimiento del pedido**, no de velocidad), que se puede atacar por separado.

2. **El efecto condicional es grande, aunque el promedio lo diluya.** Midiendo solo pedidos **entregados a tiempo** (para aislar el efecto): la tasa de clientes muy molestos (1–2★) pasa de **7,5% con 1 ítem** a **23% con 2 ítems** (¡el triple!) y **32% con 5+**. El ρ global parece pequeño (~1% de la varianza) solo porque hoy ~90% de los pedidos son de un único ítem.

3. **Mecanismo: “eslabón más débil”.** Cada ítem adicional es otra oportunidad de que algo falle (dañado, incompleto, empaque distinto, entrega parcial); basta que **un** producto falle para hundir la nota de todo el pedido. La evidencia lo confirma: cuando el pedido llega de **varios vendedores** (paquetes separados), el descontento salta de **21% a 47%**. El efecto observado incluso **supera** al de fallos independientes, señal de fragmentación logística.

4. **Es real, no azar, y su magnitud es sólida (Monte Carlo).** Una **prueba de permutación** (5.000 simulaciones que rompen el vínculo ítems↔insatisfacción) produjo una brecha máxima por azar de **1,05 pp**; la brecha real es de **17,1 pp** (**p < 0,0002**). Un **bootstrap** (4.000 remuestreos) estima **~173 clientes insatisfechos evitables por cada 10.000 pedidos** hoy, con intervalo de confianza 90% **[165–181]** (y **[156–190]** con *cluster bootstrap por vendedor*, más conservador ante correlación intra-vendedor).

**Por qué actuar ahora (proyección).** Hoy el número de ítems explica solo **~1,1% de la varianza** de la satisfacción (ρ² con ρ=−0,107), un efecto pequeño *únicamente* porque ~90% de los pedidos son de un ítem; **no es una cifra fija**. Según las simulaciones, el impacto **escala linealmente** con la proporción de pedidos multi-ítem: si esa proporción crece (más venta cruzada, canastas más grandes), los detractores evitables suben de ~173 hoy a **~513 (si el multi-ítem llega al 30%)** y **~855 (al 50%)** por cada 10.000 pedidos. Es barato prevenirlo ahora; se encarece si se deja crecer.

## 4. Comportamiento del vendedor (mención breve)
El desempeño operativo del vendedor lo explica sobre todo su **volumen** (ρ = 0,20 con el % de despachos tardíos; distancia y región son irrelevantes). Importante para la interpretación: **el vendedor solo controla ~11–14% de su propia calificación**; el resto depende del transportador y del producto. No debe penalizarse al vendedor por demoras del transportista.

## 5. Recomendaciones accionables
1. **Programa de cumplimiento para pedidos multi-ítem** (prioridad de este informe): verificación de completitud antes del despacho, empaque reforzado y **consolidación en un solo envío** cuando sea posible. Independiente de la logística de entrega y de bajo costo.
2. **Marcar como “alto riesgo” los pedidos multi-ítem y multi-vendedor** para control de calidad proactivo; son los del efecto “eslabón más débil”.
3. **Mantener la entrega como prioridad #1:** gestión de ETA, KPI de cumplimiento de promesa y **auditoría logística automática ante cada 1★** (una 1★ es 4,7× más probable si hubo retraso).
4. **Vendedor:** tutelar a los sellers según volumen y usar el **% de despacho tardío** como KPI atribuible; no castigarlos por el transportador.
5. **No invertir** en método de pago, flete ni categoría como palancas de satisfacción: su efecto práctico es nulo (ver Anexo).

---

## Anexo A — Evidencia cuantitativa de los 11 conceptos
| # | Concepto | Aplicación | Resultado |
|---|----------|-----------|-----------|
| 1 | Probabilidad condicional | Mala nota dado retraso | P(≤2★\|tarde)=0,54 vs 0,09 a tiempo (RR 5,9×) |
| 2 | Teorema de Bayes | Diagnóstico de la 1★ | P(tarde\|1★)=0,38 (prior 0,08); lift 4,7× |
| 3 | Verosimilitud / MLE | Ajuste del flete | Log-normal (σ=0,52; escala 17,33); mejor AIC |
| 4 | Distribuciones paramétricas | Tiempo de entrega, precio | Log-normales (KS 0,032 y 0,029) |
| 5 | Esperanza y varianza | Calificación media | E=4,09; Var=1,82; peores estados: AL/MA≈3,76 |
| 6 | Independencia y correlación | Predictores (Spearman) | tiempo −0,235; retraso −0,176; **nº ítems −0,107**; flete −0,088; distancia −0,065; precio −0,03 |
| 7 | Prior y posterior | Shrinkage por vendedor | κ=1,92; seller 1 pedido/5,0★ → posterior 4,33 |
| 8 | Entropía (Shannon) | Diversidad | pago 1,02 bits (efic. 0,44); categoría 4,73 bits (0,77) |
| 9 | Entropía cruzada | Clasificador log. reseña | log-loss 0,471 vs base 0,515 (−8,5%); AUC 0,66 |
| 10 | Divergencia KL | Formas de distribución | a-tiempo‖tarde 0,81 bits; SP‖Nordeste 0,03 bits |
| 11 | χ² (independencia) | Pago × reseña | χ²=32,4; **V de Cramér=0,018** (efecto nulo) |

## Anexo B — Cifras del hallazgo “número de ítems” (pedidos entregados a tiempo)
| Métrica | Valor |
|---|---|
| % detractores (1–2★) por nº de ítems | 1 ítem 7,5% · 2 ítems 23% · 3 ítems 27% · 4 ítems 32% · 5+ 32% |
| % detractores en multi-ítem según vendedores | 1 vendedor 21% · varios 47% |
| Correlación nº ítems ↔ tiempo de entrega | ρ = −0,026 (independiente del tiempo) |
| Correlación parcial (controlando tiempo) | −0,117 (el efecto persiste) |
| Monte Carlo — permutación | brecha real 17,1 pp vs máx. azar 1,05 pp; p < 0,0002 |
| Bootstrap — evitables/10.000 pedidos (hoy) | 173 (IC 90%: 165–181; *cluster* por vendedor 156–190) |
| Proyección si multi-ítem sube a 30% / 50% | ~513 / ~855 evitables por 10.000 pedidos |

*Nota metodológica: todo es asociación observacional (no causal); datos 2016–2018. Los detalles reproducibles están en `outputs/reports/` y el dashboard interactivo en `dashboard/index.html`.*
