# -*- coding: utf-8 -*-
"""Monte Carlo: ¿el nº de items importa para la (in)satisfaccion?
1) Prueba de PERMUTACION: ¿el efecto es real o azar?  (rompe el vinculo item<->detractor)
2) BOOTSTRAP: incertidumbre del impacto (detractores evitables) y bandas de la proyeccion.
Aislado del tiempo: solo pedidos entregados A TIEMPO.
"""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
RAWD = os.path.join(BASE, "data", "raw")
rng = np.random.default_rng(42)

# datos on-time  (items desde data/raw: mismo mapeo pedido->vendedor que la version limpia)
it = pd.read_csv(os.path.join(RAWD, "olist_order_items_dataset.csv"), usecols=["order_id", "seller_id"])
nsel = it.groupby("order_id")["seller_id"].nunique().rename("n_sel")
# vendedor principal por pedido (el de mas items; desempate por primero) para el cluster bootstrap
prim = (it.groupby(["order_id", "seller_id"]).size().reset_index(name="c")
          .sort_values(["order_id", "c"], ascending=[True, False])
          .drop_duplicates("order_id").set_index("order_id")["seller_id"])
cli = pd.read_csv(os.path.join(PROC, "analitico_cliente.csv"),
                  usecols=["order_id", "review_score", "dias_retraso", "order_status", "n_items"])
cli = cli[(cli.order_status == "delivered") & (cli.dias_retraso <= 0)].copy()
cli["seller_id"] = cli["order_id"].map(prim)
det = (cli["review_score"].values <= 2).astype(int)
k = np.clip(cli["n_items"].values, 1, 5).astype(int)
multi = (cli["n_items"].values >= 2).astype(int)
N = len(det)
print("N on-time =", N, "| detractor rate =", round(det.mean(), 4))

# ---------- 1) PERMUTACION ----------
def gap(labels):  # P(det|multi) - P(det|single)
    return labels[multi == 1].mean() - labels[multi == 0].mean()
obs_gap = float(gap(det))
B1 = 5000
null = np.empty(B1)
for b in range(B1):
    null[b] = gap(det[rng.permutation(N)])
p_val = float((np.abs(null) >= abs(obs_gap)).mean())
# p-valor con correccion (k+1)/(B+1): evita reportar "p=0" (imposible estimar 0 con B finito)
p_val_addone = float((np.sum(np.abs(null) >= abs(obs_gap)) + 1) / (B1 + 1))
# histograma del nulo (en puntos porcentuales)
null_pp = null * 100
lo, hi = null_pp.min(), null_pp.max()
edges = np.linspace(min(lo, -0.5), max(hi, 0.5), 31)
counts, _ = np.histogram(null_pp, bins=edges)
centers = ((edges[:-1] + edges[1:]) / 2).round(3)
perm = {"null_centers": centers.tolist(), "null_counts": counts.tolist(),
        "observed_pp": round(obs_gap * 100, 2), "p_value": p_val,
        "p_value_addone": p_val_addone, "p_upper_bound": round(1.0 / (B1 + 1), 6), "B": B1,
        "null_max_pp": round(float(null_pp.max()), 2)}
print("PERM obs_gap=%.1f pp | null max=%.2f pp | p_raw=%.4g | p<%.5f (add-one=%.5f)"
      % (obs_gap * 100, null_pp.max(), p_val, 1.0 / (B1 + 1), p_val_addone))

# ---------- 2) BOOTSTRAP ----------
B2 = 4000
idx_single = np.where(multi == 0)[0]
idx_multi = np.where(multi == 1)[0]
p1_b = np.empty(B2); pmulti_b = np.empty(B2); ratenow_b = np.empty(B2)
for b in range(B2):
    s = rng.integers(0, N, N)  # resample con reemplazo
    lab = det[s]; mk = multi[s]
    p1_b[b] = lab[mk == 0].mean()
    pmulti_b[b] = lab[mk == 1].mean()
    ratenow_b[b] = lab.mean()
avoid_today = (ratenow_b - p1_b) * 10000  # detractores evitables por 10k si multi=single
bt = {"avoid_today_median": float(np.median(avoid_today)),
      "avoid_today_p05": float(np.percentile(avoid_today, 5)),
      "avoid_today_p95": float(np.percentile(avoid_today, 95))}
# histograma avoid_today
ce, cc = np.histogram(avoid_today, bins=28)
boot_hist = {"centers": ((cc[:-1] + cc[1:]) / 2).round(1).tolist(), "counts": ce.tolist()}
print("BOOT avoidable/10k hoy: mediana=%.0f  [%.0f, %.0f]" %
      (bt["avoid_today_median"], bt["avoid_today_p05"], bt["avoid_today_p95"]))

# ---------- 2b) CLUSTER BOOTSTRAP por seller_id (IC honesto ante correlacion intra-vendedor) ----------
# Remuestrea VENDEDORES con reemplazo y agrega sus totales (estadisticos suficientes por cluster).
cl = pd.DataFrame({"seller": cli["seller_id"].values, "det": det, "multi": multi})
n_no_seller = int(cl["seller"].isna().sum())
cl = cl.dropna(subset=["seller"])
cl["single"] = (cl["multi"] == 0).astype(int)
cl["multif"] = (cl["multi"] == 1).astype(int)
g = cl.groupby("seller")
n0 = g["single"].sum().values.astype(float)              # pedidos de 1 item por vendedor
s0 = (cl["det"] * cl["single"]).groupby(cl["seller"]).sum().values.astype(float)  # detractores single
n1 = g["multif"].sum().values.astype(float)              # pedidos multi por vendedor
s1 = (cl["det"] * cl["multif"]).groupby(cl["seller"]).sum().values.astype(float)  # detractores multi
nC = len(n0)
Bc = 4000
avoid_c = np.empty(Bc)
for b in range(Bc):
    mult = np.bincount(rng.integers(0, nC, nC), minlength=nC).astype(float)
    N0 = mult @ n0; S0 = mult @ s0; N1 = mult @ n1; S1 = mult @ s1
    p1c = S0 / N0
    ratec = (S0 + S1) / (N0 + N1)
    avoid_c[b] = (ratec - p1c) * 10000
btc = {"n_clusters": int(nC), "n_sin_vendedor": n_no_seller, "B": Bc,
       "avoid_today_median": float(np.median(avoid_c)),
       "avoid_today_p05": float(np.percentile(avoid_c, 5)),
       "avoid_today_p95": float(np.percentile(avoid_c, 95))}
print("CLUSTER-BOOT (por vendedor, nC=%d): mediana=%.0f  [%.0f, %.0f]" %
      (nC, btc["avoid_today_median"], btc["avoid_today_p05"], btc["avoid_today_p95"]))

# ---------- 3) PROYECCION con banda (bootstrap x escenarios) ----------
shares = [round(float(x), 2) for x in np.arange(0.10, 0.61, 0.05)]
med, plo, phi = [], [], []
for m in shares:
    rate = (1 - m) * p1_b + m * pmulti_b  # sin control
    med.append(round(float(np.median(rate)) * 100, 3))
    plo.append(round(float(np.percentile(rate, 5)) * 100, 3))
    phi.append(round(float(np.percentile(rate, 95)) * 100, 3))
proj = {"shares": shares, "median": med, "lo": plo, "hi": phi,
        "control": round(float(np.median(p1_b)) * 100, 3)}

mc = {"perm": perm, "boot_today": {**bt, "hist": boot_hist}, "boot_today_cluster": btc,
      "proj": proj, "n_ontime": int(N), "multi_share_now": round(float(multi.mean()), 4)}
out = os.path.join(BASE, "outputs", "reports", "montecarlo_items.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(mc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Guardado:", out)
