# -*- coding: utf-8 -*-
"""
================================================================================
 reproducir_informe.py
 Reproducción íntegra y AUTO-VERIFICABLE del "Informe ejecutivo — Satisfacción
 del cliente en Olist" (outputs/reports/informe_ejecutivo_olist.pdf).
================================================================================

Este único archivo ejecuta TODO el pipeline que produjo las cifras del informe,
en orden, desde los CSV crudos de Olist hasta las simulaciones Monte Carlo, y al
final VERIFICA que cada número citado en el informe coincide exactamente con el
resultado recalculado. Sale con código != 0 si algo no cuadra.

--------------------------------------------------------------------------------
PIPELINE (cada paso es un script real del proyecto; aquí solo se orquestan)
--------------------------------------------------------------------------------
  Paso 1  build_derivadas.py       raw/*  -> data/processed/analitico_cliente.csv
                                            + analitico_vendedor.csv
          (limpieza + derivación: reconstruye las tablas analíticas maestras
           desde data/raw, porque la limpieza previa eliminó las llaves de unión.
           Aquí se calculan fechas->datetime, días de retraso, tiempo de entrega,
           distancia vendedor-cliente (haversine sobre geolocation), n_items, etc.)
  Paso 2  pruebas_normalidad.py    Shapiro-Wilk + Anderson-Darling + KS
          (justifica la decisión de usar SOLO pruebas NO paramétricas: 0/21
           variables numéricas son normales)
  Paso 3  analisis_categoricas.py  descripción y validación de variables categóricas
  Paso 4  encoding_features.py     ingeniería de features / encoding (datasets *_encoded)
  Paso 5  analisis_inferencial.py  -> outputs/reports/resultados.json
          (los 11 conceptos estadísticos obligatorios + hipótesis H1-H4;
           Anexo A y los factores §1-§2 del informe salen de aquí)
  Paso 6  analisis_comportamiento.py -> resultados_comportamiento.json
          (comportamiento operativo del vendedor; §4 del informe)
  Paso 7  analisis_dashboard.py    -> resultados_dashboard.json  (H5-H7, D1-D2)
  Paso 8  montecarlo_items.py      -> montecarlo_items.json
          (SIMULACIONES: prueba de permutación + bootstrap i.i.d. + cluster
           bootstrap por vendedor + proyección; §3 y Anexo B del informe)

  (La construcción del dashboard —build_payload.py / build_dashboard.py— es
   presentación, no genera cifras nuevas del informe, y no se incluye aquí.)

--------------------------------------------------------------------------------
USO
--------------------------------------------------------------------------------
  python reproducir_informe.py            # corre el pipeline completo + verifica
  python reproducir_informe.py --verify   # NO recalcula; solo verifica los JSON ya
                                           # presentes en outputs/reports/

Requisitos: numpy, pandas, scipy, matplotlib, statsmodels (los mismos que el
proyecto). Ejecutar desde cualquier directorio: el script fija su propia ruta.
================================================================================
"""
import os
import sys
import json
import time
import runpy

# --- stdout robusto a consolas Windows (cp1252): nunca romper por un carácter ---
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
from scipy import stats

# Rutas ancladas a la ubicación de este archivo (reproducible desde cualquier cwd)
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)                      # los scripts del Paso 2-5 usan rutas relativas
os.environ.setdefault("MPLBACKEND", "Agg")   # matplotlib headless, sin ventanas
PROC = os.path.join(BASE, "data", "processed")
REP = os.path.join(BASE, "outputs", "reports")

STAGES = [
    ("Paso 1  Limpieza + derivación (raw -> tablas analíticas)", "build_derivadas.py"),
    ("Paso 2  Pruebas de normalidad (Shapiro/Anderson/KS)",      "pruebas_normalidad.py"),
    ("Paso 3  Análisis de variables categóricas",                "analisis_categoricas.py"),
    ("Paso 4  Encoding / ingeniería de features",                "encoding_features.py"),
    ("Paso 5  Inferencia: 11 conceptos + hipótesis H1-H4",       "analisis_inferencial.py"),
    ("Paso 6  Comportamiento operativo del vendedor",            "analisis_comportamiento.py"),
    ("Paso 7  Análisis extra del dashboard (H5-H7, D1-D2)",      "analisis_dashboard.py"),
    ("Paso 8  Simulaciones Monte Carlo (permutación+bootstrap)", "montecarlo_items.py"),
]


def banner(txt):
    print("\n" + "=" * 78)
    print(txt)
    print("=" * 78)


def run_pipeline():
    banner("EJECUTANDO PIPELINE COMPLETO (desde data/raw)")
    t_all = time.time()
    for titulo, script in STAGES:
        ruta = os.path.join(BASE, script)
        if not os.path.exists(ruta):
            raise FileNotFoundError("Falta el script del pipeline: " + script)
        print("\n--- %s  [%s] ---" % (titulo, script))
        t0 = time.time()
        # Ejecuta el script tal cual, como si fuera 'python script.py'
        runpy.run_path(ruta, run_name="__main__")
        print("    OK  (%.1fs)" % (time.time() - t0))
    print("\nPipeline completo en %.1fs" % (time.time() - t_all))


# ------------------------------------------------------------------------------
#  VERIFICACIÓN: cada cifra del informe vs. resultado recalculado
# ------------------------------------------------------------------------------
RESULTS = []  # (ok, seccion, concepto, obtenido, esperado_informe, unidad)


def chk(seccion, concepto, obtenido, esperado, tol, unidad=""):
    try:
        ok = obtenido is not None and abs(float(obtenido) - float(esperado)) <= tol
    except (TypeError, ValueError):
        ok = False
    RESULTS.append((ok, seccion, concepto, obtenido, esperado, unidad))
    return ok


def chk_eq(seccion, concepto, obtenido, esperado):
    ok = (obtenido == esperado)
    RESULTS.append((ok, seccion, concepto, obtenido, esperado, ""))
    return ok


def _load(name):
    with open(os.path.join(REP, name), encoding="utf-8") as f:
        return json.load(f)


def verificar():
    banner("VERIFICACIÓN: cifras del informe vs. resultados recalculados")

    r = _load("resultados.json")               # 11 conceptos + H1-H4
    c = _load("resultados_comportamiento.json")  # vendedor (§4)
    m = _load("montecarlo_items.json")         # simulaciones (§3, Anexo B)

    # ---------------- §2  Factor #1: la demora en la entrega ----------------
    c1 = r["c1_prob_cond"]
    chk("§2", "P(<=2 estrellas | llega tarde) = 0,54", c1["P(review<=2 | tarde)"], 0.54, 0.005)
    chk("§2", "P(<=2 estrellas | a tiempo) = 0,09", c1["P(review<=2 | a_tiempo)"], 0.09, 0.005)
    chk("§2", "Riesgo relativo tardío = 5,9x", c1["riesgo_relativo"], 5.9, 0.1)
    h1 = r["H1"]
    chk("§2", "Caída por día de retraso ~0,16 estrellas", abs(h1["theilsen_caida_por_dia_retraso_MEDIA"]), 0.16, 0.01)
    chk("§2", "Asimetría caída/subida = 10,8x", h1["ratio_asimetria_caida/subida_MEDIA"], 10.8, 0.2)

    # distancia -> tiempo de entrega (Spearman 0,54): recomputo inline
    cli = pd.read_csv(os.path.join(PROC, "analitico_cliente.csv"))
    deliv = cli[cli["order_status"] == "delivered"].copy()
    dd = deliv.dropna(subset=["distancia_seller_customer_km", "tiempo_entrega_dias"])
    rho_dist = stats.spearmanr(dd["distancia_seller_customer_km"], dd["tiempo_entrega_dias"]).correlation
    chk("§2", "Spearman distancia<->tiempo entrega = 0,54", rho_dist, 0.54, 0.01)

    # ---------------- Anexo A: los 11 conceptos ----------------
    c2 = r["c2_bayes"]
    chk("AnexoA-2", "Bayes posterior P(tarde|1 estrella) = 0,38", c2["posterior_P(tarde|r1)"], 0.38, 0.01)
    chk("AnexoA-2", "Bayes prior P(tarde) = 0,08", c2["prior_P(tarde)"], 0.08, 0.005)
    chk("AnexoA-2", "Bayes lift = 4,7x", c2["lift"], 4.7, 0.1)

    c3 = r["c3_mle_freight"]
    chk_eq("AnexoA-3", "MLE flete: mejor AIC = lognorm", c3["mejor_AIC"], "lognorm")
    chk("AnexoA-3", "MLE flete lognorm sigma = 0,52", c3["ajustes"]["lognorm"]["params"][0], 0.52, 0.01)
    chk("AnexoA-3", "MLE flete lognorm escala = 17,33", c3["ajustes"]["lognorm"]["params"][2], 17.33, 0.05)

    c4 = r["c4_distribuciones"]
    chk_eq("AnexoA-4", "Tiempo entrega: mejor AIC = lognorm", c4["tiempo_entrega_dias"]["mejor_AIC"], "lognorm")
    chk("AnexoA-4", "Tiempo entrega lognorm KS = 0,032", c4["tiempo_entrega_dias"]["ajustes"]["lognorm"]["KS"], 0.032, 0.002)
    chk_eq("AnexoA-4", "Precio: mejor AIC = lognorm", c4["price_total"]["mejor_AIC"], "lognorm")
    chk("AnexoA-4", "Precio lognorm KS = 0,029", c4["price_total"]["ajustes"]["lognorm"]["KS"], 0.029, 0.002)

    c5 = r["c5_esperanza_var"]
    chk("AnexoA-5", "E[calificación] = 4,09", c5["E_global"], 4.09, 0.01)
    chk("AnexoA-5", "Var[calificación] = 1,82", c5["Var_global"], 1.82, 0.01)
    peores = {d["customer_state"]: d["mean"] for d in c5["por_estado_top_peor"]}
    chk("AnexoA-5", "Peor estado AL ~3,76", peores.get("AL"), 3.76, 0.02)
    chk("AnexoA-5", "Peor estado MA ~3,76", peores.get("MA"), 3.76, 0.02)

    c6 = r["c6_correlacion"]
    chk("AnexoA-6", "Spearman review<->tiempo = -0,235", c6["tiempo_entrega_dias"]["rho"], -0.235, 0.003)
    chk("AnexoA-6", "Spearman review<->retraso = -0,176", c6["dias_retraso"]["rho"], -0.176, 0.003)
    chk("AnexoA-6", "Spearman review<->n_items = -0,107", c6["n_items"]["rho"], -0.107, 0.003)
    chk("AnexoA-6", "Spearman review<->flete = -0,088", c6["freight_total"]["rho"], -0.088, 0.003)
    chk("AnexoA-6", "Spearman review<->distancia = -0,065", c6["distancia_seller_customer_km"]["rho"], -0.065, 0.003)

    c7 = r["c7_shrinkage"]
    chk("AnexoA-7", "Shrinkage kappa (pseudo-conteo) = 1,92", c7["kappa_pseudo_conteo"], 1.92, 0.01)
    chk("AnexoA-7", "Seller 1 pedido/5,0 -> posterior 4,33", c7["ej_sellers_5perfectos"][0]["review_posterior"], 4.33, 0.02)

    c8 = r["c8_entropia"]
    chk("AnexoA-8", "Entropía pago = 1,02 bits", c8["payment_type"]["H_bits"], 1.02, 0.01)
    chk("AnexoA-8", "Eficiencia entropía pago = 0,44", c8["payment_type"]["eficiencia"], 0.44, 0.01)
    chk("AnexoA-8", "Entropía categoría = 4,73 bits", c8["product_category"]["H_bits"], 4.73, 0.01)
    chk("AnexoA-8", "Eficiencia entropía categoría = 0,77", c8["product_category"]["eficiencia"], 0.77, 0.01)

    c9 = r["c9_cross_entropy"]
    chk("AnexoA-9", "Log-loss modelo = 0,471", c9["log_loss_modelo"], 0.471, 0.002)
    chk("AnexoA-9", "Log-loss baseline = 0,515", c9["log_loss_baseline"], 0.515, 0.002)
    chk("AnexoA-9", "Reducción log-loss = 8,5%", c9["reduccion_pct"], 8.5, 0.2)
    chk("AnexoA-9", "AUC = 0,66", c9["AUC"], 0.66, 0.01)

    c10 = r["c10_kl"]
    chk("AnexoA-10", "KL(a-tiempo || tarde) = 0,81 bits", c10["atiempo_vs_tarde"]["KL(atiempo||tarde)_bits"], 0.81, 0.01)
    chk("AnexoA-10", "KL(SP || Nordeste) = 0,03 bits", c10["SP_vs_Nordeste"]["KL(SP||NE)_bits"], 0.03, 0.005)

    c11 = r["c11_chi2_pay_review"]
    chk("AnexoA-11", "Chi2 pago x review = 32,4", c11["chi2"], 32.4, 0.2)
    chk("AnexoA-11", "V de Cramér = 0,018 (efecto nulo)", c11["cramer_v"], 0.018, 0.002)

    # ---------------- §4  Comportamiento del vendedor ----------------
    p6 = c["p6_ranking_driver_despacho_tardio"]["ranking"][0]
    chk("§4", "Spearman volumen<->% despachos tardíos = 0,20", p6["rho"], 0.20, 0.01)
    p7 = c["p7_comportamiento_a_resultado"]
    chk("§4", "Vendedor controla ~11% (rho2 %tardío->review)", p7["spearman_pct_tardio_review"]["rho2"], 0.113, 0.01)
    chk("§4", "Vendedor controla ~14% (rho2 t.despacho->review)", p7["spearman_tiempo_despacho_review"]["rho2"], 0.144, 0.01)

    # ---------------- §3 + Anexo B: hallazgo "número de ítems" ----------------
    # (a) cifras de simulación desde montecarlo_items.json
    chk("§3/AnexoB", "Permutación: brecha observada = 17,1 pp", m["perm"]["observed_pp"], 17.1, 0.1)
    chk("§3/AnexoB", "Permutación: máx. brecha por azar = 1,05 pp", m["perm"]["null_max_pp"], 1.05, 0.1)
    chk("§3/AnexoB", "Permutación: cota p-valor <= 0,0002", m["perm"]["p_upper_bound"], 0.0002, 1e-9)
    chk("§3/AnexoB", "Bootstrap: evitables/10k (mediana) = 173", m["boot_today"]["avoid_today_median"], 173, 2)
    chk("§3/AnexoB", "Bootstrap: IC90 inferior = 165", m["boot_today"]["avoid_today_p05"], 165, 2)
    chk("§3/AnexoB", "Bootstrap: IC90 superior = 181", m["boot_today"]["avoid_today_p95"], 181, 2)
    chk("§3/AnexoB", "Cluster bootstrap: IC90 inferior = 156", m["boot_today_cluster"]["avoid_today_p05"], 156, 2)
    chk("§3/AnexoB", "Cluster bootstrap: IC90 superior = 190", m["boot_today_cluster"]["avoid_today_p95"], 190, 2)
    chk("§3/AnexoB", "Proporción multi-ítem hoy ~10%", m["multi_share_now"], 0.10, 0.01)
    chk_eq("§3/AnexoB", "N pedidos on-time = 88.163", m["n_ontime"], 88163)

    # (b) descriptivos de §3 recalculados INLINE (reproducción independiente)
    ot = deliv[deliv["dias_retraso"] <= 0].copy()
    det = (ot["review_score"].values <= 2).astype(int)
    kit = np.clip(ot["n_items"].values, 1, 5).astype(int)
    tasas = {v: det[kit == v].mean() * 100 for v in [1, 2, 3, 4, 5]}
    chk("§3/AnexoB", "Detractores con 1 ítem = 7,5%", tasas[1], 7.5, 0.5)
    chk("§3/AnexoB", "Detractores con 2 ítems = 23%", tasas[2], 23.0, 1.0)
    chk("§3/AnexoB", "Detractores con 3 ítems = 27%", tasas[3], 27.0, 1.0)
    chk("§3/AnexoB", "Detractores con 4 ítems = 32%", tasas[4], 32.0, 1.5)
    chk("§3/AnexoB", "Detractores con 5+ ítems = 32%", tasas[5], 32.0, 1.5)

    it = pd.read_csv(os.path.join(PROC, "olist_order_items_clean.csv"), usecols=["order_id", "seller_id"])
    nsel = it.groupby("order_id")["seller_id"].nunique()
    ot = ot.assign(n_sel=ot["order_id"].map(nsel))
    mult = ot[ot["n_items"] >= 2]
    tasa_1v = (mult[mult["n_sel"] == 1]["review_score"] <= 2).mean() * 100
    tasa_nv = (mult[mult["n_sel"] > 1]["review_score"] <= 2).mean() * 100
    chk("§3/AnexoB", "Multi-ítem 1 vendedor = 21%", tasa_1v, 21.0, 1.0)
    chk("§3/AnexoB", "Multi-ítem varios vendedores = 47%", tasa_nv, 47.0, 1.5)

    # correlación n_items <-> tiempo de entrega (independiente del tiempo)
    xx = deliv.dropna(subset=["n_items", "tiempo_entrega_dias"])
    rho_it = stats.spearmanr(xx["n_items"], xx["tiempo_entrega_dias"]).correlation
    chk("§3/AnexoB", "Spearman n_items<->tiempo entrega = -0,026", rho_it, -0.026, 0.01)

    # correlación parcial n_items <-> review controlando tiempo (el efecto persiste)
    zz = deliv.dropna(subset=["n_items", "review_score", "tiempo_entrega_dias"])
    rn = stats.rankdata(zz["n_items"]); rr = stats.rankdata(zz["review_score"]); rt = stats.rankdata(zz["tiempo_entrega_dias"])

    def _resid(y, x):
        b = np.polyfit(x, y, 1)
        return y - (b[0] * x + b[1])
    parcial = np.corrcoef(_resid(rn, rt), _resid(rr, rt))[0, 1]
    chk("§3/AnexoB", "Correlación parcial n_items<->review | tiempo = -0,117", parcial, -0.117, 0.01)

    # varianza global explicada por n_items hoy ~1,1% (rho^2), cita del informe
    chk("§3", "n_items explica ~1,1% de la varianza (rho^2)", c6["n_items"]["rho"] ** 2 * 100, 1.1, 0.15)

    # proyección de detractores evitables/10k si crece el multi-ítem (513 / 855)
    p1 = det[kit == 1].mean()
    pmulti = (ot["review_score"].values[ot["n_items"].values >= 2] <= 2).mean()
    exceso = (pmulti - p1) * 10000
    chk("§3", "Proyección evitables/10k si multi-ítem 30% = 513", 0.30 * exceso, 513, 6)
    chk("§3", "Proyección evitables/10k si multi-ítem 50% = 855", 0.50 * exceso, 855, 8)


def imprimir_tabla():
    banner("RESULTADO DE LA VERIFICACIÓN")
    ancho = max(len(x[2]) for x in RESULTS)
    n_ok = 0
    seccion_actual = None
    for ok, seccion, concepto, obtenido, esperado, unidad in RESULTS:
        if seccion != seccion_actual:
            print("\n[%s]" % seccion)
            seccion_actual = seccion
        estado = "OK  " if ok else "FALLA"
        if isinstance(obtenido, float):
            got = "%.4f" % obtenido
        else:
            got = str(obtenido)
        print("  %-5s %-*s  informe=%-10s  recalculado=%s" % (estado, ancho, concepto, esperado, got))
        n_ok += int(ok)
    total = len(RESULTS)
    banner("TOTAL: %d/%d verificaciones OK" % (n_ok, total))
    return n_ok == total


def main():
    solo_verificar = "--verify" in sys.argv or "--solo-verificar" in sys.argv
    if solo_verificar:
        banner("MODO --verify: se omite el pipeline; se verifican los JSON existentes")
        faltan = [f for f in ("resultados.json", "resultados_comportamiento.json", "montecarlo_items.json")
                  if not os.path.exists(os.path.join(REP, f))]
        if faltan:
            print("Faltan JSON necesarios: %s. Ejecuta sin --verify para generarlos." % faltan)
            sys.exit(2)
    else:
        run_pipeline()

    verificar()
    todo_ok = imprimir_tabla()
    if not todo_ok:
        print("\nATENCIÓN: hay verificaciones en FALLA. Revisar antes de citar el informe.")
        sys.exit(1)
    print("\nTodas las cifras del informe quedaron reproducidas y verificadas.")
    sys.exit(0)


if __name__ == "__main__":
    main()
