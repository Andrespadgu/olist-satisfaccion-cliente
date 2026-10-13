# -*- coding: utf-8 -*-
"""PARTE 2: dashboard/dashboard_payload.json — arrays compactos + concepto + explicacion simple."""
import json, os, datetime
import numpy as np, pandas as pd
import scipy.stats as st

BASE = r"C:\Users\ANDRES\Desktop\Maquinas no supervisadas"
PROC = BASE + r"\data\processed"
os.makedirs(BASE + r"\dashboard", exist_ok=True)

REGION_MAP = {}
for r, ufs in {"Norte": "AM,PA,AC,RO,RR,AP,TO", "Nordeste": "MA,PI,CE,RN,PB,PE,AL,SE,BA",
               "Centro-Oeste": "MT,MS,GO,DF", "Sudeste": "SP,RJ,MG,ES", "Sur": "PR,SC,RS"}.items():
    for uf in ufs.split(","):
        REGION_MAP[uf] = r
REGIONES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sur"]

MACROS = ["Tecnología", "Muebles y Hogar", "Moda y Cuidado personal", "Deporte y Juguetes",
          "Libros, Música y Arte", "Alimentos y Bebidas", "Auto, Herramientas e Industria", "Otros"]
def macro_of(c):
    if not isinstance(c, str): return "Otros"
    c = c.lower()
    if any(k in c for k in ['book','cds','dvd','music','stationery','art']): return "Libros, Música y Arte"
    if any(k in c for k in ['fashion','health_beauty','perfum','beauty','luggage','baby','diaper','watches','fashio']): return "Moda y Cuidado personal"
    if any(k in c for k in ['computer','tele','tablet','electronic','pc_','audio','console','_games','cine_photo','image','phone']): return "Tecnología"
    if any(k in c for k in ['auto','construction_tools','costruction','_tools','industry','agro','security','signaling','market_place']): return "Auto, Herramientas e Industria"
    if any(k in c for k in ['furniture','home','house','kitchen','bed_bath','la_cuisine','decor','appliance','housewares','condition','construction','comfort','confort']): return "Muebles y Hogar"
    if any(k in c for k in ['sport','toy','leisure','party','christmas','cool_stuff','fun','games']): return "Deporte y Juguetes"
    if any(k in c for k in ['food','drink']): return "Alimentos y Bebidas"
    return "Otros"

# centroides aproximados por UF (lat, lng)
UF_CENT = {"AC":(-9.0,-70.0),"AL":(-9.6,-36.6),"AP":(1.0,-52.0),"AM":(-4.2,-64.0),"BA":(-12.5,-41.7),
 "CE":(-5.2,-39.6),"DF":(-15.8,-47.9),"ES":(-19.6,-40.6),"GO":(-16.0,-49.6),"MA":(-5.0,-45.3),
 "MT":(-13.0,-56.0),"MS":(-20.5,-54.6),"MG":(-18.5,-44.5),"PA":(-4.0,-53.0),"PB":(-7.1,-36.8),
 "PR":(-24.5,-51.5),"PE":(-8.4,-37.9),"PI":(-7.5,-42.5),"RJ":(-22.3,-42.8),"RN":(-5.8,-36.6),
 "RS":(-30.0,-53.5),"RO":(-10.9,-63.0),"RR":(2.0,-61.4),"SC":(-27.3,-50.5),"SP":(-22.2,-48.7),
 "SE":(-10.6,-37.4),"TO":(-10.2,-48.3)}

def rj(p):
    with open(p, encoding="utf-8") as f: return json.load(f)
RES = rj(BASE + r"\outputs\reports\resultados.json")
RESD = rj(BASE + r"\outputs\reports\resultados_dashboard.json")
RC = rj(BASE + r"\outputs\reports\resultados_comportamiento.json")
MC = rj(BASE + r"\outputs\reports\montecarlo_items.json")
def inn(x): return None if pd.isna(x) else int(round(float(x)))

# ---------------- CLIENTE ----------------
print("Cargando cliente...")
cli = pd.read_csv(PROC + r"\analitico_cliente.csv")
cli["region"] = cli["customer_state"].map(REGION_MAP)
cli["ym"] = pd.to_datetime(cli["order_purchase_timestamp"], errors="coerce").dt.strftime("%Y-%m")
cli = cli[cli["region"].notna() & cli["ym"].notna()].copy()
cli["macro"] = cli["product_category_name_english"].map(macro_of)
# nº de categorias y vendedores distintos por pedido (desde crudos, product_id ya no esta en products_clean)
_it = pd.read_csv(PROC + r"\olist_order_items_clean.csv", usecols=["order_id", "product_id", "seller_id"])
_pr = pd.read_csv(BASE + r"\data\raw\olist_products_dataset.csv", usecols=["product_id", "product_category_name"])
_tr = pd.read_csv(BASE + r"\data\raw\product_category_name_translation.csv")
_pr = _pr.merge(_tr, on="product_category_name", how="left")
_it = _it.merge(_pr[["product_id", "product_category_name_english"]], on="product_id", how="left")
_g = _it.groupby("order_id").agg(n_cat=("product_category_name_english", "nunique"),
                                 n_sel=("seller_id", "nunique")).reset_index()
cli = cli.merge(_g, on="order_id", how="left")
estados = sorted(cli["customer_state"].dropna().unique().tolist())
categorias = sorted(cli["product_category_name_english"].dropna().unique().tolist())
pagos = sorted(cli["payment_type"].dropna().unique().tolist())
meses = sorted(cli["ym"].dropna().unique().tolist())
ri = {r: i for i, r in enumerate(REGIONES)}; ei = {e: i for i, e in enumerate(estados)}
ci = {c: i for i, c in enumerate(categorias)}; pi = {p: i for i, p in enumerate(pagos)}
mi = {m: i for i, m in enumerate(meses)}; macI = {m: i for i, m in enumerate(MACROS)}

cliente_rows = []
for t in cli.itertuples(index=False):
    ratio = None if pd.isna(t.ratio_flete_precio) else int(round(float(t.ratio_flete_precio) * 100))
    ontime = None if pd.isna(t.dias_retraso) else (1 if float(t.dias_retraso) <= 0 else 0)
    cliente_rows.append([ri[t.region], ei.get(t.customer_state, -1), ci.get(t.product_category_name_english, -1),
                         pi.get(t.payment_type, -1), mi[t.ym], int(t.review_score), inn(t.dias_retraso),
                         inn(t.tiempo_entrega_dias), ratio, inn(t.distancia_seller_customer_km), ontime,
                         inn(t.payment_installments) or 0, inn(t.n_items) or 1, macI[t.macro],
                         inn(t.n_cat) or 1, inn(t.n_sel) or 1])
print("cliente rows:", len(cliente_rows))

# ---------------- VENDEDOR ----------------
print("Cargando vendedor...")
ven = pd.read_csv(PROC + r"\analitico_vendedor.csv")
ven["region"] = ven["seller_state"].map(REGION_MAP); ven = ven[ven["region"].notna()].copy()
def x100(v): return None if pd.isna(v) else int(round(float(v) * 100))
def x10(v): return None if pd.isna(v) else int(round(float(v) * 10))
vendedor_rows = []
for t in ven.itertuples(index=False):
    vendedor_rows.append([ri[t.region], ei.get(t.seller_state, -1), x100(t.review_score_promedio),
                          x10(t.pct_despachos_tardios), x10(t.pct_cancelados), x10(t.tiempo_despacho_promedio_dias),
                          inn(t.volumen_ventas) or 0, int(t.n_pedidos), inn(t.distancia_promedio_a_clientes),
                          x100(t.ratio_flete_precio_promedio)])
print("vendedor rows:", len(vendedor_rows))

# ================= CALCULOS NUEVOS (estatica de referencia) =================
deliv = cli[(cli["order_status"] == "delivered") & cli["dias_retraso"].notna()].copy()
def eff_r(x):
    x = abs(x); return "insignificante" if x < .1 else "pequeño" if x < .3 else "mediano" if x < .5 else "grande"
def eff_v(x):
    return "insignificante" if x < .1 else "pequeño" if x < .2 else "moderado" if x < .4 else "fuerte"
def eps2_kw(groups):
    groups = [g for g in groups if len(g) > 0]; k = len(groups); n = sum(len(g) for g in groups)
    H, p = st.kruskal(*groups); return H, p, (H - k + 1) / (n - k)

# pago x tarde (independencia)
ot = deliv[deliv["dias_retraso"].notna()].copy(); ot["late"] = (ot["dias_retraso"] > 0).astype(int)
tab = pd.crosstab(ot["payment_type"], ot["late"])
chi2_pl, p_pl, dof_pl, _ = st.chi2_contingency(tab)
V_pl = float(np.sqrt(chi2_pl / (tab.values.sum() * (min(tab.shape) - 1))))
pct_late_pay = (100 * tab[1] / tab.sum(axis=1)).round(1).to_dict()
# n_items vs review
rho_ni, p_ni = st.spearmanr(deliv["n_items"], deliv["review_score"])
# macro vs review
gR = [g["review_score"].values for _, g in deliv.groupby("macro")]
Hm, pm, eps2_mr = eps2_kw(gR)
# macro vs retraso
gD = [g["dias_retraso"].values for _, g in deliv.groupby("macro")]
Hd, pd_, eps2_md = eps2_kw(gD)
# por macro: review medio y retraso mediano -> spearman entre ellos
macro_stat = deliv.groupby("macro").agg(rev=("review_score", "mean"), ret=("dias_retraso", "median")).reindex(MACROS).dropna()
rho_macro, p_macro = st.spearmanr(macro_stat["rev"], macro_stat["ret"])
# distancia -> dias de entrega
dd = deliv.dropna(subset=["distancia_seller_customer_km", "tiempo_entrega_dias"])
rho_de, p_de = st.spearmanr(dd["distancia_seller_customer_km"], dd["tiempo_entrega_dias"])
# nº de items / categorias vs TIEMPO de entrega
rho_ni_t, _ = st.spearmanr(deliv["n_items"], deliv["tiempo_entrega_dias"], nan_policy="omit")
rho_nc_t, _ = st.spearmanr(deliv["n_cat"], deliv["tiempo_entrega_dias"], nan_policy="omit")
_multi = deliv[deliv["n_items"] >= 2]
_mono_t = _multi[_multi["n_cat"] == 1]["tiempo_entrega_dias"].dropna()
_var_t = _multi[_multi["n_cat"] >= 2]["tiempo_entrega_dias"].dropna()
_U, _ = st.mannwhitneyu(_mono_t, _var_t); rbc_cat = round(1 - 2 * _U / (len(_mono_t) * len(_var_t)), 3)
med_mono, med_var = round(float(_mono_t.median()), 1), round(float(_var_t.median()), 1)
print(f"tiempo: rho(nitems)={rho_ni_t:.3f} rho(ncat)={rho_nc_t:.3f} | mono {med_mono}d vs varias {med_var}d rbc={rbc_cat}")
print(f"pago->tarde V={V_pl:.3f} | %late={pct_late_pay} | nitems rho={rho_ni:.3f} | macro-rev eps2={eps2_mr:.4f} | dist->entrega rho={rho_de:.3f}")

# mapas por categoria: origen (vendedor) vs destino (cliente)
def bubbles(series):
    out = []
    for uf, n in series.value_counts().items():
        if uf in UF_CENT:
            out.append({"uf": uf, "lat": UF_CENT[uf][0], "lng": UF_CENT[uf][1], "n": int(n)})
    return out
def mapa_for(macro_name):
    sub = deliv[deliv["macro"] == macro_name]
    rho, _ = st.spearmanr(sub["distancia_seller_customer_km"], sub["tiempo_entrega_dias"], nan_policy="omit")
    return {"macro": macro_name, "seller_states": bubbles(sub["seller_state"]), "customer_states": bubbles(sub["customer_state"]),
            "dist_med_cat": int(sub["distancia_seller_customer_km"].median()),
            "dist_med_global": int(deliv["distancia_seller_customer_km"].median()),
            "rho_dist_ent": round(float(rho), 3), "pct_sellers_sp": round(100 * (sub["seller_state"] == "SP").mean(), 1),
            "ent_med_cat": round(float(sub["tiempo_entrega_dias"].median()), 1),
            "ent_med_global": round(float(deliv["tiempo_entrega_dias"].median()), 1), "n": int(len(sub))}
mapa_muebles = mapa_for("Muebles y Hogar")
mapa_tecnologia = mapa_for("Tecnología")
for nm, mp in [("muebles", mapa_muebles), ("tecnologia", mapa_tecnologia)]:
    print("mapa %s: n=%d, sellers SP=%.1f%%, dist_cat=%d vs global=%d, ent_cat=%.1f vs global=%.1f, rho=%.2f" %
          (nm, mp["n"], mp["pct_sellers_sp"], mp["dist_med_cat"], mp["dist_med_global"], mp["ent_med_cat"], mp["ent_med_global"], mp["rho_dist_ent"]))

# ===== SIMULACION: efecto del nº de items sobre la insatisfaccion (aislado del tiempo) =====
ot = cli[(cli["order_status"] == "delivered") & (cli["dias_retraso"] <= 0)].copy()
ot["k"] = ot["n_items"].clip(upper=5)
p_by_k = [round(float((ot[ot["k"] == k]["review_score"] <= 2).mean()), 4) for k in [1, 2, 3, 4, 5]]
share_k = [round(float((ot["k"] == k).mean()), 4) for k in [1, 2, 3, 4, 5]]
p1 = p_by_k[0]
pred_weak = [round(1 - (1 - p1) ** k, 4) for k in [1, 2, 3, 4, 5]]
w_multi = [float((ot["k"] == k).sum()) for k in [2, 3, 4, 5]]; sw = sum(w_multi)
pmulti = round(sum(p_by_k[k - 1] * w_multi[k - 2] for k in [2, 3, 4, 5]) / sw, 4)
multi_share_now = round(float((ot["n_items"] >= 2).mean()), 4)
rate_now = round(sum(p_by_k[k - 1] * share_k[k - 1] for k in [1, 2, 3, 4, 5]), 4)
mfrag = ot[ot["n_items"] >= 2]
frag_uno = round(float((mfrag[mfrag["n_sel"] == 1]["review_score"] <= 2).mean()), 4)
frag_var = round(float((mfrag[mfrag["n_sel"] >= 2]["review_score"] <= 2).mean()), 4)
proj_shares = [round(float(x), 2) for x in np.arange(0.10, 0.61, 0.05)]
proj_nc = [round((1 - m) * p1 + m * pmulti, 4) for m in proj_shares]
imp = {"hoy": round((rate_now - p1) * 10000), "m30": round((0.7 * p1 + 0.3 * pmulti - p1) * 10000),
       "m50": round((0.5 * p1 + 0.5 * pmulti - p1) * 10000)}
simulacion = {"labels_k": ["1", "2", "3", "4", "5+"], "p_by_k": p_by_k, "pred_weak": pred_weak, "share_k": share_k,
              "p1": p1, "pmulti": pmulti, "multi_share_now": multi_share_now, "rate_now": rate_now,
              "frag": {"un_vendedor": frag_uno, "varios": frag_var},
              "proj_shares": proj_shares, "proj_nocontrol": proj_nc, "proj_control": p1, "impacto_10k": imp}
print("sim: p1=%.3f pmulti=%.3f multi_now=%.3f frag %0.3f->%0.3f imp_hoy=%d" % (p1, pmulti, multi_share_now, frag_uno, frag_var, imp["hoy"]))

# ---------------- referencias previas ----------------
c5 = RES["c5_esperanza_var"]; c6 = RES["c6_correlacion"]; c10 = RES["c10_kl"]; c11 = RES["c11_chi2_pay_review"]
H1 = RES["H1"]; H3 = RES["H3"]; D1 = RESD["D1"]; D2 = RESD["D2"]; H6 = RESD["H6"]; H7 = RESD["H7"]; H5 = RESD["H5"]
gan = D2["ganador"]; reg_eps2 = [r for r in D2["ranking"] if r["var"] == "region"][0]
p1 = RC["p1_saturacion_volumen"]; p2 = RC["p2_dispersion_rK_comportamiento"]; p3 = RC["p3_distancia_despacho"]
p4 = RC["p4_cancelacion_vs_tardanza"]; p5 = RC["p5_geografia"]; p6 = RC["p6_ranking_driver_despacho_tardio"]; p7 = RC["p7_comportamiento_a_resultado"]
h3_rho = H3.get("rho_ratio_review_puntuales", -0.032)
pl_txt = ", ".join(f"{k} {v}%" for k, v in sorted(pct_late_pay.items(), key=lambda x: -x[1]))

stats = {
 "dist_review": f"Descriptivo, sin prueba de hipotesis. Media E[review]={c5['E_global']}, varianza={c5['Var_global']}. Forma en J.",
 "review_vs_retraso": f"Spearman rho={H1['rho_retraso']} (tarde) vs {H1['rho_adelanto']} (adelanto); Kruskal-Wallis eps2={H1['kruskal_eps2']} (mediano). Asimetria {H1['ratio_asimetria_caida/subida_MEDIA']}x.",
 "regional_olist_vs_mercado": f"Divergencia KL(Olist||mercado)={D1['kl_bits']} bits; chi2={D1['chi2']}, V de Cramer={D1['cramers_v']}. Conceptos: KL / entropia cruzada.",
 "review_por_region": f"Kruskal-Wallis entre regiones eps2={reg_eps2['valor']} (insignificante); KL(SP||Nordeste)={c10['SP_vs_Nordeste']['KL(NE||SP)_bits']} bits.",
 "pago_vs_tarde": f"Chi-cuadrado de INDEPENDENCIA (metodo de pago x llego tarde): chi2={round(chi2_pl,1)}, V de Cramer={round(V_pl,3)} ({eff_v(V_pl)}). Se recalcula con tus filtros. % de tardios por metodo: {pl_txt}.",
 "review_vs_ratioflete": f"Spearman rho(ratio flete/precio, review)={h3_rho} en puntuales (trivial). Correlacion de rangos.",
 "entrega_vs_distancia": f"Spearman rho(distancia km, dias de entrega)={round(rho_de,3)} ({eff_r(rho_de)}, p<0.001, n={len(dd):,}). Correlacion de rangos.",
 "review_vs_nitems": f"Spearman rho(n de items, review)={round(rho_ni,3)} ({eff_r(rho_ni)}, p<0.001). Fue la 2a causa NO temporal. Correlacion de rangos.",
 "detractores_vs_nitems": "Probabilidad condicional: P(review<=2 | n de items del pedido). Descriptivo por grupo.",
 "tiempo_vs_nitems": f"Spearman rho(n de items, dias de entrega)={round(rho_ni_t,3)} (insignificante). El tiempo NO es proporcional al n de items.",
 "tiempo_mono_vs_multicat": f"Mann-Whitney (1 categoria vs varias, en pedidos de 2+ items): rank-biserial={rbc_cat}. Medianas: 1 categoria {med_mono} dias vs varias {med_var} dias. Spearman rho(n categorias, tiempo)={round(rho_nc_t,3)}.",
 "sim_weakest": f"P(detractor 1-2★ | nº ítems) en pedidos ENTREGADOS A TIEMPO (aísla el efecto del tiempo). Modelo 'eslabón más débil' = 1-(1-p)^k con p={p1}. Observado (2 ítems={p_by_k[1]}) SUPERA al modelo.",
 "sim_fragmentacion": f"Probabilidad condicional. En pedidos de 2+ ítems: P(detractor | 1 vendedor)={frag_uno} vs P(detractor | varios vendedores)={frag_var}.",
 "sim_proyeccion": f"Simulación: tasa de detractores = (1-m)·{p1} + m·{pmulti}, con m = % de pedidos multi-ítem. Hoy m={multi_share_now}. Modelo lineal, no pronóstico fechado.",
 "sim_impacto": f"Clientes insatisfechos EVITABLES por cada 10.000 pedidos si el multi-ítem se cumpliera como el 1-ítem. Hoy ≈{imp['hoy']}; si el multi-ítem sube al 30% ≈{imp['m30']}; al 50% ≈{imp['m50']}.",
 "mc_permutacion": f"Prueba de permutación Monte Carlo ({MC['perm']['B']:,} barajados que rompen el vínculo ítems↔detractor). Brecha observada = {MC['perm']['observed_pp']} pp; máximo bajo azar = {MC['perm']['null_max_pp']} pp; p-valor < {MC['perm']['p_upper_bound']}.",
 "mc_impacto_dist": f"Bootstrap Monte Carlo (4.000 remuestreos): detractores evitables hoy por 10.000 pedidos = mediana {round(MC['boot_today']['avoid_today_median'])} (IC 90%: {round(MC['boot_today']['avoid_today_p05'])}–{round(MC['boot_today']['avoid_today_p95'])}; cluster por vendedor: {round(MC['boot_today_cluster']['avoid_today_p05'])}–{round(MC['boot_today_cluster']['avoid_today_p95'])}).",
 "mc_proyeccion_banda": f"Bootstrap: tasa de detractores según % multi-ítem con banda del 90%. Línea de control = {MC['proj']['control']}%. Concepto: intervalo de confianza por remuestreo.",
 "review_por_macrocat": f"Kruskal-Wallis entre macro-categorias: H={round(Hm,1)}, eps2={round(eps2_mr,4)} ({eff_v(eps2_mr) if eps2_mr>=0 else 'insignificante'}).",
 "demora_por_macrocat": f"Kruskal-Wallis del retraso entre macro-categorias eps2={round(eps2_md,4)}. Spearman entre (calificacion media) y (retraso mediano) por macro-categoria = {round(rho_macro,3)} (n={len(macro_stat)} grupos).",
 "segunda_causa": f"Fuerza de cada factor = varianza de review explicada (rho2 / eps2). Se INCLUYE el tiempo (rojo) como referencia: domina. Entre los NO temporales el mayor es {gan['var']} (rho2={gan['valor']}).",
 "comp_tardios_dist": f"Descriptivo (KDE). % de despachos tardios por vendedor (n>=5 pedidos, {RC['meta']['n_sellers_tras_excluir_n<5']} vendedores).",
 "comp_volumen_vs_tardios": f"Spearman rho(n_pedidos, %tardios)={p1['spearman_npedidos_pct_tardio']['rho']} (pequeno); Kruskal eps2={p1['kruskal_pct_tardio_entre_deciles']['eps2']}. Medianas por banda: 0% -> 4.5% -> 5.2%.",
 "comp_volumen_vs_dispersion": f"Fligner-Killeen stat={p2['fligner_killeen_pct_tardio_entre_bandas']['stat']}, p={p2['fligner_killeen_pct_tardio_entre_bandas']['p']:.3f}. IQR cae 15.4 -> 11.6 -> 9.2 al crecer volumen.",
 "comp_distancia_vs_despacho": f"Spearman rho(distancia, tiempo despacho)={p3['bruto']['spearman_distancia_tiempo_despacho']['rho']} (insignificante); rho(distancia, %tardios)={p3['bruto']['spearman_distancia_pct_tardio']['rho']} (nulo).",
 "comp_cancel_vs_tardios": f"Spearman rho(%cancelados, %tardios)={p4['spearman_pct_cancelados_pct_tardio']['rho']} (pequeno, positivo).",
 "comp_region": f"Kruskal-Wallis %tardios entre regiones H={p5['kruskal_pct_tardio_entre_regiones']['H']}, p={p5['kruskal_pct_tardio_entre_regiones']['p']:.2f}, eps2 aprox 0.",
 "comp_drivers": f"Ranking por varianza explicada del %despacho tardio: volumen rho2={p6['ranking'][0]['valor']} (unico no trivial); flete {p6['ranking'][1]['valor']}; distancia {p6['ranking'][2]['valor']}; region aprox 0.",
 "comp_comportamiento_vs_review": f"Spearman rho(%tardios, review)={p7['spearman_pct_tardio_review']['rho']} y rho(tiempo despacho, review)={p7['spearman_tiempo_despacho_review']['rho']} (medianos). El comportamiento explica ~{round(p7['pct_varianza_review_por_comportamiento_tardio'])}% del review.",
}
explica = {
 "dist_review": "La mayoria califica 5★ y hay un grupo que da 1★. La gente tiende a estar muy contenta o muy molesta.",
 "review_vs_retraso": "Si el pedido llega tarde, la nota se desploma; llegar antes casi no la sube. Lo clave es cumplir la fecha prometida.",
 "regional_olist_vs_mercado": "Olist vende proporcionalmente MAS en el Sudeste que el promedio del pais, y MUCHO menos en Norte y Nordeste. Esta concentrada donde la logistica es facil.",
 "review_por_region": "Las regiones peor conectadas califican algo mas bajo, pero poco: no es que el cliente sea mas exigente, es que le llega tarde mas seguido.",
 "pago_vs_tarde": "Aqui vemos si el metodo de pago cambia la probabilidad de que el pedido llegue TARDE (no la satisfaccion). El boleto tarda 1-3 dias en aprobarse, asi que puede retrasar el arranque. Mira las barras: si el % de tardios es parecido entre metodos, el pago casi no influye en la tardanza.",
 "review_vs_ratioflete": "Entre pedidos a tiempo, pagar mas flete respecto al precio casi no baja la nota. El flete molesta al comprar, no al calificar si llega bien.",
 "entrega_vs_distancia": "Cuanto mas lejos esta el vendedor del cliente (mas km), mas dias tarda en llegar el pedido. Este grafico muestra esa relacion: la distancia es un motor directo del tiempo de entrega.",
 "review_vs_nitems": "Cuantos mas productos trae un pedido, un poco peor tiende a ser la calificacion: mas items = mas cosas que pueden salir mal (uno llega dañado, otro tarde). Es la 2a causa mas fuerte fuera del tiempo.",
 "detractores_vs_nitems": "Muestra el % de clientes muy molestos (1-2★) segun cuantos items pidieron. Si sube con el nº de items, confirma que los pedidos grandes son mas riesgosos.",
 "tiempo_vs_nitems": "El nº de items NO alarga la entrega: la linea es casi plana (rho ~ -0.03). Un pedido de 5 items tarda casi lo mismo (o incluso menos) que uno de 1. El tiempo lo manda la distancia y el vendedor, no cuantas cosas pidas.",
 "tiempo_mono_vs_multicat": "Pedir de VARIAS categorias NO demora mas; al contrario, esos pedidos llegan un poco ANTES (probablemente porque vienen de vendedores grandes/profesionales de Sao Paulo). Asi que 'varias categorias' NO explica la tardanza.",
 "sim_weakest": "Aqui esta el PORQUE: un pedido de 1 item molesta al 7.5% de clientes; uno de 2 items, al 23% (casi el triple). Cada producto extra es otra cosa que puede llegar danada, incompleta o mal. Y sube incluso mas rapido de lo que predice el azar (linea gris): porque mas items suele significar mas envios separados.",
 "sim_fragmentacion": "La causa concreta del 'eslabon mas debil': cuando el pedido viene de VARIOS vendedores (varios paquetes que llegan por separado), el descontento se dispara del 21% al 47%. Basta que UN paquete falle para hundir la nota de TODO el pedido.",
 "sim_proyeccion": "¿Vale la pena? Si la canasta promedio crece (mas pedidos multi-item) y no se hace nada, la tasa de clientes insatisfechos sube en linea recta (roja). Si se controla el cumplimiento multi-item, se queda plana en el minimo (verde). Hoy el efecto es chico (~10% de pedidos son multi-item), pero crece con ese %.",
 "sim_impacto": "Traducido a personas: por cada 10.000 pedidos, cuantos clientes insatisfechos te ahorrarias si los pedidos multi-item se cumplieran tan bien como los de un solo item. Es una palanca barata (empaque/completitud/consolidacion) e independiente del tiempo de entrega.",
 "mc_permutacion": "Otra perspectiva: barajamos al azar 5.000 veces quién quedó insatisfecho, borrando toda relación con el nº de ítems. En ese mundo aleatorio la diferencia entre multi y 1-ítem NUNCA pasó de ~1 punto; en la realidad es de 17 puntos. Conclusión: es IMPOSIBLE que sea casualidad — el nº de ítems SÍ importa.",
 "mc_impacto_dist": "Repetimos el cálculo 4.000 veces sobre muestras distintas de los mismos datos. El ahorro de clientes molestos por cada 10.000 pedidos cae casi siempre entre 165 y 181. O sea, el número (~173) es sólido, no un accidente de la muestra.",
 "mc_proyeccion_banda": "La proyección CON su margen de error (banda del 90%). Aunque haya incertidumbre, la línea sin control sube claramente al crecer el multi-ítem y su banda nunca toca la línea verde de control: la conclusión aguanta estadísticamente.",
 "review_por_macrocat": f"OJO con las diferencias: aunque una familia se ve peor que otra, la diferencia es PRACTICAMENTE NULA. La familia de producto explica solo ~{round(eps2_mr*100,1)}% de la variacion en la nota (eps2={round(eps2_mr,4)}). Con {len(deliv):,} pedidos el test da 'significativo', pero en la practica TODAS las familias se califican casi igual (entre 4.1 y 4.3 estrellas): no vale la pena priorizar por categoria. Lo que manda es el tiempo de entrega.",
 "demora_por_macrocat": "Compara la calificacion y la demora por familia de producto. Si las familias peor calificadas son tambien las que mas se demoran, la mala nota es sobre todo un problema de tiempo, no del producto.",
 "segunda_causa": "El tiempo de entrega domina todo (barras rojas). Dejandolo de lado, lo que mas pesa es el nº de items y luego la categoria. Ninguno se acerca al tiempo.",
 "comp_tardios_dist": "La mayoria de vendedores despacha casi siempre a tiempo. Solo una minoria concentra los incumplimientos.",
 "comp_volumen_vs_tardios": "A mas pedidos, el vendedor se retrasa un poco mas al despachar, pero se estanca: la escala satura su capacidad, no la destruye.",
 "comp_volumen_vs_dispersion": "Los vendedores grandes son mas predecibles; los pequenos son una loteria (unos perfectos, otros pesimos).",
 "comp_distancia_vs_despacho": "La distancia NO cambia lo rapido que el vendedor despacha. Afecta la entrega final (transportador), no lo que el controla. No hay que culparlo por vender lejos.",
 "comp_cancel_vs_tardios": "Los que cancelan mas tambien despachan mas tarde: son el mismo 'vendedor problematico', aunque el vinculo es debil.",
 "comp_region": "La region del vendedor no explica su cumplimiento: se despacha igual de bien (o mal) en todo Brasil.",
 "comp_drivers": "De todo lo que podria explicar que un vendedor despache tarde, solo su volumen importa (y poco). Distancia, flete y region son irrelevantes.",
 "comp_comportamiento_vs_review": "Lo que el vendedor controla (despachar a tiempo) explica solo ~11-14% de su calificacion. El resto depende del transportador y del producto.",
 "mapa_muebles": ("Azul = de dónde SALEN los muebles (vendedores); naranja = a dónde VAN (clientes). Casi todos los vendedores están en São Paulo (" + str(mapa_muebles['pct_sellers_sp']) + "%) y los clientes se reparten por Brasil. Dentro de la categoría, a más distancia SÍ tarda más (ρ=" + str(mapa_muebles['rho_dist_ent']) + "). PERO estos productos NO viajan más lejos que el promedio (" + str(mapa_muebles['dist_med_cat']) + " km vs " + str(mapa_muebles['dist_med_global']) + " km global): su demora extra NO es por distancia, sino porque son voluminosos/pesados (más difíciles de manejar y despachar)."),
}
stats["mapa_muebles"] = (f"Descriptivo (mapa) + Spearman. {mapa_muebles['n']:,} pedidos de Muebles y Hogar. "
                         f"Vendedores en SP: {mapa_muebles['pct_sellers_sp']}%. Distancia mediana {mapa_muebles['dist_med_cat']} km "
                         f"(vs {mapa_muebles['dist_med_global']} km global). Spearman(distancia, días de entrega) dentro de la categoría = {mapa_muebles['rho_dist_ent']}.")
stats["mapa_tecnologia"] = (f"Descriptivo (mapa) + Spearman. {mapa_tecnologia['n']:,} pedidos de Tecnología. "
                            f"Vendedores en SP: {mapa_tecnologia['pct_sellers_sp']}%. Distancia mediana {mapa_tecnologia['dist_med_cat']} km "
                            f"(vs {mapa_tecnologia['dist_med_global']} km global). Días de entrega {mapa_tecnologia['ent_med_cat']} (vs {mapa_tecnologia['ent_med_global']} global). "
                            f"Spearman(distancia, días de entrega) dentro de la categoría = {mapa_tecnologia['rho_dist_ent']}.")
explica["mapa_tecnologia"] = ("Azul = de dónde SALEN los productos de tecnología (vendedores); naranja = a dónde VAN (clientes). "
    "Igual que muebles, los vendedores se concentran en São Paulo (" + str(mapa_tecnologia['pct_sellers_sp']) + "%). "
    "PERO aquí la distancia SÍ es un factor: estos productos viajan MÁS lejos que el promedio (" + str(mapa_tecnologia['dist_med_cat']) +
    " km vs " + str(mapa_tecnologia['dist_med_global']) + " km global) y es la categoría que MÁS tarda (" + str(mapa_tecnologia['ent_med_cat']) +
    " días vs " + str(mapa_tecnologia['ent_med_global']) + " global). Dentro de la categoría, a más distancia más demora (ρ=" +
    str(mapa_tecnologia['rho_dist_ent']) + "). A diferencia de muebles, en tecnología la lejanía SÍ ayuda a explicar la tardanza.")

regional = {"olist": D1["olist_pct"], "mercado": D1["mercado_pct"], "kl_bits": D1["kl_bits"],
            "cramers_v": D1["cramers_v"], "chi2": D1["chi2"], "ratio": D1["ratio_olist_vs_mercado"], "nota": D1["nota"]}
temporal = []
for v in ["tiempo_entrega_dias", "dias_retraso"]:
    temporal.append({"var": v, "valor": round(c6[v]["rho"] ** 2, 6), "temporal": True})
no_temp = [{"var": r["var"], "valor": r["valor"], "temporal": False} for r in D2["ranking"]]
segunda_causa = {"ranking": sorted(temporal + no_temp, key=lambda d: d["valor"], reverse=True), "ganador": D2["ganador"]}
comportamiento = {"driver": p6["driver_mas_fuerte"], "ranking": p6["ranking"],
                  "review_dependencia_pct": p7["pct_varianza_review_por_comportamiento_tardio"],
                  "nota": ("El comportamiento del vendedor lo explica sobre todo su VOLUMEN de pedidos (rho=+0.20, unico efecto no trivial). "
                           "Distancia, flete y region NO lo explican. Su despacho solo determina ~11-14% de su calificacion.")}

payload = {
 "meta": {"n_cliente": len(cliente_rows), "n_vendedor": len(vendedor_rows), "ym_min": meses[0], "ym_max": meses[-1],
          "generado": datetime.datetime.now().isoformat(timespec="seconds")},
 "dims": {"regiones": REGIONES, "estados": estados, "categorias": categorias, "payment_types": pagos,
          "meses": meses, "macro_categorias": MACROS},
 "cliente": cliente_rows, "vendedor": vendedor_rows,
 "stats": stats, "explica": explica,
 "regional": regional, "segunda_causa": segunda_causa, "comportamiento": comportamiento,
 "mapa_muebles": mapa_muebles, "mapa_tecnologia": mapa_tecnologia, "simulacion": simulacion, "montecarlo": MC,
}
out = BASE + r"\dashboard\dashboard_payload.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
print(f"\nGuardado: {out}  ({os.path.getsize(out)/1e6:.2f} MB) | stats {len(stats)} | explica {len(explica)}")
