# -*- coding: utf-8 -*-
"""
Analisis inferencial final - Satisfaccion Olist.
Parte 1: 11 conceptos estadisticos obligatorios.
Parte 2: 4 hipotesis no convencionales.
Reglas: solo pruebas NO parametricas. Decision por TAMANO DE EFECTO.
Salida: charts en outputs/charts, resultados serializados a outputs/reports/resultados.json
"""
import json
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
np.random.seed(42)

# ---- Estilo grafico: fondo claro, anotaciones directas ----
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "axes.grid": True,
    "grid.alpha": 0.25, "font.size": 11, "axes.titleweight": "bold",
})
CHART = "outputs/charts/"
R = {}  # resultados numericos

C = pd.read_csv("data/processed/analitico_cliente.csv")
V = pd.read_csv("data/processed/analitico_vendedor.csv")

# ============================================================
# Helpers de tamano de efecto (no parametricos)
# ============================================================
def rank_biserial(a, b):
    """Rank-biserial a partir de Mann-Whitney U. Rango de a vs b."""
    a = np.asarray(a); b = np.asarray(b)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan, np.nan
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    rbc = 1 - 2 * U / (len(a) * len(b))  # >0 => a tiende a ser MAYOR que b
    return rbc, p, U

def epsilon_squared(groups):
    """epsilon^2 para Kruskal-Wallis."""
    groups = [np.asarray(g)[~np.isnan(g)] for g in groups]
    groups = [g for g in groups if len(g) > 0]
    n = sum(len(g) for g in groups)
    k = len(groups)
    if k < 2 or n <= k:
        return np.nan, np.nan, np.nan
    H, p = stats.kruskal(*groups)
    eps2 = (H - k + 1) / (n - k)
    return eps2, p, H

def spearman(x, y):
    m = (~np.isnan(x)) & (~np.isnan(y))
    if m.sum() < 10:
        return np.nan, np.nan, int(m.sum())
    rho, p = stats.spearmanr(x[m], y[m])
    return rho, p, int(m.sum())

def spearman_partial(x, y, z):
    """Spearman parcial de x,y controlando z (via residuos de rango)."""
    df = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(df) < 20:
        return np.nan, len(df)
    rx = df["x"].rank(); ry = df["y"].rank(); rz = df["z"].rank()
    def resid(a, b):
        b1 = np.polyfit(b, a, 1)
        return a - np.polyval(b1, b)
    ex = resid(rx.values, rz.values)
    ey = resid(ry.values, rz.values)
    rho, _ = stats.spearmanr(ex, ey)
    return rho, len(df)

# ============================================================
# PARTE 1 - LOS 11 CONCEPTOS
# ============================================================

# Filtro base entregados con fechas validas para lo que usa entrega
deliv = C[(C.order_status == "delivered") & C.dias_retraso.notna() &
          C.tiempo_entrega_dias.notna()].copy()
deliv["tarde"] = deliv["dias_retraso"] > 0
R["n_delivered_validos"] = int(len(deliv))

# ---- 1. Probabilidad condicional ----
p_low_tarde = (deliv.loc[deliv.tarde, "review_score"] <= 2).mean()
p_low_atiempo = (deliv.loc[~deliv.tarde, "review_score"] <= 2).mean()
R["c1_prob_cond"] = {
    "P(review<=2 | tarde)": round(float(p_low_tarde), 4),
    "P(review<=2 | a_tiempo)": round(float(p_low_atiempo), 4),
    "riesgo_relativo": round(float(p_low_tarde / p_low_atiempo), 3),
    "n_tarde": int(deliv.tarde.sum()), "n_atiempo": int((~deliv.tarde).sum()),
}

# ---- 2. Teorema de Bayes: P(tarde | review==1) invirtiendo ----
p_tarde = deliv.tarde.mean()                          # prior
p_r1_dado_tarde = (deliv.loc[deliv.tarde, "review_score"] == 1).mean()   # verosimilitud
p_r1_dado_atiempo = (deliv.loc[~deliv.tarde, "review_score"] == 1).mean()
p_r1 = (deliv.review_score == 1).mean()               # evidencia
p_tarde_dado_r1 = p_r1_dado_tarde * p_tarde / p_r1
R["c2_bayes"] = {
    "prior_P(tarde)": round(float(p_tarde), 4),
    "verosim_P(r1|tarde)": round(float(p_r1_dado_tarde), 4),
    "P(r1|a_tiempo)": round(float(p_r1_dado_atiempo), 4),
    "evidencia_P(r1)": round(float(p_r1), 4),
    "posterior_P(tarde|r1)": round(float(p_tarde_dado_r1), 4),
    "lift": round(float(p_tarde_dado_r1 / p_tarde), 3),
}

# ---- 3. MLE: ajustar distribucion a freight_value ----
fv = C["freight_value"].dropna().values
fv = fv[fv > 0]
mle = {}
for name, dist in [("lognorm", stats.lognorm), ("gamma", stats.gamma),
                   ("expon", stats.expon), ("weibull_min", stats.weibull_min)]:
    par = dist.fit(fv, floc=0)
    ll = np.sum(dist.logpdf(fv, *par))
    k = len(par)
    aic = 2 * k - 2 * ll
    bic = k * np.log(len(fv)) - 2 * ll
    ks = stats.kstest(fv, dist.cdf, args=par).statistic
    mle[name] = {"params": [round(float(x), 4) for x in par],
                 "loglik": round(float(ll), 1), "AIC": round(float(aic), 1),
                 "BIC": round(float(bic), 1), "KS": round(float(ks), 4)}
best_fv = min(mle, key=lambda d: mle[d]["AIC"])
R["c3_mle_freight"] = {"n": int(len(fv)), "ajustes": mle, "mejor_AIC": best_fv}

# ---- 4. Distribuciones parametricas: mejor dist a tiempo_entrega y price ----
def fit_best(x, cands):
    x = x[np.isfinite(x)]; x = x[x > 0]
    out = {}
    for name, dist in cands:
        try:
            par = dist.fit(x, floc=0)
            ll = np.sum(dist.logpdf(x, *par))
            aic = 2 * len(par) - 2 * ll
            ks = stats.kstest(x, dist.cdf, args=par).statistic
            out[name] = {"params": [round(float(z), 4) for z in par],
                         "AIC": round(float(aic), 1), "KS": round(float(ks), 4)}
        except Exception as e:
            out[name] = {"error": str(e)}
    valid = {k: v for k, v in out.items() if "AIC" in v}
    best = min(valid, key=lambda d: valid[d]["AIC"]) if valid else None
    return out, best

cands = [("lognorm", stats.lognorm), ("gamma", stats.gamma), ("weibull_min", stats.weibull_min)]
te = deliv["tiempo_entrega_dias"].values
te_out, te_best = fit_best(te, cands)
pr = C["price_total"].dropna().values
pr_out, pr_best = fit_best(pr, cands)
R["c4_distribuciones"] = {
    "tiempo_entrega_dias": {"ajustes": te_out, "mejor_AIC": te_best},
    "price_total": {"ajustes": pr_out, "mejor_AIC": pr_best},
}

# ---- 5. Esperanza y varianza de review por grupo ----
by_state = C.groupby("customer_state")["review_score"].agg(["mean", "var", "count"])
by_state = by_state[by_state["count"] >= 100].sort_values("mean")
by_pay = C.groupby("payment_type")["review_score"].agg(["mean", "var", "count"])
by_pay = by_pay[by_pay["count"] >= 50]
R["c5_esperanza_var"] = {
    "por_estado_top_peor": by_state.head(3).round(3).reset_index().to_dict("records"),
    "por_estado_top_mejor": by_state.tail(3).round(3).reset_index().to_dict("records"),
    "por_payment_type": by_pay.round(3).reset_index().to_dict("records"),
    "E_global": round(float(C.review_score.mean()), 3),
    "Var_global": round(float(C.review_score.var()), 3),
}

# ---- 6. Independencia y correlacion: Spearman derivadas vs review ----
num_cols = ["dias_retraso", "tiempo_entrega_dias", "ratio_flete_precio",
            "distancia_seller_customer_km", "price_total", "freight_total",
            "n_items", "payment_value"]
corr_target = {}
for col in num_cols:
    rho, p, n = spearman(deliv["review_score"].values.astype(float), deliv[col].values.astype(float))
    corr_target[col] = {"rho": round(rho, 4), "p": float(p), "n": n}
R["c6_correlacion"] = corr_target
# matriz de correlacion de rangos
corr_cols = ["review_score"] + num_cols
corr_mat = deliv[corr_cols].corr(method="spearman")

# ---- 7. Prior y Posterior: shrinkage bayesiano review por seller ----
# Modelo normal-normal empirico. y_bar_i (media seller) contraida al prior global.
# Necesitamos media y n por seller. Traemos seller_id via merge order->seller no disponible en analitico
# cliente; usamos analitico_vendedor que ya trae review_score_promedio y n_pedidos por seller.
vv = V[V.review_score_promedio.notna() & (V.n_pedidos > 0)].copy()
mu0 = vv["review_score_promedio"].mean()               # media global (prior)
# varianza entre sellers (tau^2) y varianza intra estimada por review global (~ var de review_score)
var_review = float(C.review_score.var())               # varianza de una review individual
tau2 = float(vv["review_score_promedio"].var())        # var entre medias de seller (aprox prior)
# shrink: posterior_i = w_i*y_i + (1-w_i)*mu0 ; w_i = n_i/(n_i + var_review/tau2)
kappa = var_review / tau2
vv["w"] = vv["n_pedidos"] / (vv["n_pedidos"] + kappa)
vv["review_posterior"] = vv["w"] * vv["review_score_promedio"] + (1 - vv["w"]) * mu0
vv["shrink_abs"] = (vv["review_posterior"] - vv["review_score_promedio"]).abs()
R["c7_shrinkage"] = {
    "mu0_prior_global": round(float(mu0), 4),
    "var_review_individual": round(var_review, 4),
    "tau2_entre_sellers": round(tau2, 4),
    "kappa_pseudo_conteo": round(float(kappa), 3),
    "shrink_medio_abs": round(float(vv["shrink_abs"].mean()), 4),
    "shrink_lowvol_n<=5": round(float(vv.loc[vv.n_pedidos <= 5, "shrink_abs"].mean()), 4),
    "shrink_highvol_n>100": round(float(vv.loc[vv.n_pedidos > 100, "shrink_abs"].mean()), 4),
    "ej_sellers_5perfectos": vv[(vv.review_score_promedio == 5) & (vv.n_pedidos <= 3)]
        [["n_pedidos", "review_score_promedio", "review_posterior"]].head(3).round(3).to_dict("records"),
}

# ---- 8. Entropia de Shannon: payment_type y product_category ----
def shannon(series):
    p = series.value_counts(normalize=True).values
    return float(stats.entropy(p, base=2)), int(len(p))
h_pay, k_pay = shannon(C["payment_type"].dropna())
h_cat, k_cat = shannon(C["product_category_name_english"].dropna())
R["c8_entropia"] = {
    "payment_type": {"H_bits": round(h_pay, 4), "k_categorias": k_pay,
                     "H_max": round(float(np.log2(k_pay)), 4),
                     "eficiencia": round(h_pay / np.log2(k_pay), 3)},
    "product_category": {"H_bits": round(h_cat, 4), "k_categorias": k_cat,
                         "H_max": round(float(np.log2(k_cat)), 4),
                         "eficiencia": round(h_cat / np.log2(k_cat), 3)},
}

# ---- 9. Entropia cruzada: log_loss de clasificador logistico review pos/neg ----
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

clf_df = deliv.dropna(subset=["dias_retraso", "tiempo_entrega_dias",
                              "ratio_flete_precio", "freight_total", "price_total"]).copy()
Xf = ["dias_retraso", "tiempo_entrega_dias", "ratio_flete_precio", "freight_total", "price_total"]
X = clf_df[Xf].values
y = (clf_df["review_score"] >= 4).astype(int).values
pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
proba = cross_val_predict(pipe, X, y, cv=5, method="predict_proba")[:, 1]
ll = log_loss(y, proba)
# baseline: predecir siempre la tasa base
base_rate = y.mean()
ll_base = log_loss(y, np.full_like(proba, base_rate))
auc = roc_auc_score(y, proba)
pipe.fit(X, y)
coefs = dict(zip(Xf, pipe.named_steps["logisticregression"].coef_[0].round(4)))
R["c9_cross_entropy"] = {
    "n": int(len(y)), "tasa_base_pos": round(float(base_rate), 4),
    "log_loss_modelo": round(float(ll), 4), "log_loss_baseline": round(float(ll_base), 4),
    "reduccion_pct": round(float((ll_base - ll) / ll_base * 100), 2),
    "AUC": round(float(auc), 4), "coefs_estandarizados": {k: float(v) for k, v in coefs.items()},
}

# ---- 10. Divergencia KL: distribucion review SP vs Nordeste, y a tiempo vs tarde ----
def review_dist(sub):
    vc = sub["review_score"].value_counts(normalize=True).reindex([1, 2, 3, 4, 5]).fillna(1e-9)
    v = vc.values; return v / v.sum()
nordeste = ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "PI", "SE"]
p_sp = review_dist(C[C.customer_state == "SP"])
q_ne = review_dist(C[C.customer_state.isin(nordeste)])
kl_sp_ne = float(stats.entropy(p_sp, q_ne, base=2))
kl_ne_sp = float(stats.entropy(q_ne, p_sp, base=2))
p_at = review_dist(deliv[~deliv.tarde])
q_ta = review_dist(deliv[deliv.tarde])
kl_at_ta = float(stats.entropy(p_at, q_ta, base=2))
kl_ta_at = float(stats.entropy(q_ta, p_at, base=2))
R["c10_kl"] = {
    "SP_vs_Nordeste": {"P_SP": p_sp.round(4).tolist(), "Q_NE": q_ne.round(4).tolist(),
                       "KL(SP||NE)_bits": round(kl_sp_ne, 4), "KL(NE||SP)_bits": round(kl_ne_sp, 4)},
    "atiempo_vs_tarde": {"P_atiempo": p_at.round(4).tolist(), "Q_tarde": q_ta.round(4).tolist(),
                         "KL(atiempo||tarde)_bits": round(kl_at_ta, 4),
                         "KL(tarde||atiempo)_bits": round(kl_ta_at, 4)},
}

# ---- 11. Extra: independencia payment_type x review (chi2) ----
ct = pd.crosstab(C["payment_type"], (C["review_score"] >= 4))
chi2, pchi, dof, _ = stats.chi2_contingency(ct)
n = ct.values.sum()
cramer_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
R["c11_chi2_pay_review"] = {
    "chi2": round(float(chi2), 2), "p": float(pchi), "dof": int(dof),
    "cramer_v": round(float(cramer_v), 4), "n": int(n),
}

print(">> PARTE 1 completada")

# ============================================================
# PARTE 2 - HIPOTESIS
# ============================================================

def theil_sen(x, y):
    """Pendiente de Theil-Sen (mediana de pendientes por pares)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3:
        return np.nan
    res = stats.theilslopes(y, x)
    return float(res[0])

# ---- H1: aversion a la perdida ----
h1 = deliv.copy()
adel = h1[(h1.dias_retraso >= -15) & (h1.dias_retraso < 0)]
retr = h1[(h1.dias_retraso > 0) & (h1.dias_retraso <= 15)]
rho_adel, p_adel, n_adel = spearman(adel.dias_retraso.values.astype(float), adel.review_score.values.astype(float))
rho_retr, p_retr, n_retr = spearman(retr.dias_retraso.values.astype(float), retr.review_score.values.astype(float))
# Theil-Sen sobre medianas por dia
med_adel = adel.groupby(adel.dias_retraso.round())["review_score"].median()
med_retr = retr.groupby(retr.dias_retraso.round())["review_score"].median()
ts_adel = theil_sen(med_adel.index.values, med_adel.values)   # subida/dia (mediana)
ts_retr = theil_sen(med_retr.index.values, med_retr.values)   # caida/dia (mediana)
mean_adel = adel.groupby(adel.dias_retraso.round())["review_score"].mean()
mean_retr = retr.groupby(retr.dias_retraso.round())["review_score"].mean()
ts_adel_mean = theil_sen(mean_adel.index.values, mean_adel.values)
ts_retr_mean = theil_sen(mean_retr.index.values, mean_retr.values)
# Kruskal entre zonas adelanto/justo/retraso
z_adel = h1.loc[h1.dias_retraso < 0, "review_score"].values.astype(float)
z_justo = h1.loc[h1.dias_retraso == 0, "review_score"].values.astype(float)
z_retr = h1.loc[h1.dias_retraso > 0, "review_score"].values.astype(float)
eps2_h1, p_kw_h1, H_h1 = epsilon_squared([z_adel, z_justo, z_retr])
rbc_h1, p_mw_h1, _ = rank_biserial(z_adel, z_retr)   # adelanto vs retraso
# Spearman parcial tiempo_entrega controlando dias_retraso
rho_te_partial, n_partial = spearman_partial(
    h1.tiempo_entrega_dias.values.astype(float),
    h1.review_score.values.astype(float),
    h1.dias_retraso.values.astype(float))
rho_te_raw, _, _ = spearman(h1.tiempo_entrega_dias.values.astype(float), h1.review_score.values.astype(float))
ratio_asim = abs(ts_retr_mean) / abs(ts_adel_mean) if ts_adel_mean and not np.isnan(ts_adel_mean) and ts_adel_mean != 0 else np.nan
R["H1"] = {
    "rho_adelanto": round(rho_adel, 4), "n_adelanto": n_adel,
    "rho_retraso": round(rho_retr, 4), "n_retraso": n_retr,
    "theilsen_subida_por_dia_adelanto_MEDIANA": round(ts_adel, 4) if not np.isnan(ts_adel) else None,
    "theilsen_caida_por_dia_retraso_MEDIANA": round(ts_retr, 4) if not np.isnan(ts_retr) else None,
    "theilsen_subida_por_dia_adelanto_MEDIA": round(ts_adel_mean, 4) if not np.isnan(ts_adel_mean) else None,
    "theilsen_caida_por_dia_retraso_MEDIA": round(ts_retr_mean, 4) if not np.isnan(ts_retr_mean) else None,
    "ratio_asimetria_caida/subida_MEDIA": round(float(ratio_asim), 2) if ratio_asim==ratio_asim else None,
    "kruskal_eps2": round(eps2_h1, 4), "kruskal_p": float(p_kw_h1),
    "mannwhitney_rbc_adel_vs_retr": round(rbc_h1, 4),
    "rho_tiempo_entrega_raw": round(rho_te_raw, 4),
    "rho_tiempo_entrega_parcial_ctrl_retraso": round(rho_te_partial, 4),
}

# ---- H2: buffer / colas ----
# buffer = estimada - compra
h2 = deliv.copy()
h2["order_purchase_timestamp"] = pd.to_datetime(h2["order_purchase_timestamp"])
h2["order_estimated_delivery_date"] = pd.to_datetime(h2["order_estimated_delivery_date"])
h2["buffer_prometido_dias"] = (h2["order_estimated_delivery_date"] - h2["order_purchase_timestamp"]).dt.total_seconds() / 86400
bandas = [(0, 7), (8, 14), (15, 21), (22, 30), (31, 999)]
h2_bandas = {}
rhos_h2 = []
for lo, hi in bandas:
    sub = h2[(h2.tiempo_entrega_dias >= lo) & (h2.tiempo_entrega_dias <= hi)]
    rho, p, nn = spearman(sub.buffer_prometido_dias.values.astype(float), sub.review_score.values.astype(float))
    h2_bandas[f"{lo}-{hi if hi<999 else '+'}"] = {"rho": round(rho, 4) if rho==rho else None,
                                                   "p": float(p) if p==p else None, "n": nn}
    if rho == rho:
        rhos_h2.append(rho)
rho_h2_global, _, _ = spearman(h2.buffer_prometido_dias.values.astype(float), h2.review_score.values.astype(float))
R["H2"] = {
    "rho_buffer_review_SIN_condicionar": round(rho_h2_global, 4),
    "por_banda_tiempo_entrega": h2_bandas,
    "n_bandas_con_rho>=0.10": int(sum(1 for r in rhos_h2 if r >= 0.10)),
    "n_bandas_total": len(rhos_h2),
}

# ---- H3: flete relativo (solo puntuales) ----
h3 = deliv[deliv.dias_retraso <= 0].copy()
rho_ratio, p_ratio, n_ratio = spearman(h3.ratio_flete_precio.values.astype(float), h3.review_score.values.astype(float))
# parcial: freight absoluto controlando price
rho_fv_partial, n_fvp = spearman_partial(h3.freight_total.values.astype(float),
                                         h3.review_score.values.astype(float),
                                         h3.price_total.values.astype(float))
rho_fv_raw, _, _ = spearman(h3.freight_total.values.astype(float), h3.review_score.values.astype(float))
rho_ratio_dist, _, _ = spearman(h3.ratio_flete_precio.values.astype(float), h3.distancia_seller_customer_km.values.astype(float))
rho_ratio_items, _, _ = spearman(h3.ratio_flete_precio.values.astype(float), h3.n_items.values.astype(float))
# quintiles ratio -> kruskal
h3v = h3.dropna(subset=["ratio_flete_precio"]).copy()
h3v["q_ratio"] = pd.qcut(h3v["ratio_flete_precio"], 5, labels=False, duplicates="drop")
grps = [h3v.loc[h3v.q_ratio == q, "review_score"].values.astype(float) for q in sorted(h3v.q_ratio.dropna().unique())]
eps2_h3, p_kw_h3, H_h3 = epsilon_squared(grps)
med_by_q = h3v.groupby("q_ratio")["review_score"].agg(["median", "mean", "count"]).round(3)
R["H3"] = {
    "rho_ratio_review": round(rho_ratio, 4), "n": n_ratio,
    "rho_freight_abs_parcial_ctrl_price": round(rho_fv_partial, 4),
    "rho_freight_abs_raw": round(rho_fv_raw, 4),
    "rho_ratio_distancia": round(rho_ratio_dist, 4),
    "rho_ratio_nitems": round(rho_ratio_items, 4),
    "kruskal_quintiles_eps2": round(eps2_h3, 4), "kruskal_p": float(p_kw_h3),
    "review_por_quintil_ratio": med_by_q.reset_index().to_dict("records"),
}

# ---- H4: r/K vendedores ----
h4 = V[V.n_pedidos >= 5].copy()   # excluye artefacto binomial
def banda_vol(n):
    if n <= 20: return "5-20"
    if n <= 100: return "21-100"
    return ">100"
h4["banda"] = h4["n_pedidos"].apply(banda_vol)
rho_np_tardio, p1, n1 = spearman(h4.n_pedidos.values.astype(float), h4.pct_despachos_tardios.values.astype(float))
rho_np_review, p2, n2 = spearman(h4.n_pedidos.values.astype(float), h4.review_score_promedio.values.astype(float))
orden = ["5-20", "21-100", ">100"]
iqr_tardio = {}; iqr_review = {}; medianas = {}
gt = []; gr = []
for b in orden:
    sub = h4[h4.banda == b]
    st = sub.pct_despachos_tardios.dropna()
    sr = sub.review_score_promedio.dropna()
    iqr_tardio[b] = round(float(st.quantile(.75) - st.quantile(.25)), 3)
    iqr_review[b] = round(float(sr.quantile(.75) - sr.quantile(.25)), 3)
    medianas[b] = {"n_sellers": int(len(sub)),
                   "med_pct_tardio": round(float(st.median()), 3),
                   "med_review": round(float(sr.median()), 3)}
    gt.append(st.values); gr.append(sr.values)
fk_tardio_stat, fk_tardio_p = stats.fligner(*[g for g in gt if len(g) > 1])
fk_review_stat, fk_review_p = stats.fligner(*[g for g in gr if len(g) > 1])
R["H4"] = {
    "n_sellers_tras_excluir_n<5": int(len(h4)),
    "rho_npedidos_pct_tardio": round(rho_np_tardio, 4),
    "rho_npedidos_review": round(rho_np_review, 4),
    "medianas_por_banda": medianas,
    "IQR_pct_tardio_por_banda": iqr_tardio,
    "IQR_review_por_banda": iqr_review,
    "fligner_pct_tardio": {"stat": round(float(fk_tardio_stat), 2), "p": float(fk_tardio_p)},
    "fligner_review": {"stat": round(float(fk_review_stat), 2), "p": float(fk_review_p)},
}

print(">> PARTE 2 completada")

# ============================================================
# GRAFICAS
# ============================================================
ACCENT = "#2b6cb0"; RED = "#c53030"; GREEN = "#2f855a"; GREY = "#4a5568"

# G1: distribucion review (forma en J)
fig, ax = plt.subplots(figsize=(7, 4.5))
vc = C.review_score.value_counts().sort_index()
bars = ax.bar(vc.index, vc.values, color=ACCENT, edgecolor="white")
for x, y in zip(vc.index, vc.values):
    ax.text(x, y + 500, f"{y:,}\n({y/vc.sum()*100:.0f}%)", ha="center", va="bottom", fontsize=9)
ax.set_title("Distribucion de review_score (forma en J)")
ax.set_xlabel("review_score"); ax.set_ylabel("n ordenes"); ax.set_ylim(0, vc.max()*1.18)
fig.tight_layout(); fig.savefig(CHART + "01_dist_review_scoreJ.png", dpi=130); plt.close(fig)

# G2: review medio vs dias_retraso, linea en 0 (H1)
fig, ax = plt.subplots(figsize=(8, 4.5))
sub = deliv[(deliv.dias_retraso >= -20) & (deliv.dias_retraso <= 20)]
g = sub.groupby(sub.dias_retraso.round())["review_score"].mean()
ax.plot(g.index, g.values, color=ACCENT, lw=2)
ax.axvline(0, color=RED, ls="--", lw=1.5)
ax.text(0.3, ax.get_ylim()[0]+0.1, "retraso = 0", color=RED, rotation=90, va="bottom", fontsize=9)
ax.annotate(f"caida/dia (retraso): {R['H1']['theilsen_caida_por_dia_retraso_MEDIA']}\n"
            f"subida/dia (adelanto): {R['H1']['theilsen_subida_por_dia_adelanto_MEDIA']}\n"
            f"asimetria x{R['H1']['ratio_asimetria_caida/subida_MEDIA']}",
            xy=(0.02, 0.05), xycoords="axes fraction", fontsize=9,
            bbox=dict(boxstyle="round", fc="#f0f4f8", ec=GREY))
ax.set_title("Review medio vs dias de retraso (H1: aversion a la perdida)")
ax.set_xlabel("dias_retraso (>0 = tarde)"); ax.set_ylabel("review medio")
fig.tight_layout(); fig.savefig(CHART + "02_H1_review_vs_retraso.png", dpi=130); plt.close(fig)

# G3: Spearman(buffer,review) por banda (H2)
fig, ax = plt.subplots(figsize=(7.5, 4.5))
labels = list(h2_bandas.keys())
vals = [h2_bandas[k]["rho"] if h2_bandas[k]["rho"] is not None else 0 for k in labels]
cols = [GREEN if v >= 0.10 else GREY for v in vals]
bars = ax.bar(labels, vals, color=cols, edgecolor="white")
ax.axhline(0.10, color=RED, ls="--", lw=1.2); ax.axhline(0, color="black", lw=0.8)
ax.text(len(labels)-0.5, 0.105, "umbral 0.10", color=RED, ha="right", fontsize=9)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v + (0.003 if v>=0 else -0.008), f"{v:.3f}",
            ha="center", va="bottom" if v>=0 else "top", fontsize=9)
ax.set_title("H2: Spearman(buffer, review) por banda de tiempo_entrega real")
ax.set_xlabel("banda tiempo_entrega_dias"); ax.set_ylabel("rho de Spearman")
fig.tight_layout(); fig.savefig(CHART + "03_H2_buffer_por_banda.png", dpi=130); plt.close(fig)

# G4: review vs quintil ratio flete/precio (H3)
fig, ax = plt.subplots(figsize=(7.5, 4.5))
q = med_by_q.reset_index()
bars = ax.bar(q["q_ratio"].astype(int).astype(str), q["mean"], color=ACCENT, edgecolor="white")
for b, v, med in zip(bars, q["mean"], q["median"]):
    ax.text(b.get_x()+b.get_width()/2, v+0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
ax.annotate(f"rho(ratio,review)={R['H3']['rho_ratio_review']}\n"
            f"eps2 quintiles={R['H3']['kruskal_quintiles_eps2']}",
            xy=(0.02, 0.05), xycoords="axes fraction", fontsize=9,
            bbox=dict(boxstyle="round", fc="#f0f4f8", ec=GREY))
ax.set_title("H3: review medio por quintil de ratio flete/precio (solo puntuales)")
ax.set_xlabel("quintil ratio_flete_precio (0=bajo,4=alto)"); ax.set_ylabel("review medio")
ax.set_ylim(q["mean"].min()-0.15, q["mean"].max()+0.15)
fig.tight_layout(); fig.savefig(CHART + "04_H3_review_por_quintil_ratio.png", dpi=130); plt.close(fig)

# G5: IQR de desempeno por banda de volumen (H4)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, d, ttl in [(axes[0], iqr_tardio, "IQR % despachos tardios"),
                   (axes[1], iqr_review, "IQR review promedio")]:
    ks = orden; vs = [d[k] for k in ks]
    bars = ax.bar(ks, vs, color=ACCENT, edgecolor="white")
    for b, v in zip(bars, vs):
        ax.text(b.get_x()+b.get_width()/2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_title(ttl); ax.set_xlabel("banda de volumen (n_pedidos)"); ax.set_ylabel("IQR")
axes[0].annotate(f"Fligner p={R['H4']['fligner_pct_tardio']['p']:.1e}", xy=(0.03,0.9),
                 xycoords="axes fraction", fontsize=9)
axes[1].annotate(f"Fligner p={R['H4']['fligner_review']['p']:.1e}", xy=(0.03,0.9),
                 xycoords="axes fraction", fontsize=9)
fig.suptitle("H4: dispersion (IQR) de desempeno por banda de volumen (n>=5)", fontweight="bold")
fig.tight_layout(); fig.savefig(CHART + "05_H4_IQR_por_volumen.png", dpi=130); plt.close(fig)

# G6: matriz de correlacion de Spearman
fig, ax = plt.subplots(figsize=(8.5, 7))
im = ax.imshow(corr_mat.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr_cols))); ax.set_yticks(range(len(corr_cols)))
ax.set_xticklabels(corr_cols, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(corr_cols, fontsize=8)
for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        v = corr_mat.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                color="white" if abs(v) > 0.5 else "black")
fig.colorbar(im, ax=ax, fraction=0.046)
ax.set_title("Matriz de correlacion de Spearman (rangos)")
fig.tight_layout(); fig.savefig(CHART + "06_matriz_spearman.png", dpi=130); plt.close(fig)

# G7: prior vs posterior sellers (shrinkage)
fig, ax = plt.subplots(figsize=(7.5, 5.5))
sc = ax.scatter(vv["review_score_promedio"], vv["review_posterior"],
                c=np.log10(vv["n_pedidos"]), cmap="viridis", s=12, alpha=0.6)
ax.plot([1, 5], [1, 5], color=RED, ls="--", lw=1.2)
ax.axhline(mu0, color=GREY, ls=":", lw=1)
ax.text(1.05, mu0+0.03, f"prior global={mu0:.2f}", color=GREY, fontsize=9)
ax.text(4.2, 4.35, "y=x (sin shrink)", color=RED, fontsize=9, rotation=38)
cb = fig.colorbar(sc, ax=ax); cb.set_label("log10(n_pedidos)")
ax.set_title("Prior vs Posterior: shrinkage bayesiano del review por seller")
ax.set_xlabel("review_score_promedio (verosimilitud cruda)")
ax.set_ylabel("review posterior (contraido)")
fig.tight_layout(); fig.savefig(CHART + "07_shrinkage_prior_posterior.png", dpi=130); plt.close(fig)

# G8: KL distribuciones review (a tiempo vs tarde)
fig, ax = plt.subplots(figsize=(7.5, 4.5))
x = np.array([1,2,3,4,5]); w = 0.38
ax.bar(x-w/2, p_at, w, label="a tiempo (P)", color=GREEN, edgecolor="white")
ax.bar(x+w/2, q_ta, w, label="tarde (Q)", color=RED, edgecolor="white")
for xi, v in zip(x, p_at): ax.text(xi-w/2, v+0.005, f"{v:.2f}", ha="center", fontsize=8)
for xi, v in zip(x, q_ta): ax.text(xi+w/2, v+0.005, f"{v:.2f}", ha="center", fontsize=8)
ax.annotate(f"KL(atiempo||tarde)={kl_at_ta:.3f} bits\nKL(tarde||atiempo)={kl_ta_at:.3f} bits",
            xy=(0.35, 0.75), xycoords="axes fraction", fontsize=9,
            bbox=dict(boxstyle="round", fc="#f0f4f8", ec=GREY))
ax.set_title("Divergencia KL: distribucion de review a tiempo vs tarde")
ax.set_xlabel("review_score"); ax.set_ylabel("probabilidad"); ax.legend()
fig.tight_layout(); fig.savefig(CHART + "08_KL_review_atiempo_tarde.png", dpi=130); plt.close(fig)

print(">> Graficas generadas")

# Serializar resultados
with open("outputs/reports/resultados.json", "w", encoding="utf-8") as f:
    json.dump(R, f, indent=2, ensure_ascii=False, default=str)
print(">> resultados.json guardado")
print(json.dumps(R, indent=2, ensure_ascii=False, default=str))
