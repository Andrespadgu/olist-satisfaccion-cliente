# Reporte de Analisis Estadistico - Satisfaccion y Comportamiento en Olist

Analista estadistico. Fecha: 2026-08-21.
Datasets: data/processed/analitico_cliente.csv (98.673 ordenes) y data/processed/analitico_vendedor.csv (3.095 sellers).

---

## Resumen ejecutivo

El factor que domina la satisfaccion del cliente en Olist es, sin ambiguedad, el cumplimiento de la fecha prometida de entrega, y lo hace con una asimetria de aversion a la perdida: entregar tarde destruye la resena mucho mas de lo que entregar antes la mejora. Un cliente al que le llega el pedido tarde tiene 5,9 veces mas probabilidad de dejar 1-2 estrellas que uno al que le llega a tiempo (54,1% vs 9,2%). El tiempo total de entrega tambien pesa, pero menos que el incumplimiento de la promesa.

Hallazgos de las 4 hipotesis no convencionales:

| Hipotesis | Veredicto | Evidencia principal (tamano de efecto) |
|---|---|---|
| H1 - Aversion a la perdida | CONFIRMA | Caida por dia de retraso ~ 10,8x la subida por dia de adelanto; rho retraso -0,54 vs rho adelanto -0,06; tiempo_entrega pierde poco poder al controlar retraso pero no desaparece (rho parcial -0,20). |
| H2 - Buffer / colas | SUGIERE (parcial) | Al condicionar por tiempo de entrega real, el efecto del buffer solo aparece en entregas lentas (rho 0,30 y 0,31 en bandas 22-30 y >30 dias); plano/nulo en entregas rapidas. No es artefacto puro, pero tampoco efecto general. |
| H3 - Flete relativo | REFUTA | rho(ratio_flete/precio, review) = -0,03 (trivial); eps2 por quintiles = 0,001. El ratio no predice mejor que el flete absoluto y ambos son despreciables una vez fijada la puntualidad. |
| H4 - r/K vendedores | CONFIRMA | Tras excluir sellers con n<5, la dispersion (IQR) del desempeno crece al bajar el volumen: IQR de review 0,75 (5-20 pedidos) vs 0,32 (>100); Fligner-Killeen p~4e-38. Los sellers pequenos son mucho mas heterogeneos e impredecibles. |

Advertencia causal permanente: todo lo anterior es correlacion / asociacion observacional, no causalidad. No hay aleatorizacion: los pedidos que llegan tarde pueden diferir sistematicamente de los puntuales (rutas, categorias, sellers). Las conclusiones son sobre asociacion con la resena, no sobre el efecto causal de intervenir sobre la logistica.

Regla metodologica aplicada: las 21 variables numericas son no normales (0% pasa Shapiro-Wilk/Anderson-Darling). Se uso solo estadistica no parametrica (Mann-Whitney U, Kruskal-Wallis, Spearman, Fligner-Killeen, Theil-Sen). Con n grande casi todo p-valor es significativo; las decisiones se tomaron por tamano de efecto y direccion, no por p.

---

## PARTE 1 - Los 11 conceptos estadisticos

Base para lo relacionado con entrega: ordenes delivered con fechas validas = 95.824.

### 1. Probabilidad condicional
P(review<=2 | entregado tarde) = 0,541 vs P(review<=2 | a tiempo) = 0,092.
Riesgo relativo = 5,86. Un retraso multiplica por casi 6 la probabilidad de resena insatisfecha. (n tarde = 7.661; n a tiempo = 88.163.)

### 2. Teorema de Bayes
Invirtiendo la condicional para obtener P(tarde | review = 1):
- Prior P(tarde) = 0,080; verosimilitud P(r1 | tarde) = 0,462; evidencia P(r1) = 0,098.
- Posterior P(tarde | review=1) = 0,379, un lift de 4,7x sobre el prior.
Ver una resena de 1 estrella eleva de 8% a 38% la creencia de que ese pedido llego tarde. Fuerte indicador diagnostico de fallo logistico, aunque no exclusivo.

### 3. Verosimilitud / MLE (freight_value)
Ajuste por maxima verosimilitud de 4 distribuciones (loc=0), n = 97.579:

| Distribucion | Parametros | log-verosimilitud | AIC | KS |
|---|---|---|---|---|
| Log-normal | sigma=0,517; scale=17,33 | -352.352 | 704.710 | 0,111 |
| Gamma | a=3,35; scale=6,05 | -362.634 | 725.273 | 0,156 |
| Weibull | c=1,54; scale=22,78 | -374.793 | 749.592 | 0,161 |
| Exponencial | scale=20,27 | -391.200 | 782.404 | 0,301 |

Mejor ajuste: log-normal (menor AIC y KS). El KS de 0,11 indica colas mas pesadas que la teorica, pero log-normal es la mas plausible.

### 4. Distribuciones parametricas
- tiempo_entrega_dias -> log-normal (sigma=0,68; scale=10,02; AIC 639.313; KS 0,032). Muy buen ajuste.
- price_total -> log-normal (sigma=0,93; scale=85,0; AIC 1.134.326; KS 0,029). Buen ajuste.
Tiempos y montos son log-normales, tipico de procesos multiplicativos positivos sesgados a la derecha.

### 5. Esperanza y varianza
E[review] global = 4,086, Var = 1,816.
- Por estado (>=100 ordenes): peores en el Nordeste - AL 3,76 / MA 3,76 / SE 3,81 (var ~2,3). Mejores - AM 4,21 / PR 4,18 / SP 4,17. Los peores son ademas mas variables.
- Por payment_type: debit_card 4,17 (menor var 1,68) > credit_card 4,09 ~ boleto 4,09 > voucher 4,01 (mayor var 1,96). Diferencias pequenas.

### 6. Independencia y correlacion (Spearman con review)
| Variable | rho |
|---|---|
| tiempo_entrega_dias | -0,235 |
| dias_retraso | -0,176 |
| n_items | -0,107 |
| freight_total | -0,088 |
| distancia_seller_customer_km | -0,065 |
| payment_value | -0,039 |
| ratio_flete_precio | -0,031 |
| price_total | -0,029 |

Todas negativas. Solo tiempo de entrega y retraso superan |rho|>0,15. Matriz completa: outputs/charts/06_matriz_spearman.png.

### 7. Prior y posterior - shrinkage bayesiano por seller
Modelo normal-normal empirico: posterior_i = w_i*ybar_i + (1-w_i)*mu0, con w_i = n_i/(n_i+kappa), kappa = Var_review/tau2 = 1,92 pseudo-observaciones.
- Prior global mu0 = 3,973; tau2 entre sellers = 0,946.
- Shrinkage medio absoluto = 0,285. En bajo volumen (n<=5) = 0,557; en alto volumen (>100) = 0,003.
- Ejemplo: seller con 1 pedido y 5,0 estrellas se corrige a posterior 4,33, evitando premiarlo por un dato anecdotico.
Atiende la advertencia del experto de negocio: no rankear por promedio crudo. Ver outputs/charts/07_shrinkage_prior_posterior.png.

### 8. Entropia de Shannon
- payment_type: H = 1,022 bits (max 2,322; eficiencia 0,44). Baja diversidad, dominado por credit_card (75%).
- product_category: H = 4,725 bits (max 6,150 sobre 71 categorias; eficiencia 0,77). Catalogo diverso.

### 9. Entropia cruzada (clasificador logistico review>=4 vs <=3)
Regresion logistica, CV 5-fold, n = 95.824.
- Log-loss modelo = 0,471 vs baseline (tasa base 0,789) = 0,515 -> reduccion 8,5%.
- AUC = 0,662 (poder moderado).
- Coeficientes estandarizados: tiempo_entrega -0,52 y dias_retraso -0,28 dominan; freight -0,12; ratio y price ~0.
Las derivadas contienen senal real pero moderada; mucha resena queda inexplicada por logistica.

### 10. Divergencia KL (bits, base 2)
- A tiempo (P) vs tarde (Q): KL(P||Q) = 0,810; KL(Q||P) = 1,060 bits. Divergencia grande (a tiempo 62% cinco estrellas; tarde 46% una estrella). Ver outputs/charts/08_KL_review_atiempo_tarde.png.
- SP (P) vs Nordeste (Q): KL(P||Q) = 0,030; KL(NE||SP) = 0,032 bits. Divergencia pequena: la geografia mueve la media pero apenas la forma.
Se reporta la asimetria KL(P||Q) != KL(Q||P); P es la referencia en cada caso.

### 11. Extra - Independencia payment_type x review (chi2)
chi2 = 32,4; dof = 4; p = 1,6e-6; Cramer V = 0,018. p significativo (n~98.700) pero V~0 -> asociacion practicamente nula. Caso didactico de significativo != relevante.

---

## PARTE 2 - Validacion de las 4 hipotesis

### H1 - Aversion a la perdida - CONFIRMA
Filtro: delivered + fechas validas. Ramas adelanto [-15,0) y retraso (0,+15].
- Spearman por rama: adelanto rho = -0,058 (n=58.710, plano) vs retraso rho = -0,538 (n=6.326, fuerte).
- Theil-Sen sobre media diaria: caida -0,156 estrellas/dia de retraso vs subida -0,015/dia de adelanto (el adelanto es incluso levemente negativo -> entregar aun mas temprano no suma). Ratio de asimetria ~ 10,8x. (Con medianas el adelanto satura en 5 -> pendiente 0; por eso se uso la media, documentado en el script.)
- Kruskal-Wallis adelanto/justo/retraso: eps2 = 0,086 (efecto medio); Mann-Whitney adelanto vs retraso: rank-biserial = -0,554 (efecto grande).
- Control de confusion: Spearman parcial de tiempo_entrega controlando dias_retraso baja de -0,235 a -0,203; pierde algo de poder pero no cae bajo 0,10. El tiempo total tiene efecto propio ademas del incumplimiento.

Criterio del plan cumplido: caida/dia >= 2x subida/dia (10,8x). Matiz: tiempo_entrega no perdio todo su poder (-0,20), refinando la hipotesis: importa tanto romper la promesa como el tiempo absoluto, siendo el incumplimiento el mas brutal. Ver outputs/charts/02_H1_review_vs_retraso.png (el codo en retraso=0 es la firma visual).

### H2 - Buffer / colas - SUGIERE (condicional, no general)
buffer = estimada - compra. Como dias_retraso ~ tiempo_entrega - buffer (identidad), se condiciono por bandas de tiempo real:

| Banda tiempo_entrega | rho(buffer, review) | n |
|---|---|---|
| 0-7 dias | -0,014 | 25.933 |
| 8-14 dias | 0,026 | 32.391 |
| 15-21 dias | 0,072 | 13.783 |
| 22-30 dias | 0,297 | 6.401 |
| >30 dias | 0,312 | 4.007 |

Sin condicionar rho = -0,056 (enganoso). El efecto positivo del buffer solo aparece con fuerza en entregas lentas (2 de 5 bandas > 0,10). Interpretacion de colas: cuando el envio sera largo, prometer un plazo holgado protege la resena; en envios rapidos es irrelevante.
Veredicto: no es artefacto algebraico puro (sobrevive en bandas lentas) pero no es efecto general (nulo en la mayoria del volumen, que entrega en <=14 dias). Ver outputs/charts/03_H2_buffer_por_banda.png.

### H3 - Flete relativo - REFUTA
Filtro: delivered + solo puntuales (dias_retraso<=0), n=88.163.
- rho(ratio_flete_precio, review) = -0,032 (trivial).
- Flete absoluto controlando price (parcial): rho = -0,054; absoluto crudo: rho = -0,075. El absoluto predice igual o mejor que el ratio - lo contrario a la hipotesis.
- rho(ratio, distancia) = 0,216 y rho(ratio, n_items) = 0,083: el ratio es proxy de distancia, no de percepcion de abuso.
- Kruskal por quintiles: eps2 = 0,001 (nulo). Review medio baja de 4,34 a 4,25: pendiente real pero insignificante.
Veredicto: no se cumple |rho|>=0,10 ni que el ratio supere al absoluto. Ver outputs/charts/04_H3_review_por_quintil_ratio.png.

### H4 - r/K vendedores - CONFIRMA
En analitico_vendedor, excluyendo n_pedidos<5 (artefacto binomial: proporcion sobre pocos ensayos infla la varianza). Sellers restantes: 1.794.

| Banda volumen | n sellers | mediana %tardio | mediana review | IQR %tardio | IQR review |
|---|---|---|---|---|---|
| 5-20 | 996 | 0,0 | 4,19 | 15,39 | 0,75 |
| 21-100 | 588 | 4,55 | 4,13 | 11,65 | 0,48 |
| >100 | 210 | 5,24 | 4,08 | 9,21 | 0,32 |

- rho(n_pedidos, %tardio) = 0,202; rho(n_pedidos, review) = -0,105 (monotona debil).
- Clave - dispersion: IQR de review cae de 0,75 a 0,32 al subir volumen; IQR de %tardio de 15,4 a 9,2. Fligner-Killeen: review p ~ 3,8e-38 (contundente); %tardio p = 0,039 (debil pero direccional).
Veredicto: la dispersion NO crece con el volumen sino que decrece - patron r/K correcto: los sellers pequenos (estrategia r) son el grupo impredecible y heterogeneo; los grandes (K) convergen a desempeno estable. Sobrevive tras excluir n<5 -> no es artefacto binomial -> hallazgo fuerte. La decision de negocio (monitorear a los pequenos) es la misma. Ver outputs/charts/05_H4_IQR_por_volumen.png.

---

## Limitaciones

1. Observacional, no causal. Ninguna variable fue aleatorizada; posibles confusores no medidos (categoria real, expectativa, historial del seller, estacionalidad).
2. Sesgo de seleccion en resenas. Solo ordenes con resena; los insatisfechos suelen resenar mas (coherente con la forma en J).
3. Nulos. 2.843 ordenes sin fechas validas fuera del analisis logistico; 2.182 sin categoria; 756 sin ratio.
4. Ajustes de distribucion imperfectos. KS de freight 0,11 -> colas mas pesadas que la log-normal teorica.
5. Correlaciones parciales por residuos de rango: aproximacion monotona, no parcial gaussiana.
6. Proxy de satisfaccion del vendedor mide satisfaccion del cliente con ese seller, no del seller.
7. AUC 0,66 / reduccion log-loss 8,5%: la logistica explica solo una fraccion; hay determinantes fuera del dataset.

---

## Graficas generadas
- outputs/charts/01_dist_review_scoreJ.png - distribucion de review_score (forma en J).
- outputs/charts/02_H1_review_vs_retraso.png - review medio vs dias de retraso, linea en 0 (H1).
- outputs/charts/03_H2_buffer_por_banda.png - Spearman(buffer, review) por banda (H2).
- outputs/charts/04_H3_review_por_quintil_ratio.png - review por quintil de ratio flete/precio (H3).
- outputs/charts/05_H4_IQR_por_volumen.png - IQR de desempeno por banda de volumen (H4).
- outputs/charts/06_matriz_spearman.png - matriz de correlacion de Spearman.
- outputs/charts/07_shrinkage_prior_posterior.png - prior vs posterior de sellers (shrinkage).
- outputs/charts/08_KL_review_atiempo_tarde.png - divergencia KL a tiempo vs tarde.

Script reproducible: analisis_inferencial.py (raiz del proyecto). Resultados serializados: outputs/reports/resultados.json.
