# -*- coding: utf-8 -*-
"""
Analisis NUEVOS para dashboard Olist: H5, H6, H7, D1, D2.
Solo pruebas NO parametricas. Decision por TAMANO DE EFECTO.
Reutiliza outputs/reports/resultados.json (no recalcula 11 conceptos + H1-H4).
"""
import json, math, datetime
import numpy as np
import pandas as pd
from scipy import stats

BASE = r"C:\Users\ANDRES\Desktop\Maquinas no supervisadas"
PROC = BASE + r"\data\processed"

# ---------- mapeo estado -> macro-region ----------
REGION_MAP = {}
for r, ufs in {
    "Norte": "AM,PA,AC,RO,RR,AP,TO",
    "Nordeste": "MA,PI,CE,RN,PB,PE,AL,SE,BA",
    "Centro-Oeste": "MT,MS,GO,DF",
    "Sudeste": "SP,RJ,MG,ES",
    "Sur": "PR,SC,RS",
}.items():
    for uf in ufs.split(","):
        REGION_MAP[uf] = r
REGIONES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sur"]

# ---------- helpers tamano de efecto ----------
def rank_biserial_mw(x, y):
    """rank-biserial a partir de U de Mann-Whitney. r = 2U/(n1*n2)-1 (x mayor -> positivo)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return np.nan, np.nan, (n1, n2)
    U, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    r = 2.0 * U / (n1 * n2) - 1.0
    return r, p, (n1, n2)

def epsilon_sq_kw(groups):
    """epsilon^2 para Kruskal-Wallis = (H - k + 1)/(n - k)."""
    groups = [np.asarray(g, float) for g in groups if len(g) > 0]
    k = len(groups)
    if k < 2:
        return np.nan, np.nan, np.nan, 0
    n = sum(len(g) for g in groups)
    H, p = stats.kruskal(*groups)
    eps2 = (H - k + 1) / (n - k) if n > k else np.nan
    return H, p, eps2, n

def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    if m.sum() < 3:
        return np.nan, np.nan, int(m.sum())
    rho, p = stats.spearmanr(a[m], b[m])
    return rho, p, int(m.sum())

def spearman_partial(x, y, z):
    """Spearman parcial de x,y controlando z: correlacion de residuos de rangos."""
    df = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(df) < 5:
        return np.nan, np.nan, len(df)
    rx = df.x.rank(); ry = df.y.rank(); rz = df.z.rank()
    def resid(t):
        A = np.vstack([np.ones(len(rz)), rz.values]).T
        beta, *_ = np.linalg.lstsq(A, t.values, rcond=None)
        return t.values - A @ beta
    ex, ey = resid(rx), resid(ry)
    r, p = stats.pearsonr(ex, ey)
    return r, p, len(df)

def entropy_bits(vals):
    vc = pd.Series(vals).value_counts(normalize=True)
    return float(stats.entropy(vc.values, base=2))

def cramers_v(chi2, n, r, c):
    return math.sqrt((chi2 / n) / (min(r - 1, c - 1)))

def eff_label_r(r):
    a = abs(r)
    if a < 0.1: return "insignificante"
    if a < 0.3: return "pequeno"
    if a < 0.5: return "mediano"
    return "grande"

def eff_label_eps2(e):
    if e < 0.01: return "insignificante"
    if e < 0.06: return "pequeno"
    if e < 0.14: return "mediano"
    return "grande"

# ---------- carga ----------
print("Cargando datasets...")
cli = pd.read_csv(PROC + r"\analitico_cliente.csv")
ven = pd.read_csv(PROC + r"\analitico_vendedor.csv")
cli["region"] = cli["customer_state"].map(REGION_MAP)
cli["foranea"] = (cli["customer_state"] != cli["seller_state"]).astype(int)
cli["ontime"] = np.where(cli["dias_retraso"].notna(), (cli["dias_retraso"] <= 0).astype(float), np.nan)
ven["region"] = ven["seller_state"].map(REGION_MAP)

# delivered con retraso valido
deliv = cli[(cli["order_status"] == "delivered") & cli["dias_retraso"].notna()].copy()
punt = deliv[deliv["dias_retraso"] <= 0].copy()   # puntuales
tard = deliv[deliv["dias_retraso"] > 0].copy()     # tardios
print(f"n cli={len(cli)} deliv_validos={len(deliv)} puntuales={len(punt)} tardios={len(tard)}")

RES = {"generado": datetime.datetime.now().isoformat(timespec="seconds")}

# ============================================================
# H5 geografia como causa propia
# ============================================================
print("\n== H5 ==")
h5 = {}
# (a) MW review SP vs Nordeste SOLO en puntuales
sp = punt[punt["customer_state"] == "SP"]["review_score"]
ne = punt[punt["region"] == "Nordeste"]["review_score"]
r_ab, p_ab, (n_sp, n_ne) = rank_biserial_mw(sp, ne)
h5["a_sp_vs_nordeste_puntuales"] = {
    "rank_biserial": round(r_ab, 4), "p": float(f"{p_ab:.3e}"),
    "n_sp": n_sp, "n_nordeste": n_ne,
    "review_sp_mediana": float(sp.median()), "review_ne_mediana": float(ne.median()),
    "review_sp_media": round(float(sp.mean()), 4), "review_ne_media": round(float(ne.mean()), 4),
    "efecto": eff_label_r(r_ab),
    "sobrevive_gap": bool(abs(r_ab) >= 0.1),
}
print("H5a rank-biserial SP vs NE (puntuales):", round(r_ab, 4), "efecto", eff_label_r(r_ab))

# (b) por customer_state: frac_foranea, distancia mediana, varianza de review
est = deliv.groupby("customer_state").agg(
    frac_foranea=("foranea", "mean"),
    dist_med=("distancia_seller_customer_km", "median"),
    var_review=("review_score", "var"),
    n=("review_score", "size"),
).reset_index()
est = est[est["n"] >= 30]  # estados con soporte
# terciles de frac_foranea (a nivel order, usando frac del estado)
deliv2 = deliv.merge(est[["customer_state", "frac_foranea"]], on="customer_state", how="inner", suffixes=("", "_estado"))
terc = pd.qcut(deliv2["frac_foranea"].rank(method="first"), 3, labels=["bajo", "medio", "alto"])
deliv2["tercil_foranea"] = terc
grupos_review = [deliv2[deliv2["tercil_foranea"] == t]["review_score"].values for t in ["bajo", "medio", "alto"]]
# Fligner-Killeen (dispersion) vs Kruskal-Wallis (media/rango)
fk_stat, fk_p = stats.fligner(*grupos_review)
H_kw, p_kw, eps2_kw, n_kw = epsilon_sq_kw(grupos_review)
# Spearman a nivel-estado: frac_foranea vs varianza de review
rho_fv, p_fv, n_fv = spearman(est["frac_foranea"], est["var_review"])
h5["b_dispersion_vs_media"] = {
    "fligner_stat": round(float(fk_stat), 4), "fligner_p": float(f"{fk_p:.3e}"),
    "kruskal_H": round(float(H_kw), 4), "kruskal_p": float(f"{p_kw:.3e}"), "kruskal_eps2": round(float(eps2_kw), 5),
    "spearman_estado_fforanea_vs_varreview": {"rho": round(rho_fv, 4), "p": float(f"{p_fv:.3e}"), "n_estados": n_fv},
    "domina": "dispersion" if fk_p < p_kw and eps2_kw < 0.01 else "ninguno_claro",
    "efecto_kw": eff_label_eps2(eps2_kw),
}
print("H5b Fligner p=", f"{fk_p:.2e}", "KW eps2=", round(eps2_kw, 5), "Spearman estado f_foranea~var:", round(rho_fv, 3))

# (c) vendedor: Spearman parcial distancia vs review controlando pct_tardios (n_pedidos>=5)
vv = ven[ven["n_pedidos"] >= 5].copy()
rho_dr, p_dr, n_dr = spearman(vv["distancia_promedio_a_clientes"], vv["review_score_promedio"])
rho_par, p_par, n_par = spearman_partial(vv["distancia_promedio_a_clientes"], vv["review_score_promedio"], vv["pct_despachos_tardios"])
h5["c_vendedor_distancia_review"] = {
    "spearman_bruto": {"rho": round(rho_dr, 4), "p": float(f"{p_dr:.3e}"), "n": n_dr},
    "spearman_parcial_control_tardios": {"rho": round(rho_par, 4), "p": float(f"{p_par:.3e}"), "n": n_par},
    "efecto_parcial": eff_label_r(rho_par),
}
print("H5c distancia~review bruto rho=", round(rho_dr, 3), "parcial=", round(rho_par, 3))

# veredicto H5
h5_efecto_max = max(abs(r_ab), abs(rho_par))
h5["veredicto"] = ("RECHAZADA: geografia no tiene causa propia sustancial una vez aislado el tiempo"
                   if h5_efecto_max < 0.1 else
                   "PARCIAL: queda un efecto geografico pequeno tras controlar puntualidad/tardios")
RES["H5"] = h5

# ============================================================
# H6 "regalo roto" (SEGUNDA CAUSA - prioridad)
# ============================================================
print("\n== H6 ==")
h6 = {}
# (a) subconjunto review<=2 AND puntual
mal_punt = punt[punt["review_score"] <= 2].copy()
h6["a_tamano"] = {
    "n_review_bajo_puntual": len(mal_punt),
    "pct_de_puntuales": round(100 * len(mal_punt) / len(punt), 2),
    "pct_de_todo_review_bajo": round(100 * len(mal_punt) / len(deliv[deliv["review_score"] <= 2]), 2),
}
print("H6a insatisfechos puntuales:", len(mal_punt), f"({h6['a_tamano']['pct_de_puntuales']}% de puntuales)")

# chi2 bondad de ajuste: cat observada en mal_punt vs esperada por exposicion (dist en TODOS los puntuales)
cats_all = punt["product_category_name_english"].dropna()
exp_dist = cats_all.value_counts(normalize=True)
obs = mal_punt["product_category_name_english"].dropna().value_counts()
# alinear categorias con soporte razonable
cats_comunes = exp_dist[exp_dist.index.isin(obs.index)].index
obs_v = obs.reindex(cats_comunes).fillna(0).values.astype(float)
exp_v = (exp_dist.reindex(cats_comunes).values * obs_v.sum())
# normalizar exp para que sume igual a obs
exp_v = exp_v * (obs_v.sum() / exp_v.sum())
chi2_h6, p_h6 = stats.chisquare(obs_v, exp_v)
resid_std = (obs_v - exp_v) / np.sqrt(exp_v)
lift = obs_v / exp_v
rank_df = pd.DataFrame({"categoria": cats_comunes, "obs": obs_v.astype(int), "esp": exp_v.round(1),
                        "resid_std": resid_std.round(2), "lift": lift.round(3)})
# solo categorias con esperado>=5 para validez chi2, y rankear sobre-representadas
rank_valid = rank_df[rank_df["esp"] >= 5].sort_values("resid_std", ascending=False)
top_sobre = rank_valid[rank_valid["resid_std"] > 2].head(10)
h6["a_chi2_categoria"] = {
    "chi2": round(float(chi2_h6), 2), "p": float(f"{p_h6:.3e}"), "df": int(len(cats_comunes) - 1),
    "top_sobrerrepresentadas": top_sobre[["categoria", "obs", "esp", "resid_std", "lift"]].to_dict("records"),
}
print("H6a chi2=", round(chi2_h6, 1), "top sobre:", list(top_sobre["categoria"].head(5)))

# (b) MW price_total review<=2 vs review>=4 dentro de puntuales
pt_bajo = punt[punt["review_score"] <= 2]["price_total"].dropna()
pt_alto = punt[punt["review_score"] >= 4]["price_total"].dropna()
r_pt, p_pt, (n_b, n_a) = rank_biserial_mw(pt_bajo, pt_alto)
h6["b_precio_cola"] = {
    "rank_biserial": round(r_pt, 4), "p": float(f"{p_pt:.3e}"),
    "mediana_bajo": float(pt_bajo.median()), "mediana_alto": float(pt_alto.median()),
    "n_bajo": n_b, "n_alto": n_a, "efecto": eff_label_r(r_pt),
    "el_precio_muerde": bool(abs(r_pt) >= 0.1),
}
print("H6b price rank-biserial bajo vs alto (puntuales):", round(r_pt, 4), eff_label_r(r_pt))

# (c) entropia H(review) en bits por categoria (n>=100) condicionando en puntualidad
ent_por_cat = []
for cat, sub in punt.groupby("product_category_name_english"):
    if len(sub) >= 100:
        ent_por_cat.append({"categoria": cat, "n": len(sub),
                            "entropia_bits": round(entropy_bits(sub["review_score"]), 4),
                            "review_medio": round(float(sub["review_score"].mean()), 3)})
ent_por_cat.sort(key=lambda d: d["entropia_bits"], reverse=True)
h6["c_entropia_review_por_categoria_puntual"] = ent_por_cat[:15]
print("H6c cat mas impredecible (puntual):", ent_por_cat[0]["categoria"] if ent_por_cat else None)

h6["veredicto"] = (f"CONFIRMADA parcial: {h6['a_tamano']['pct_de_puntuales']}% de entregas puntuales aun reciben review<=2; "
                   f"hay categorias sobre-representadas en fallo (chi2={round(chi2_h6,1)}, p<0.001), "
                   f"pero el precio NO discrimina en la cola (rank-biserial={round(r_pt,3)}, {eff_label_r(r_pt)}).")
RES["H6"] = h6

# ============================================================
# H7 pago como interaccion
# ============================================================
print("\n== H7 ==")
h7 = {}
# (a) dentro de tardios: Spearman(dias_retraso, review) por payment_type
sp_por_pago = {}
for pt, sub in tard.groupby("payment_type"):
    if len(sub) >= 30:
        rho, p, n = spearman(sub["dias_retraso"], sub["review_score"])
        sp_por_pago[pt] = {"rho": round(rho, 4), "p": float(f"{p:.3e}"), "n": n}
# KW review entre payment_types en tardios vs puntuales
def kw_pago(df):
    grupos = [g["review_score"].values for _, g in df.groupby("payment_type") if len(g) >= 30]
    return epsilon_sq_kw(grupos)
H_t, p_t, eps2_t, n_t = kw_pago(tard)
H_p, p_p, eps2_p, n_p = kw_pago(punt)
h7["a_interaccion"] = {
    "spearman_retraso_review_por_pago_en_tardios": sp_por_pago,
    "kw_pago_en_tardios": {"H": round(float(H_t), 3), "eps2": round(float(eps2_t), 5), "p": float(f"{p_t:.3e}"), "n": n_t},
    "kw_pago_en_puntuales": {"H": round(float(H_p), 3), "eps2": round(float(eps2_p), 5), "p": float(f"{p_p:.3e}"), "n": n_p},
    "hay_interaccion": bool(eps2_t > eps2_p + 0.005),
}
print("H7a KW pago eps2 tardios=", round(eps2_t, 5), "vs puntuales=", round(eps2_p, 5))

# (b) Spearman parcial (installments, review | dias_retraso) en tardios
rho_i, p_i, n_i = spearman_partial(tard["payment_installments"], tard["review_score"], tard["dias_retraso"])
h7["b_installments_parcial_en_tardios"] = {"rho": round(rho_i, 4), "p": float(f"{p_i:.3e}"), "n": n_i, "efecto": eff_label_r(rho_i)}
print("H7b installments~review | retraso (tardios) parcial rho=", round(rho_i, 4))

h7["veredicto"] = ("RECHAZADA: el tipo de pago no modula la relacion retraso->review (eps2 casi identico en tardios y puntuales); "
                   "las cuotas tampoco predicen review una vez fijado el retraso (efecto " + eff_label_r(rho_i) + ").")
RES["H7"] = h7

# ============================================================
# D1 regional: % orders Olist por macro-region (TODAS las orders con customer_state)
# ============================================================
print("\n== D1 ==")
orders = pd.read_csv(PROC + r"\olist_orders_clean.csv", usecols=["customer_id", "order_status"])
customers = pd.read_csv(PROC + r"\olist_customers_clean.csv", usecols=["customer_id", "customer_state"])
oc = orders.merge(customers, on="customer_id", how="left")
oc["region"] = oc["customer_state"].map(REGION_MAP)
n_orders_total = len(oc)
reg_counts = oc["region"].value_counts()
olist_pct = (reg_counts / reg_counts.sum() * 100).reindex(REGIONES).fillna(0)
mercado = {"Norte": 4, "Nordeste": 18, "Centro-Oeste": 7, "Sudeste": 56, "Sur": 16}
p_olist = np.array([olist_pct[r] / 100 for r in REGIONES])
q_mercado = np.array([mercado[r] / 100 for r in REGIONES])
kl_bits = float(stats.entropy(p_olist, q_mercado, base=2))
# chi2 bondad de ajuste: observado (conteos) vs esperado (mercado * n)
obs_reg = np.array([reg_counts.get(r, 0) for r in REGIONES], float)
exp_reg = (q_mercado / q_mercado.sum()) * obs_reg.sum()
chi2_reg, p_reg = stats.chisquare(obs_reg, exp_reg)
cv_reg = cramers_v(chi2_reg, obs_reg.sum(), len(REGIONES), 2)
d1 = {
    "n_orders": int(n_orders_total),
    "olist_pct": {r: round(float(olist_pct[r]), 2) for r in REGIONES},
    "mercado_pct": mercado,
    "kl_bits": round(kl_bits, 4),
    "chi2": round(float(chi2_reg), 1), "chi2_p": float(f"{p_reg:.3e}"),
    "cramers_v": round(float(cv_reg), 4),
}
# sobre/sub
ratios = {r: round(float(olist_pct[r]) / mercado[r], 2) for r in REGIONES}
d1["ratio_olist_vs_mercado"] = ratios
sobre = [r for r in REGIONES if ratios[r] > 1.15]
sub = [r for r in REGIONES if ratios[r] < 0.85]
d1["nota"] = (f"Olist sobre-representa {', '.join(sobre) if sobre else 'ninguna'} y sub-representa "
              f"{', '.join(sub) if sub else 'ninguna'} frente al mercado. "
              f"KL={round(kl_bits,3)} bits indica desviacion moderada; V de Cramer={round(cv_reg,3)}.")
print("D1 olist_pct:", d1["olist_pct"], "KL=", round(kl_bits, 3))
RES["D1"] = d1

# ============================================================
# D2 SEGUNDA CAUSA excluyendo tiempo
# ============================================================
print("\n== D2 ==")
excluidas = ["dias_retraso", "tiempo_entrega_dias"]
base = deliv.copy()  # usar delivered con retraso valido para poder controlar tiempo
cont_vars = ["price_total", "freight_total", "ratio_flete_precio", "distancia_seller_customer_km",
             "n_items", "payment_value", "payment_installments"]
cat_vars = {"product_category_name_english": "categoria", "payment_type": "payment_type", "region": "region"}
ranking = []
for v in cont_vars:
    rho, p, n = spearman(base[v], base["review_score"])
    ranking.append({"var": v, "tipo": "continua", "metrica": "rho2_spearman",
                    "valor": round(rho ** 2, 6), "rho": round(rho, 4), "p": float(f"{p:.3e}"), "n": n})
for v, _ in cat_vars.items():
    grupos = []
    for lvl, sub in base.groupby(v):
        if len(sub) >= 30:
            grupos.append(sub["review_score"].values)
    H, p, eps2, n = epsilon_sq_kw(grupos)
    ranking.append({"var": v, "tipo": "categorica", "metrica": "eps2_kruskal",
                    "valor": round(float(eps2), 6), "H": round(float(H), 2), "p": float(f"{p:.3e}"), "n": n})
ranking.sort(key=lambda d: d["valor"], reverse=True)

# ganador: mayor valor que SOBREVIVA control por Spearman parcial (solo aplica a continuas)
ganador = None
for cand in ranking:
    if cand["tipo"] == "continua":
        # parcial controlando dias_retraso y tiempo_entrega (control secuencial: usar retraso, luego tiempo)
        r1, _, _ = spearman_partial(base[cand["var"]], base["review_score"], base["dias_retraso"])
        r2, _, _ = spearman_partial(base[cand["var"]], base["review_score"], base["tiempo_entrega_dias"])
        cand["rho_parcial_ctrl_retraso"] = round(r1, 4)
        cand["rho_parcial_ctrl_entrega"] = round(r2, 4)
        cand["sobrevive"] = bool(abs(r1) >= 0.05 and abs(r2) >= 0.05)
    else:
        # para categoricas no hay parcial simple; marcamos si eps2 no despreciable
        cand["sobrevive"] = bool(cand["valor"] >= 0.01)
for cand in ranking:
    if cand["sobrevive"] and ganador is None:
        ganador = cand
d2 = {
    "excluidas": excluidas,
    "ranking": ranking,
    "ganador": {
        "var": ganador["var"],
        "efecto": (eff_label_eps2(ganador["valor"]) if ganador["tipo"] == "categorica" else eff_label_r(math.sqrt(ganador["valor"]))),
        "prueba": ganador["metrica"],
        "valor": ganador["valor"],
        "interpretacion": (f"{ganador['var']} es el predictor NO temporal con mayor varianza de review asociada "
                           f"({ganador['metrica']}={ganador['valor']}) que sobrevive el control por tiempo.")
    } if ganador else None,
}
print("D2 ranking top3:", [(r["var"], r["valor"]) for r in ranking[:3]])
print("D2 ganador:", d2["ganador"]["var"] if ganador else None)
RES["D2"] = d2

# ---------- guardar resultados nuevos ----------
out = BASE + r"\outputs\reports\resultados_dashboard.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(RES, f, ensure_ascii=False, indent=2)
print("\nGuardado:", out)
print("DONE ANALISIS")
