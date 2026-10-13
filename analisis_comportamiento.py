# -*- coding: utf-8 -*-
"""
Analisis del COMPORTAMIENTO OPERATIVO del vendedor Olist (no su satisfaccion).
Solo pruebas NO parametricas. Decision por TAMANO DE EFECTO.
Excluye sellers con n_pedidos < 5 (artefacto de denominador).
NaN nunca se imputa a 0: se descarta por par de variables (pairwise).
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

RAW = r"C:\Users\ANDRES\Desktop\Maquinas no supervisadas\data\processed\analitico_vendedor.csv"
OUT = r"C:\Users\ANDRES\Desktop\Maquinas no supervisadas\outputs\reports\resultados_comportamiento.json"

MAP_REGION = {}
for reg, estados in {
    "Norte": "AM PA AC RO RR AP TO",
    "Nordeste": "MA PI CE RN PB PE AL SE BA",
    "Centro-Oeste": "MT MS GO DF",
    "Sudeste": "SP RJ MG ES",
    "Sur": "PR SC RS",
}.items():
    for e in estados.split():
        MAP_REGION[e] = reg


def r(x, nd=4):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    return round(float(x), nd)


def spearman(a, b):
    """Spearman con descarte pairwise de NaN. Devuelve rho, p, n, rho2."""
    m = np.isfinite(a) & np.isfinite(b)
    n = int(m.sum())
    if n < 3:
        return {"rho": None, "p": None, "n": n, "rho2": None}
    rho, p = stats.spearmanr(a[m], b[m])
    return {"rho": r(rho), "p": r(p, 8), "n": n, "rho2": r(rho**2, 6)}


def efecto_rho(rho):
    a = abs(rho)
    if a < 0.10:
        return "insignificante"
    if a < 0.30:
        return "pequeno"
    if a < 0.50:
        return "mediano"
    return "grande"


def efecto_eps2(e):
    # Cohen aprox para eps2/eta2
    if e < 0.01:
        return "insignificante"
    if e < 0.06:
        return "pequeno"
    if e < 0.14:
        return "mediano"
    return "grande"


def kruskal_eps2(groups):
    """Kruskal-Wallis + epsilon^2. groups: lista de arrays (ya sin NaN)."""
    groups = [g[np.isfinite(g)] for g in groups]
    groups = [g for g in groups if len(g) > 0]
    N = sum(len(g) for g in groups)
    k = len(groups)
    if k < 2 or N <= k:
        return {"H": None, "p": None, "eps2": None, "n": N, "k": k}
    H, p = stats.kruskal(*groups)
    eps2 = (H - k + 1) / (N - k)
    return {"H": r(H, 3), "p": r(p, 8), "eps2": r(eps2, 6),
            "efecto": efecto_eps2(eps2), "n": N, "k": k}


# ---------- Carga y filtro ----------
df = pd.read_csv(RAW)
n_total = len(df)
df = df[df["n_pedidos"] >= 5].copy()
n_filtrado = len(df)
df["region"] = df["seller_state"].map(MAP_REGION)

# Bandas de volumen fijas pedidas
def banda_fija(n):
    if n <= 20:
        return "5-20"
    if n <= 100:
        return "21-100"
    return ">100"

df["banda_vol"] = df["n_pedidos"].apply(banda_fija)

# Deciles de n_pedidos (para KW monotonicidad / saturacion)
df["decil_vol"] = pd.qcut(df["n_pedidos"], 10, labels=False, duplicates="drop")

res = {
    "meta": {
        "n_sellers_total": n_total,
        "n_sellers_tras_excluir_n<5": n_filtrado,
        "n_excluidos": n_total - n_filtrado,
        "regla_exclusion": "n_pedidos < 5 (proporciones sobre pocos pedidos = ruido)",
        "nan_policy": "pairwise deletion; NaN nunca imputado a 0",
        "solo_no_parametricas": True,
        "decision_por": "tamano de efecto (|rho|, rho2, eps2)",
    }
}

pct_tard = df["pct_despachos_tardios"].to_numpy(float)
tiempo = df["tiempo_despacho_promedio_dias"].to_numpy(float)
pct_canc = df["pct_cancelados"].to_numpy(float)
npe = df["n_pedidos"].to_numpy(float)
dist = df["distancia_promedio_a_clientes"].to_numpy(float)
ratio = df["ratio_flete_precio_promedio"].to_numpy(float)
review = df["review_score_promedio"].to_numpy(float)

# ---------- 1. SATURACION POR VOLUMEN (H1 colas) ----------
sp_np_tard = spearman(npe, pct_tard)
sp_np_tiempo = spearman(npe, tiempo)

# KW de pct_tardios entre deciles de volumen
grupos_dec = [df.loc[df["decil_vol"] == d, "pct_despachos_tardios"].to_numpy(float)
              for d in sorted(df["decil_vol"].dropna().unique())]
kw_dec_tard = kruskal_eps2(grupos_dec)

# medianas de pct_tardio por decil (para ver monotonia vs codo)
med_por_decil = []
for d in sorted(df["decil_vol"].dropna().unique()):
    sub = df.loc[df["decil_vol"] == d]
    med_por_decil.append({
        "decil": int(d),
        "n_sellers": int(len(sub)),
        "npedidos_min": int(sub["n_pedidos"].min()),
        "npedidos_max": int(sub["n_pedidos"].max()),
        "med_pct_tardio": r(sub["pct_despachos_tardios"].median(), 3),
        "med_tiempo_despacho": r(sub["tiempo_despacho_promedio_dias"].median(), 3),
    })

# medianas por banda fija pedida
med_por_banda = {}
for b in ["5-20", "21-100", ">100"]:
    sub = df.loc[df["banda_vol"] == b]
    med_por_banda[b] = {
        "n_sellers": int(len(sub)),
        "med_pct_tardio": r(sub["pct_despachos_tardios"].median(), 3),
        "med_tiempo_despacho": r(sub["tiempo_despacho_promedio_dias"].median(), 3),
    }

# Test de monotonia: comparar salto 5-20 -> 21-100 vs 21-100 -> >100
res["p1_saturacion_volumen"] = {
    "spearman_npedidos_pct_tardio": {**sp_np_tard, "efecto": efecto_rho(sp_np_tard["rho"] or 0)},
    "spearman_npedidos_tiempo_despacho": {**sp_np_tiempo, "efecto": efecto_rho(sp_np_tiempo["rho"] or 0)},
    "kruskal_pct_tardio_entre_deciles": kw_dec_tard,
    "medianas_pct_tardio_por_decil": med_por_decil,
    "medianas_por_banda": med_por_banda,
}

# ---------- 2. DISPERSION r/K sobre COMPORTAMIENTO ----------
grupos_banda_tard = [df.loc[df["banda_vol"] == b, "pct_despachos_tardios"].dropna().to_numpy(float)
                     for b in ["5-20", "21-100", ">100"]]
fk = stats.fligner(*grupos_banda_tard)
iqr_por_banda = {}
for b in ["5-20", "21-100", ">100"]:
    x = df.loc[df["banda_vol"] == b, "pct_despachos_tardios"].dropna().to_numpy(float)
    q1, q3 = np.percentile(x, [25, 75])
    iqr_por_banda[b] = {"IQR": r(q3 - q1, 3), "q1": r(q1, 3), "q3": r(q3, 3),
                        "std": r(x.std(ddof=1), 3), "n": int(len(x))}
res["p2_dispersion_rK_comportamiento"] = {
    "fligner_killeen_pct_tardio_entre_bandas": {"stat": r(fk.statistic, 3), "p": r(fk.pvalue, 8)},
    "IQR_pct_tardio_por_banda": iqr_por_banda,
    "interpretacion": "Si IQR cae al subir volumen -> la variabilidad del cumplimiento se reduce (estrategia K)."
}

# ---------- 3. DISTANCIA -> DESPACHO (H2) ----------
sp_dist_tiempo = spearman(dist, tiempo)
sp_dist_tard = spearman(dist, pct_tard)
# dentro de SP
sp = df[df["seller_state"] == "SP"]
sp_dist_tiempo_sp = spearman(sp["distancia_promedio_a_clientes"].to_numpy(float),
                             sp["tiempo_despacho_promedio_dias"].to_numpy(float))
sp_dist_tard_sp = spearman(sp["distancia_promedio_a_clientes"].to_numpy(float),
                           sp["pct_despachos_tardios"].to_numpy(float))
res["p3_distancia_despacho"] = {
    "bruto": {
        "spearman_distancia_tiempo_despacho": {**sp_dist_tiempo, "efecto": efecto_rho(sp_dist_tiempo["rho"] or 0)},
        "spearman_distancia_pct_tardio": {**sp_dist_tard, "efecto": efecto_rho(sp_dist_tard["rho"] or 0)},
    },
    "dentro_de_SP": {
        "n_sellers_SP": int(len(sp)),
        "spearman_distancia_tiempo_despacho": {**sp_dist_tiempo_sp, "efecto": efecto_rho(sp_dist_tiempo_sp["rho"] or 0)},
        "spearman_distancia_pct_tardio": {**sp_dist_tard_sp, "efecto": efecto_rho(sp_dist_tard_sp["rho"] or 0)},
    },
    "interpretacion": "La distancia es a cliente final; el despacho (seller->transportador) NO deberia depender de ella si el efecto es insignificante."
}

# ---------- 4. CANCELACION vs TARDANZA (H3) ----------
sp_canc_tard = spearman(pct_canc, pct_tard)
grupos_banda_canc = [df.loc[df["banda_vol"] == b, "pct_cancelados"].dropna().to_numpy(float)
                     for b in ["5-20", "21-100", ">100"]]
kw_canc_banda = kruskal_eps2(grupos_banda_canc)
med_canc_banda = {b: {"med_pct_cancelados": r(df.loc[df["banda_vol"] == b, "pct_cancelados"].median(), 3),
                      "n": int(df.loc[df["banda_vol"] == b, "pct_cancelados"].notna().sum())}
                  for b in ["5-20", "21-100", ">100"]}
res["p4_cancelacion_vs_tardanza"] = {
    "spearman_pct_cancelados_pct_tardio": {**sp_canc_tard, "efecto": efecto_rho(sp_canc_tard["rho"] or 0)},
    "kruskal_pct_cancelados_entre_bandas_vol": kw_canc_banda,
    "medianas_pct_cancelados_por_banda": med_canc_banda,
    "interpretacion": "rho>0 => mismo 'mal vendedor'. rho<=0/nulo => estrategias sustitutas (cancela en vez de despachar tarde)."
}

# ---------- 5. GEOGRAFIA ----------
regiones = [x for x in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sur"]
            if (df["region"] == x).any()]
g_tard = [df.loc[df["region"] == x, "pct_despachos_tardios"].dropna().to_numpy(float) for x in regiones]
g_tiempo = [df.loc[df["region"] == x, "tiempo_despacho_promedio_dias"].dropna().to_numpy(float) for x in regiones]
kw_geo_tard = kruskal_eps2(g_tard)
kw_geo_tiempo = kruskal_eps2(g_tiempo)
med_region = {}
for x in regiones:
    sub = df[df["region"] == x]
    med_region[x] = {
        "n_sellers": int(len(sub)),
        "med_pct_tardio": r(sub["pct_despachos_tardios"].median(), 3),
        "med_tiempo_despacho": r(sub["tiempo_despacho_promedio_dias"].median(), 3),
    }
res["p5_geografia"] = {
    "kruskal_pct_tardio_entre_regiones": kw_geo_tard,
    "kruskal_tiempo_despacho_entre_regiones": kw_geo_tiempo,
    "medianas_por_region": med_region,
}

# ---------- 6. RANKING: que explica el despacho tardio ----------
ranking = []
for var, arr in [("n_pedidos", npe), ("distancia_promedio_a_clientes", dist),
                 ("ratio_flete_precio_promedio", ratio)]:
    s = spearman(arr, pct_tard)
    ranking.append({"var": var, "metrica": "rho2_spearman", "valor": s["rho2"],
                    "rho": s["rho"], "p": s["p"], "n": s["n"], "efecto": efecto_rho(s["rho"] or 0)})
ranking.append({"var": "region", "metrica": "eps2_kruskal", "valor": kw_geo_tard["eps2"],
                "H": kw_geo_tard["H"], "p": kw_geo_tard["p"], "n": kw_geo_tard["n"],
                "efecto": kw_geo_tard["efecto"]})
ranking_sorted = sorted(ranking, key=lambda z: (z["valor"] or 0), reverse=True)
res["p6_ranking_driver_despacho_tardio"] = {
    "ranking": ranking_sorted,
    "driver_mas_fuerte": ranking_sorted[0],
    "nota": "n_pedidos y distancia usan rho2 (Spearman); region usa eps2 (Kruskal). Ambas metricas comparten escala 0-1 de varianza explicada."
}

# ---------- 7. COMPORTAMIENTO -> RESULTADO ----------
sp_tard_review = spearman(pct_tard, review)
sp_tiempo_review = spearman(tiempo, review)
sp_canc_review = spearman(pct_canc, review)
res["p7_comportamiento_a_resultado"] = {
    "spearman_pct_tardio_review": {**sp_tard_review, "efecto": efecto_rho(sp_tard_review["rho"] or 0)},
    "spearman_tiempo_despacho_review": {**sp_tiempo_review, "efecto": efecto_rho(sp_tiempo_review["rho"] or 0)},
    "spearman_pct_cancelados_review": {**sp_canc_review, "efecto": efecto_rho(sp_canc_review["rho"] or 0)},
    "pct_varianza_review_por_comportamiento_tardio": r((sp_tard_review["rho2"] or 0) * 100, 3),
    "interpretacion": "rho2 del pct_tardio->review = cota de cuanto del review depende del comportamiento CONTROLABLE del vendedor (resto: transportador, producto, expectativa)."
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

print("OK ->", OUT)
print("n sellers tras excluir n<5:", n_filtrado, "de", n_total)
print("--- P1 npedidos->pct_tardio:", res["p1_saturacion_volumen"]["spearman_npedidos_pct_tardio"])
print("--- P3 distancia->tiempo (bruto):", res["p3_distancia_despacho"]["bruto"]["spearman_distancia_tiempo_despacho"])
print("--- P4 canc vs tard:", res["p4_cancelacion_vs_tardanza"]["spearman_pct_cancelados_pct_tardio"])
print("--- P6 driver:", res["p6_ranking_driver_despacho_tardio"]["driver_mas_fuerte"])
print("--- P7 tard->review:", res["p7_comportamiento_a_resultado"]["spearman_pct_tardio_review"])
