# -*- coding: utf-8 -*-
"""Ensambla dashboard/index.html: un solo archivo con Chart.js + datos embebidos (sin internet)."""
import os, urllib.request
BASE = r"C:\Users\ANDRES\Desktop\Maquinas no supervisadas"; DASH = BASE + r"\dashboard"
vendor = DASH + r"\_chartjs.js"
if not os.path.exists(vendor):
    urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js", vendor)
chartjs = open(vendor, encoding="utf-8").read()
payload = open(DASH + r"\dashboard_payload.json", encoding="utf-8").read()
print("Chart.js", round(len(chartjs)/1000), "KB | payload", round(len(payload)/1e6, 2), "MB")

# contorno de Brasil (estados) para el mapa — se descarga una vez y se simplifica
import json as _json
geo_cache = DASH + r"\_brazil.geojson"; brazil_js = "[]"
try:
    if not os.path.exists(geo_cache):
        req = urllib.request.Request("https://raw.githubusercontent.com/giuliano-macedo/geodata-br-states/main/geojson/br_states.json",
                                     headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        open(geo_cache, "wb").write(data)
    gj = _json.load(open(geo_cache, encoding="utf-8")); rings = []
    for feat in gj.get("features", []):
        g = feat.get("geometry") or {}; t = g.get("type"); co = g.get("coordinates")
        if not co: continue
        polys = co if t == "MultiPolygon" else [co]
        for poly in polys:
            outer = poly[0]; step = max(1, len(outer) // 70)
            ring = [[round(p[0], 2), round(p[1], 2)] for p in outer[::step]]
            if len(ring) >= 3: rings.append(ring)
    brazil_js = _json.dumps(rings); print("Brazil rings:", len(rings))
except Exception as e:
    print("geojson fallo, mapa sin contorno:", e); brazil_js = "[]"

HTML = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Olist · Satisfacción y comportamiento — Dashboard probabilístico</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#1f2a37;--muted:#6b7280;--line:#e5e9f0;--a:#2563eb;--a2:#93c5fd;--g:#059669;--r:#dc2626;--y:#d97706;--p:#7c3aed;--slate:#64748b;--shadow:0 1px 3px rgba(16,24,40,.08),0 1px 2px rgba(16,24,40,.04);}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
header{background:linear-gradient(120deg,#1e3a8a,#2563eb);color:#fff;padding:22px 26px}
header h1{margin:0;font-size:20px;font-weight:700}header p{margin:6px 0 0;opacity:.92;font-size:13px;max-width:980px}
.wrap{max-width:1280px;margin:0 auto;padding:18px}
.tabs{display:flex;gap:8px;margin:16px 0 8px}
.tab{padding:10px 18px;border:1px solid var(--line);background:#fff;border-radius:10px;cursor:pointer;font-weight:600;color:var(--muted)}
.tab.active{background:var(--a);color:#fff;border-color:var(--a)}
.filters{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);margin-bottom:16px}
.filters h3{margin:0 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}
.frow{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start}
.fg{display:flex;flex-direction:column;gap:6px}.fg label{font-size:12px;color:var(--muted);font-weight:700}
select{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);font-size:13px}
.chips{display:flex;gap:6px;flex-wrap:wrap;max-width:640px}
.chip{padding:6px 11px;border:1px solid var(--line);border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;color:var(--muted);user-select:none}
.chip.on{background:#e0edff;border-color:var(--a);color:var(--a)}
.reset{cursor:pointer;color:var(--a);font-weight:600;background:none;border:none;font-size:13px;padding:8px 4px;align-self:flex-end}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px 12px;box-shadow:var(--shadow);min-width:0}
.card.full{grid-column:1/-1}.card h4{margin:0 0 2px;font-size:15px}.card .sub{margin:0 0 10px;font-size:12px;color:var(--muted)}
.sec{grid-column:1/-1;background:linear-gradient(120deg,#eef4ff,#f8fbff);border:1px solid #dbe6ff;border-radius:12px;padding:12px 16px}
.sec h3{margin:0;font-size:16px;color:#1e3a8a}.sec p{margin:4px 0 0;font-size:12.5px;color:#475569}
.cwrap{position:relative;height:280px}.cwrap.tall{height:340px}
.stat{margin-top:9px;padding:8px 10px;background:#eff4ff;border-left:3px solid var(--a);border-radius:6px;font-size:11.5px;color:#334155;line-height:1.45}
.stat.none{background:#f6f6f6;border-left-color:#c9ced6;color:#6b7280}
.explica{margin-top:7px;padding:8px 10px;background:#ecfdf5;border-left:3px solid var(--g);border-radius:6px;font-size:12px;color:#065f46;line-height:1.5}
.explica b{color:#064e3b}
.note{margin-top:9px;padding:9px 11px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;font-size:12px;color:#7c2d12}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.kpi{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}
.kpi .v{font-size:22px;font-weight:800;color:var(--a)}.kpi .l{font-size:12px;color:var(--muted)}
.hidden{display:none}footer{color:var(--muted);font-size:12px;text-align:center;padding:22px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
.concepto{margin-top:9px;padding:8px 11px;background:#f5f3ff;border-left:3px solid var(--p);border-radius:6px;font-size:12px;color:#5b21b6;line-height:1.45}
.concepto b{color:#4c1d95}
</style></head><body>
<header><h1>Olist · ¿Qué explica la satisfacción del cliente y el comportamiento del vendedor?</h1>
<p>Base relacional integrada (7 tablas unidas por sus llaves). Estadística <b>no paramétrica</b>; se decide por <b>tamaño de efecto</b>, no por p-valor (n≈96k). Bajo cada gráfico: el concepto usado y qué significa en palabras simples.</p></header>
<div class="wrap">
  <div class="tabs">
    <div class="tab active" data-tab="cliente">👤 Satisfacción del CLIENTE</div>
    <div class="tab" data-tab="vendedor">🏪 Comportamiento del VENDEDOR</div>
    <div class="tab" data-tab="pitch">🎤 Pitch</div>
  </div>

  <!-- ============ CLIENTE ============ -->
  <section id="tab-cliente">
    <div class="filters"><h3>Filtros — vista cliente (todos multi-seleccionables)</h3>
      <div class="frow">
        <div class="fg" style="flex:1 1 100%"><label>Región</label><div class="chips" id="cli-regiones"></div></div>
        <div class="fg" style="flex:1 1 100%"><label>Categoría (agrupada)</label><div class="chips" id="cli-macro"></div></div>
        <div class="fg"><label>Calificación (★)</label><div class="chips" id="cli-rating"></div></div>
        <div class="fg"><label>Método de pago</label><div class="chips" id="cli-pay"></div></div>
        <div class="fg"><label>Desde (mes)</label><select id="cli-from"></select></div>
        <div class="fg"><label>Hasta (mes)</label><select id="cli-to"></select></div>
        <button class="reset" id="cli-reset">↺ Restablecer</button>
      </div>
    </div>
    <div class="kpis" id="cli-kpis"></div>
    <div class="grid">
      <div class="card"><h4>Distribución de calificaciones</h4><p class="sub">¿Cómo se reparten las reseñas 1–5?</p><div class="cwrap"><canvas id="dist_review"></canvas></div><div class="stat" id="s-dist_review"></div><div class="explica" id="e-dist_review"></div></div>
      <div class="card"><h4>Calificación vs. retraso de entrega</h4><p class="sub">Días respecto a la fecha prometida (0 = a tiempo)</p><div class="cwrap"><canvas id="review_vs_retraso"></canvas></div><div class="stat" id="s-review_vs_retraso"></div><div class="explica" id="e-review_vs_retraso"></div></div>
      <div class="card full"><h4>🌎 Distribución regional: Olist vs. mercado e-commerce brasileño</h4><p class="sub">% de pedidos por macro-región (referencia global, no afectada por filtros)</p><div class="cwrap"><canvas id="regional_olist_vs_mercado"></canvas></div><div class="note" id="n-regional"></div><div class="stat" id="s-regional_olist_vs_mercado"></div><div class="explica" id="e-regional_olist_vs_mercado"></div></div>
      <div class="card"><h4>Calificación media por región</h4><p class="sub">Satisfacción media por macro-región</p><div class="cwrap"><canvas id="review_por_region"></canvas></div><div class="stat" id="s-review_por_region"></div><div class="explica" id="e-review_por_region"></div></div>
      <div class="card"><h4>Método de pago → ¿llega tarde?</h4><p class="sub">% de pedidos que llegan tarde según método de pago</p><div class="cwrap"><canvas id="pago_vs_tarde"></canvas></div><div class="stat" id="s-pago_vs_tarde"></div><div class="explica" id="e-pago_vs_tarde"></div></div>
      <div class="card full"><h4>📍 Distancia vendedor–cliente → días de entrega</h4><p class="sub">Tiempo medio de entrega según los km entre vendedor y cliente</p><div class="cwrap"><canvas id="entrega_vs_distancia"></canvas></div><div class="stat" id="s-entrega_vs_distancia"></div><div class="explica" id="e-entrega_vs_distancia"></div></div>
      <div class="card"><h4>Calificación vs. flete relativo (puntuales)</h4><p class="sub">Quintiles de ratio flete/precio en pedidos a tiempo</p><div class="cwrap"><canvas id="review_vs_ratioflete"></canvas></div><div class="stat" id="s-review_vs_ratioflete"></div><div class="explica" id="e-review_vs_ratioflete"></div></div>

      <div class="sec"><h3>🧩 Categorías agrupadas</h3><p>Las 71 categorías reducidas a 8 familias, para ver si algunas reciben peor nota y si además tardan más.</p></div>
      <div class="card"><h4>Calificación media por familia de producto</h4><p class="sub">Ordenadas de peor a mejor calificación</p><div class="cwrap"><canvas id="review_por_macrocat"></canvas></div><div class="stat" id="s-review_por_macrocat"></div><div class="explica" id="e-review_por_macrocat"></div></div>
      <div class="card"><h4>Días de entrega por familia de producto</h4><p class="sub">Mismo orden que el gráfico anterior (para comparar)</p><div class="cwrap"><canvas id="demora_por_macrocat"></canvas></div><div class="stat" id="s-demora_por_macrocat"></div><div class="explica" id="e-demora_por_macrocat"></div></div>
      <div class="card full"><h4>🗺️ Muebles y Hogar: ¿de dónde salen vs. a dónde van?</h4><p class="sub">Origen (vendedores, azul) y destino (clientes, naranja) sobre el mapa de Brasil. Tamaño del punto = nº de pedidos.</p><div class="cwrap" style="height:480px;max-width:760px;margin:0 auto"><canvas id="mapa_muebles"></canvas></div><div class="stat" id="s-mapa_muebles"></div><div class="explica" id="e-mapa_muebles"></div></div>
      <div class="card full"><h4>🗺️ Tecnología: ¿de dónde salen vs. a dónde van?</h4><p class="sub">Misma vista para Tecnología (la categoría que más tarda). Tamaño del punto = nº de pedidos.</p><div class="cwrap" style="height:480px;max-width:760px;margin:0 auto"><canvas id="mapa_tecnologia"></canvas></div><div class="stat" id="s-mapa_tecnologia"></div><div class="explica" id="e-mapa_tecnologia"></div></div>

      <div class="sec"><h3>📦 Número de ítems del pedido</h3><p>Un pedido puede traer varios productos. ¿Los pedidos con más ítems se califican peor?</p></div>
      <div class="card"><h4>Calificación media según nº de ítems</h4><p class="sub">Ítems por pedido (5+ agrupa 5 o más)</p><div class="cwrap"><canvas id="review_vs_nitems"></canvas></div><div class="stat" id="s-review_vs_nitems"></div><div class="explica" id="e-review_vs_nitems"></div></div>
      <div class="card"><h4>% de clientes muy molestos (1–2★) según nº de ítems</h4><p class="sub">Probabilidad de detractor por tamaño del pedido</p><div class="cwrap"><canvas id="detractores_vs_nitems"></canvas></div><div class="stat" id="s-detractores_vs_nitems"></div><div class="explica" id="e-detractores_vs_nitems"></div></div>
      <div class="card"><h4>¿El nº de ítems alarga la entrega?</h4><p class="sub">Días de entrega medios según cuántos ítems trae el pedido</p><div class="cwrap"><canvas id="tiempo_vs_nitems"></canvas></div><div class="stat" id="s-tiempo_vs_nitems"></div><div class="explica" id="e-tiempo_vs_nitems"></div></div>
      <div class="card"><h4>Pedir de 1 categoría vs. varias → ¿tarda más?</h4><p class="sub">Días de entrega en pedidos de 2+ ítems, según nº de ítems (controlado)</p><div class="cwrap"><canvas id="tiempo_mono_vs_multicat"></canvas></div><div class="stat" id="s-tiempo_mono_vs_multicat"></div><div class="explica" id="e-tiempo_mono_vs_multicat"></div></div>

      <div class="sec"><h3>🧪 Simulación: ¿vale la pena controlar el nº de ítems?</h3><p>El efecto hoy es pequeño (~1% de la varianza) pero independiente del tiempo de entrega. ¿Por qué más ítems bajan la nota, y qué pasa si la canasta crece y no se controla?</p></div>
      <div class="card"><h4>¿Por qué más ítems bajan la nota? (eslabón más débil)</h4><p class="sub">% de detractores por nº de ítems (solo pedidos a tiempo) vs. modelo teórico</p><div class="cwrap"><canvas id="sim_weakest"></canvas></div><div class="stat" id="s-sim_weakest"></div><div class="explica" id="e-sim_weakest"></div></div>
      <div class="card"><h4>El eslabón que falla: varios vendedores</h4><p class="sub">% de detractores en pedidos de 2+ ítems según nº de vendedores</p><div class="cwrap"><canvas id="sim_fragmentacion"></canvas></div><div class="stat" id="s-sim_fragmentacion"></div><div class="explica" id="e-sim_fragmentacion"></div></div>
      <div class="card"><h4>Proyección: si la canasta crece y no se controla</h4><p class="sub">Tasa de detractores según el % de pedidos multi-ítem</p><div class="cwrap"><canvas id="sim_proyeccion"></canvas></div><div class="stat" id="s-sim_proyeccion"></div><div class="explica" id="e-sim_proyeccion"></div></div>
      <div class="card"><h4>Clientes insatisfechos evitables (por 10.000 pedidos)</h4><p class="sub">Cuántos detractores se ahorrarían controlando el cumplimiento multi-ítem</p><div class="cwrap"><canvas id="sim_impacto"></canvas></div><div class="stat" id="s-sim_impacto"></div><div class="explica" id="e-sim_impacto"></div></div>

      <div class="sec"><h3>🎲 Monte Carlo: ¿es real y con cuánta certeza?</h3><p>Otra perspectiva: en vez de un solo número, miles de simulaciones para (1) probar si el efecto es real o azar y (2) medir su incertidumbre.</p></div>
      <div class="card"><h4>¿Es real o casualidad? (prueba de permutación)</h4><p class="sub">Diferencia multi vs 1-ítem en 5.000 mundos aleatorios vs. lo observado</p><div class="cwrap"><canvas id="mc_permutacion"></canvas></div><div class="note" id="n-mc"></div><div class="stat" id="s-mc_permutacion"></div><div class="explica" id="e-mc_permutacion"></div></div>
      <div class="card"><h4>¿Cuán sólido es el impacto? (bootstrap)</h4><p class="sub">Distribución de detractores evitables por 10.000 pedidos (4.000 remuestreos)</p><div class="cwrap"><canvas id="mc_impacto_dist"></canvas></div><div class="stat" id="s-mc_impacto_dist"></div><div class="explica" id="e-mc_impacto_dist"></div></div>
      <div class="card full"><h4>Proyección con margen de error (banda 90%)</h4><p class="sub">Tasa de detractores según % de pedidos multi-ítem, con incertidumbre</p><div class="cwrap"><canvas id="mc_proyeccion_banda"></canvas></div><div class="stat" id="s-mc_proyeccion_banda"></div><div class="explica" id="e-mc_proyeccion_banda"></div></div>

      <div class="card full"><h4>🔎 ¿Qué pesa más en la calificación? (con el tiempo incluido, sin trucos)</h4><p class="sub">Varianza de la calificación explicada por cada factor (ρ²/ε²). El tiempo va en rojo como referencia.</p><div class="cwrap"><canvas id="segunda_causa"></canvas></div><div class="note" id="n-segunda"></div><div class="stat" id="s-segunda_causa"></div><div class="explica" id="e-segunda_causa"></div></div>
    </div>
  </section>

  <!-- ============ VENDEDOR (COMPORTAMIENTO) ============ -->
  <section id="tab-vendedor" class="hidden">
    <div class="filters"><h3>Filtros — comportamiento del vendedor (1 fila por seller_id)</h3>
      <div class="frow">
        <div class="fg" style="flex:1 1 100%"><label>Región del vendedor</label><div class="chips" id="ven-regiones"></div></div>
        <div class="fg"><label>Mínimo de pedidos del vendedor</label>
          <select id="ven-min"><option value="1">Todos</option><option value="5" selected>≥ 5 (recomendado)</option><option value="21">≥ 21</option><option value="100">≥ 100</option></select></div>
        <button class="reset" id="ven-reset">↺ Restablecer</button>
      </div>
      <p class="sub" style="margin:10px 0 0">Se analiza qué explica lo que el vendedor <b>controla</b> (despachar a tiempo, cancelar, rapidez) — no su “satisfacción”.</p>
    </div>
    <div class="kpis" id="ven-kpis"></div>
    <div class="grid">
      <div class="card"><h4>Distribución del % de despachos tardíos</h4><p class="sub">El KPI más atribuible al propio vendedor</p><div class="cwrap"><canvas id="comp_tardios_dist"></canvas></div><div class="stat" id="s-comp_tardios_dist"></div><div class="explica" id="e-comp_tardios_dist"></div></div>
      <div class="card"><h4>Volumen vs. % de despachos tardíos</h4><p class="sub">¿Escalar satura la capacidad de despacho?</p><div class="cwrap"><canvas id="comp_volumen_vs_tardios"></canvas></div><div class="stat" id="s-comp_volumen_vs_tardios"></div><div class="explica" id="e-comp_volumen_vs_tardios"></div></div>
      <div class="card"><h4>Volumen vs. consistencia del cumplimiento</h4><p class="sub">IQR (variabilidad) del % de despachos tardíos por banda de volumen</p><div class="cwrap"><canvas id="comp_volumen_vs_dispersion"></canvas></div><div class="stat" id="s-comp_volumen_vs_dispersion"></div><div class="explica" id="e-comp_volumen_vs_dispersion"></div></div>
      <div class="card"><h4>Distancia vs. tiempo de despacho</h4><p class="sub">¿La distancia afecta lo que el vendedor controla?</p><div class="cwrap"><canvas id="comp_distancia_vs_despacho"></canvas></div><div class="stat" id="s-comp_distancia_vs_despacho"></div><div class="explica" id="e-comp_distancia_vs_despacho"></div></div>
      <div class="card"><h4>Cancelaciones vs. despachos tardíos</h4><p class="sub">¿Sustitutos o el mismo vendedor problemático?</p><div class="cwrap"><canvas id="comp_cancel_vs_tardios"></canvas></div><div class="stat" id="s-comp_cancel_vs_tardios"></div><div class="explica" id="e-comp_cancel_vs_tardios"></div></div>
      <div class="card"><h4>% despachos tardíos por región</h4><p class="sub">¿La geografía del vendedor explica su comportamiento?</p><div class="cwrap"><canvas id="comp_region"></canvas></div><div class="stat" id="s-comp_region"></div><div class="explica" id="e-comp_region"></div></div>
      <div class="card full"><h4>🔎 ¿Qué explica el despacho tardío del vendedor?</h4><p class="sub">Varianza del % de despachos tardíos explicada por cada factor (ρ²/ε²)</p><div class="cwrap"><canvas id="comp_drivers"></canvas></div><div class="note" id="n-drivers"></div><div class="stat" id="s-comp_drivers"></div><div class="explica" id="e-comp_drivers"></div></div>
      <div class="card full"><h4>Comportamiento del vendedor → su calificación</h4><p class="sub">Calificación media según % de despachos tardíos (¿cuánto del review depende de él?)</p><div class="cwrap"><canvas id="comp_comportamiento_vs_review"></canvas></div><div class="stat" id="s-comp_comportamiento_vs_review"></div><div class="explica" id="e-comp_comportamiento_vs_review"></div></div>
    </div>
  </section>
  <!-- ============ PITCH ============ -->
  <section id="tab-pitch" class="hidden">
    <div class="grid">
      <div class="sec"><h3>🎤 Pitch — la historia en gráficas</h3></div>

      <div class="card full"><h4>La firma del retraso: el "codo" en la fecha prometida</h4><p class="sub">Calificación media según días respecto a la fecha prometida (0 = a tiempo).</p><div class="cwrap tall"><canvas id="pitch_retraso"></canvas></div><div class="concepto"><b>Concepto usado:</b> Probabilidad condicional — P(1–2★ | llega tarde) ≈ 54% vs. 9% a tiempo (riesgo ~6×).</div></div>

      <div class="card full"><h4>El problema silencioso: más ítems, más detractores</h4><p class="sub">% de clientes muy molestos (1–2★) según nº de ítems del pedido — solo pedidos entregados a tiempo.</p><div class="cwrap tall"><canvas id="pitch_detractores"></canvas></div><div class="concepto"><b>Concepto usado:</b> Probabilidad condicional — P(detractor | nº de ítems); el efecto persiste al controlar por tiempo (correlación parcial ρ = −0,117).</div></div>

      <div class="card"><h4>Lo que está en juego: detractores evitables / 10.000 pedidos</h4><p class="sub">Cuántos detractores se ahorrarían controlando el cumplimiento multi-ítem</p><div class="cwrap"><canvas id="pitch_impacto"></canvas></div><div class="concepto"><b>Concepto usado:</b> Simulación Monte Carlo (bootstrap) — impacto estimado por remuestreo, con intervalo de confianza.</div></div>

      <div class="card"><h4>La cifra no se queda quieta: proyección al crecer la canasta</h4><p class="sub">% de detractores según el % de pedidos multi-ítem (sin control vs. con fulfillment)</p><div class="cwrap"><canvas id="pitch_proyeccion"></canvas></div><div class="concepto"><b>Concepto usado:</b> Esperanza y varianza + proyección lineal (banda 90% por bootstrap).</div></div>
    </div>
  </section>

  <footer>Análisis probabilístico Olist · datos 2016–2018 · asociación observacional, no causal</footer>
</div>

<script id="payload" type="application/json">__PAYLOAD__</script>
<script>__CHARTJS__</script>
<script>
const D=JSON.parse(document.getElementById('payload').textContent);
const BRAZIL=__BRAZIL__;
const REG=D.dims.regiones,PAYS=D.dims.payment_types,MESES=D.dims.meses,MACROS=D.dims.macro_categorias;
const COL={a:'#2563eb',a2:'#93c5fd',g:'#059669',r:'#dc2626',y:'#d97706',p:'#7c3aed',slate:'#64748b'};
Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";Chart.defaults.color="#475569";Chart.defaults.plugins.legend.labels.boxWidth=12;
const CLI=D.cliente,VEN=D.vendedor,charts={};
// cli:0 region,1 estado,2 cat,3 pay,4 ym,5 review,6 retraso,7 entrega,8 ratioX100,9 dist,10 ontime,11 inst,12 nitems,13 macro
// ven:0 region,1 estado,2 revX100,3 tardX10,4 cancX10,5 despX10,6 vol,7 nped,8 dist,9 ratioX100
function setTxt(pre,id,t,none){const e=document.getElementById(pre+id);if(!e)return;e.innerHTML=t||'';if(none&&pre==='s-')e.classList.add('none');}
function cap(id){setTxt('s-',id,D.stats[id]);setTxt('e-',id,'<b>Qué significa:</b> '+(D.explica[id]||''));}
function mk(id,cfg){const c=document.getElementById(id);if(!c)return;if(charts[id])charts[id].destroy();charts[id]=new Chart(c,cfg);}
function mean(a){return a.length?a.reduce((s,x)=>s+x,0)/a.length:null;}
function median(a){if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return quantile(s,.5);}
function quantile(s,q){if(!s.length)return null;const p=(s.length-1)*q,b=Math.floor(p),r=p-b;return s[b+1]!==undefined?s[b]+r*(s[b+1]-s[b]):s[b];}
function fmt(v){return v==null?'—':Math.round(v*1000)/1000;}
function kpi(v,l){return '<div class="kpi"><div class="v">'+v+'</div><div class="l">'+l+'</div></div>';}
function effV(v){return v<.1?'insignificante':v<.2?'pequeño':v<.4?'moderado':'fuerte';}
function chi2Indep(tab){const R=tab.length,C=tab[0].length;const rt=tab.map(r=>r.reduce((a,b)=>a+b,0));const ct=[];for(let j=0;j<C;j++){let s=0;for(let i=0;i<R;i++)s+=tab[i][j];ct.push(s);}const N=rt.reduce((a,b)=>a+b,0);if(!N)return null;let chi=0;for(let i=0;i<R;i++)for(let j=0;j<C;j++){const e=rt[i]*ct[j]/N;if(e>0)chi+=(tab[i][j]-e)**2/e;}return {chi2:chi,V:Math.sqrt(chi/(N*Math.min(R-1,C-1))),N};}

// ============ CLIENTE ============
const F={regs:new Set(REG.map((_,i)=>i)),macros:new Set(MACROS.map((_,i)=>i)),rating:new Set([1,2,3,4,5]),pays:new Set(PAYS.map((_,i)=>i)),from:0,to:MESES.length-1};
function filtCli(){const aM=F.macros.size===MACROS.length,aP=F.pays.size===PAYS.length,aR=F.rating.size===5;
  return CLI.filter(r=>F.regs.has(r[0])&&(aM||F.macros.has(r[13]))&&(aR||F.rating.has(r[5]))&&(aP||F.pays.has(r[3]))&&r[4]>=F.from&&r[4]<=F.to);}
function chipHost(host,labels,set,val1,onChange){host.innerHTML='';labels.forEach((name,idx)=>{const key=val1?idx+1:idx;const d=document.createElement('div');d.className='chip on';d.textContent=name;
  d.onclick=()=>{if(set.has(key))set.delete(key);else set.add(key);if(set.size===0)set.add(key);d.classList.toggle('on',set.has(key));onChange();};host.appendChild(d);});}
function fillSelect(sel,items){sel.innerHTML='';items.forEach((t,i)=>{const o=document.createElement('option');o.value=i;o.textContent=t;sel.appendChild(o);});}

function renderCli(){
  const rows=filtCli(),rev=rows.map(r=>r[5]),ot=rows.filter(r=>r[10]!==null);
  const pctTarde=ot.length?100*ot.filter(r=>r[10]===0).length/ot.length:0;
  document.getElementById('cli-kpis').innerHTML=kpi(rows.length.toLocaleString('es'),'pedidos filtrados')+kpi((mean(rev)||0).toFixed(2)+' ★','calificación media')+kpi((100*rev.filter(x=>x<=2).length/(rev.length||1)).toFixed(1)+'%','detractores (1–2★)')+kpi(pctTarde.toFixed(1)+'%','entregas tardías');

  mk('dist_review',{type:'bar',data:{labels:['1★','2★','3★','4★','5★'],datasets:[{data:[1,2,3,4,5].map(s=>rev.filter(x=>x===s).length),backgroundColor:['#dc2626','#f97316','#d97706','#84cc16','#059669']}]},options:optBar(true)});cap('dist_review');

  const bins=[{l:'≤-10',f:r=>r[6]<=-10},{l:'-9 a -1',f:r=>r[6]>=-9&&r[6]<0},{l:'0',f:r=>r[6]===0},{l:'1 a 3',f:r=>r[6]>=1&&r[6]<=3},{l:'4 a 7',f:r=>r[6]>=4&&r[6]<=7},{l:'8 a 15',f:r=>r[6]>=8&&r[6]<=15},{l:'>15',f:r=>r[6]>15}];
  const rr=rows.filter(r=>r[6]!==null);
  mk('review_vs_retraso',{type:'line',data:{labels:bins.map(b=>b.l),datasets:[{data:bins.map(b=>mean(rr.filter(b.f).map(r=>r[5]))),borderColor:COL.r,backgroundColor:'rgba(220,38,38,.12)',fill:true,tension:.25,pointRadius:4,pointBackgroundColor:COL.r}]},options:optLine(1,5)});cap('review_vs_retraso');

  renderRegional();
  mk('review_por_region',{type:'bar',data:{labels:REG,datasets:[{data:REG.map((_,i)=>mean(rows.filter(r=>r[0]===i).map(r=>r[5]))),backgroundColor:COL.a}]},options:optBar(false,3,5)});cap('review_por_region');

  // pago -> % tarde + chi2 independencia
  const pl=[],tab=[];PAYS.forEach((_,i)=>{const g=rows.filter(r=>r[3]===i&&r[10]!==null);const late=g.filter(r=>r[10]===0).length,on=g.length-late;pl.push(g.length?100*late/g.length:null);tab.push([on,late]);});
  mk('pago_vs_tarde',{type:'bar',data:{labels:PAYS,datasets:[{label:'% pedidos tardíos',data:pl,backgroundColor:COL.y}]},options:optBar(false,0)});
  const ch=chi2Indep(tab.filter(t=>t[0]+t[1]>0));let t1=D.stats.pago_vs_tarde;
  if(ch)t1='<b>Sobre tus datos filtrados:</b> χ²='+fmt(ch.chi2)+', V de Cramér='+fmt(ch.V)+' → el pago influye de forma <b>'+effV(ch.V)+'</b> en la tardanza. '+D.stats.pago_vs_tarde;
  setTxt('s-','pago_vs_tarde',t1);setTxt('e-','pago_vs_tarde','<b>Qué significa:</b> '+D.explica.pago_vs_tarde);

  // distancia -> dias de entrega
  const db=[{l:'0–50',f:r=>r[9]<50},{l:'50–150',f:r=>r[9]>=50&&r[9]<150},{l:'150–500',f:r=>r[9]>=150&&r[9]<500},{l:'500–1k',f:r=>r[9]>=500&&r[9]<1000},{l:'1k–2k',f:r=>r[9]>=1000&&r[9]<2000},{l:'>2k',f:r=>r[9]>=2000}];
  const de=rows.filter(r=>r[9]!=null&&r[7]!=null);
  mk('entrega_vs_distancia',{type:'line',data:{labels:db.map(b=>b.l+' km'),datasets:[{label:'días de entrega (media)',data:db.map(b=>mean(de.filter(b.f).map(r=>r[7]))),borderColor:COL.a,backgroundColor:'rgba(37,99,235,.12)',fill:true,tension:.25,pointRadius:4,pointBackgroundColor:COL.a}]},options:optLine(0,null)});cap('entrega_vs_distancia');

  const pr=rows.filter(r=>r[10]===1&&r[8]!==null).map(r=>[r[8],r[5]]);const sr=pr.map(x=>x[0]).sort((a,b)=>a-b);const qs=[0,.2,.4,.6,.8,1].map(q=>quantile(sr,q));const qm=[];
  for(let k=0;k<5;k++){const lo=qs[k],hi=qs[k+1];qm.push(mean(pr.filter(x=>k<4?(x[0]>=lo&&x[0]<hi):(x[0]>=lo&&x[0]<=hi)).map(x=>x[1])));}
  mk('review_vs_ratioflete',{type:'bar',data:{labels:['Q1 (bajo)','Q2','Q3','Q4','Q5 (alto)'],datasets:[{data:qm,backgroundColor:COL.p}]},options:optBar(false,3.5,5)});cap('review_vs_ratioflete');

  // macro-categorias: review y demora (mismo orden)
  const mrev=MACROS.map((_,i)=>({i,rev:mean(rows.filter(r=>r[13]===i).map(r=>r[5])),ent:median(rows.filter(r=>r[13]===i&&r[7]!=null).map(r=>r[7]))}));
  const ord=mrev.filter(m=>m.rev!=null).sort((a,b)=>a.rev-b.rev);
  mk('review_por_macrocat',{type:'bar',data:{labels:ord.map(m=>MACROS[m.i]),datasets:[{data:ord.map(m=>m.rev),backgroundColor:COL.y}]},options:Object.assign(optBar(false,3,5),{indexAxis:'y'})});cap('review_por_macrocat');
  mk('demora_por_macrocat',{type:'bar',data:{labels:ord.map(m=>MACROS[m.i]),datasets:[{label:'días de entrega (mediana)',data:ord.map(m=>m.ent),backgroundColor:COL.slate}]},options:Object.assign(optBar(false,0),{indexAxis:'y'})});cap('demora_por_macrocat');

  // n items
  const nlab=['1','2','3','4','5+'];const ni=k=>rows.filter(r=>Math.min(r[12],5)===k);
  mk('review_vs_nitems',{type:'bar',data:{labels:nlab,datasets:[{data:[1,2,3,4,5].map(k=>mean(ni(k).map(r=>r[5]))),backgroundColor:COL.a}]},options:optBar(false,3,5)});cap('review_vs_nitems');
  mk('detractores_vs_nitems',{type:'bar',data:{labels:nlab,datasets:[{label:'% detractores (1–2★)',data:[1,2,3,4,5].map(k=>{const g=ni(k);return g.length?100*g.filter(r=>r[5]<=2).length/g.length:null;}),backgroundColor:COL.r}]},options:optBar(false,0)});cap('detractores_vs_nitems');
  mk('tiempo_vs_nitems',{type:'line',data:{labels:nlab,datasets:[{label:'días de entrega (media)',data:[1,2,3,4,5].map(k=>mean(ni(k).filter(r=>r[7]!=null).map(r=>r[7]))),borderColor:COL.slate,backgroundColor:'rgba(100,116,139,.12)',fill:true,tension:.25,pointRadius:4,pointBackgroundColor:COL.slate}]},options:optLine(0,null)});cap('tiempo_vs_nitems');
  const bk=[2,3,4,5];
  mk('tiempo_mono_vs_multicat',{type:'bar',data:{labels:['2','3','4','5+'],datasets:[
    {label:'1 categoría',data:bk.map(k=>mean(rows.filter(r=>Math.min(r[12],5)===k&&r[14]===1&&r[7]!=null).map(r=>r[7]))),backgroundColor:COL.a},
    {label:'varias categorías',data:bk.map(k=>mean(rows.filter(r=>Math.min(r[12],5)===k&&r[14]>=2&&r[7]!=null).map(r=>r[7]))),backgroundColor:COL.y}]},options:optBar(false,0,null,true)});cap('tiempo_mono_vs_multicat');

  renderSegunda();
}
function renderMC(){const M=D.montecarlo;if(!M)return;
  mk('mc_permutacion',{type:'bar',data:{labels:M.perm.null_centers,datasets:[{label:'azar',data:M.perm.null_counts,backgroundColor:COL.a2}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>i[0].label+' pp'}}},scales:{x:{grid:{display:false},title:{display:true,text:'brecha multi − 1 ítem bajo azar (pp)'}},y:{beginAtZero:true,grid:{color:'#eef2f7'}}}}});
  document.getElementById('n-mc').textContent='◀ Observado real = '+M.perm.observed_pp+' pp — muy fuera del gráfico: el azar nunca superó '+M.perm.null_max_pp+' pp. p < '+String(M.perm.p_upper_bound).replace('.',',');
  cap('mc_permutacion');
  mk('mc_impacto_dist',{type:'bar',data:{labels:M.boot_today.hist.centers,datasets:[{label:'frecuencia',data:M.boot_today.hist.counts,backgroundColor:COL.y}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>i[0].label+' /10k'}}},scales:{x:{grid:{display:false},title:{display:true,text:'detractores evitables por 10.000 pedidos'}},y:{beginAtZero:true,grid:{color:'#eef2f7'}}}}});cap('mc_impacto_dist');
  const s=M.proj.shares.map(m=>Math.round(m*100)+'%');
  mk('mc_proyeccion_banda',{type:'line',data:{labels:s,datasets:[
    {label:'_lo',data:M.proj.lo,borderColor:'transparent',pointRadius:0,fill:false},
    {label:'banda 90%',data:M.proj.hi,borderColor:'transparent',backgroundColor:'rgba(220,38,38,.15)',pointRadius:0,fill:'-1'},
    {label:'mediana sin control',data:M.proj.median,borderColor:COL.r,pointRadius:2,fill:false},
    {label:'con control',data:s.map(()=>M.proj.control),borderColor:COL.g,borderDash:[6,4],pointRadius:0,fill:false}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,labels:{filter:it=>it.text[0]!=='_'}},tooltip:{filter:it=>it.dataset.label[0]!=='_',callbacks:{label:c=>c.dataset.label+': '+fmt(c.parsed.y)+'%'}}},scales:{x:{grid:{display:false},title:{display:true,text:'% de pedidos multi-ítem'}},y:{grid:{color:'#eef2f7'},title:{display:true,text:'% detractores'}}}}});cap('mc_proyeccion_banda');}
function renderSim(){const S=D.simulacion;if(!S)return;const pct=x=>+(x*100).toFixed(1);
  mk('sim_weakest',{data:{labels:S.labels_k,datasets:[
    {type:'bar',label:'% detractores observado',data:S.p_by_k.map(pct),backgroundColor:COL.r,order:2},
    {type:'line',label:'modelo eslabón más débil',data:S.pred_weak.map(pct),borderColor:COL.slate,borderDash:[6,4],pointRadius:3,pointBackgroundColor:COL.slate,fill:false,order:1}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt(c.parsed.y)+'%'}}},scales:{x:{grid:{display:false},title:{display:true,text:'nº de ítems'}},y:{beginAtZero:true,grid:{color:'#eef2f7'},title:{display:true,text:'% detractores'}}}}});cap('sim_weakest');
  mk('sim_fragmentacion',{type:'bar',data:{labels:['1 vendedor','Varios vendedores'],datasets:[{label:'% detractores',data:[pct(S.frag.un_vendedor),pct(S.frag.varios)],backgroundColor:[COL.a,COL.r]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmt(c.parsed.y)+'%'}}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:'#eef2f7'},title:{display:true,text:'% detractores'}}}}});cap('sim_fragmentacion');
  mk('sim_proyeccion',{type:'line',data:{labels:S.proj_shares.map(m=>Math.round(m*100)+'%'),datasets:[
    {label:'sin control (canasta crece)',data:S.proj_nocontrol.map(x=>+(x*100).toFixed(2)),borderColor:COL.r,backgroundColor:'rgba(220,38,38,.1)',fill:true,tension:.2,pointRadius:3,pointBackgroundColor:COL.r},
    {label:'con control (fulfillment)',data:S.proj_shares.map(()=>+(S.proj_control*100).toFixed(2)),borderColor:COL.g,borderDash:[6,4],pointRadius:0,fill:false}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt(c.parsed.y)+'%'}}},scales:{x:{grid:{display:false},title:{display:true,text:'% de pedidos multi-ítem'}},y:{grid:{color:'#eef2f7'},title:{display:true,text:'% detractores'}}}}});cap('sim_proyeccion');
  mk('sim_impacto',{type:'bar',data:{labels:['Hoy (~'+Math.round(S.multi_share_now*100)+'% multi)','Si sube a 30%','Si sube a 50%'],datasets:[{label:'detractores evitables / 10.000 pedidos',data:[S.impacto_10k.hoy,S.impacto_10k.m30,S.impacto_10k.m50],backgroundColor:COL.y}]},options:optBar(true)});cap('sim_impacto');}

// ============ PITCH ============
function renderPitch(){
  const rows=CLI, S=D.simulacion;                 // datos completos, sin filtros
  const ont=rows.filter(r=>r[10]===1);            // pedidos entregados a tiempo

  // (1) el "codo" del retraso
  const bins=[{l:'≤-10',f:r=>r[6]<=-10},{l:'-9 a -1',f:r=>r[6]>=-9&&r[6]<0},{l:'0 (a tiempo)',f:r=>r[6]===0},{l:'1 a 3',f:r=>r[6]>=1&&r[6]<=3},{l:'4 a 7',f:r=>r[6]>=4&&r[6]<=7},{l:'8 a 15',f:r=>r[6]>=8&&r[6]<=15},{l:'>15',f:r=>r[6]>15}];
  const rr=rows.filter(r=>r[6]!==null);
  mk('pitch_retraso',{type:'line',data:{labels:bins.map(b=>b.l),datasets:[{label:'calificación media',data:bins.map(b=>mean(rr.filter(b.f).map(r=>r[5]))),borderColor:COL.r,backgroundColor:'rgba(220,38,38,.12)',fill:true,tension:.2,pointRadius:5,pointBackgroundColor:COL.r}]},options:optLine(1,5)});

  // (2) detractores por nº de ítems (solo a tiempo)
  const nlab=['1','2','3','4','5+'];const oni=k=>ont.filter(r=>Math.min(r[12],5)===k);
  const dbyk=[1,2,3,4,5].map(k=>{const g=oni(k);return g.length?100*g.filter(r=>r[5]<=2).length/g.length:null;});
  mk('pitch_detractores',{type:'bar',data:{labels:nlab,datasets:[{label:'% detractores (1–2★)',data:dbyk,backgroundColor:['#059669','#d97706','#f97316','#dc2626','#b91c1c']}]},options:optBar(false,0)});

  // (3) impacto hoy vs. escenarios (173 -> 513 -> 855)
  mk('pitch_impacto',{type:'bar',data:{labels:['Hoy (~'+Math.round(S.multi_share_now*100)+'% multi)','Si sube a 30%','Si sube a 50%'],datasets:[{label:'detractores evitables / 10.000 pedidos',data:[S.impacto_10k.hoy,S.impacto_10k.m30,S.impacto_10k.m50],backgroundColor:[COL.slate,COL.y,COL.r]}]},options:optBar(true)});

  // (4) proyección de la tasa de detractores (sin control vs. con fulfillment)
  mk('pitch_proyeccion',{type:'line',data:{labels:S.proj_shares.map(m=>Math.round(m*100)+'%'),datasets:[
    {label:'sin control (canasta crece)',data:S.proj_nocontrol.map(x=>+(x*100).toFixed(2)),borderColor:COL.r,backgroundColor:'rgba(220,38,38,.1)',fill:true,tension:.2,pointRadius:3,pointBackgroundColor:COL.r},
    {label:'con control (fulfillment)',data:S.proj_shares.map(()=>+(S.proj_control*100).toFixed(2)),borderColor:COL.g,borderDash:[6,4],pointRadius:0,fill:false}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmt(c.parsed.y)+'%'}}},scales:{x:{grid:{display:false},title:{display:true,text:'% de pedidos multi-ítem'}},y:{grid:{color:'#eef2f7'},title:{display:true,text:'% detractores'}}}}});
}
function renderMapa(id,M){if(!M)return;const ds=[];
  (BRAZIL||[]).forEach(ring=>ds.push({type:'line',data:ring.map(p=>({x:p[0],y:p[1]})),showLine:true,pointRadius:0,borderColor:'#d3dbe6',borderWidth:.6,fill:false,order:99}));
  const maxN=Math.max(1,...M.seller_states.map(s=>s.n),...M.customer_states.map(s=>s.n));
  function bub(arr,fill,border,label){return{type:'bubble',label:label,data:arr.map(s=>({x:s.lng,y:s.lat,r:5+22*Math.sqrt(s.n/maxN),uf:s.uf,n:s.n})),backgroundColor:fill,borderColor:border,borderWidth:1,order:1};}
  ds.push(bub(M.customer_states,'rgba(217,119,6,.45)','#b45309','Clientes (destino)'));
  ds.push(bub(M.seller_states,'rgba(37,99,235,.55)','#1d4ed8','Vendedores (origen)'));
  mk(id,{type:'scatter',data:{datasets:ds},options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:true,labels:{filter:(it,d)=>d.datasets[it.datasetIndex].type==='bubble'}},
      tooltip:{filter:it=>it.dataset.type==='bubble',callbacks:{label:c=>c.raw.uf+': '+c.raw.n.toLocaleString('es')+' pedidos'}}},
    scales:{x:{min:-74,max:-33,grid:{display:false},ticks:{display:false}},y:{min:-34,max:6,grid:{display:false},ticks:{display:false}}}}});
  cap(id);}
function renderRegional(){const o=D.regional.olist,m=D.regional.mercado;
  mk('regional_olist_vs_mercado',{type:'bar',data:{labels:REG,datasets:[{label:'Olist (real)',data:REG.map(r=>o[r]),backgroundColor:COL.a},{label:'Mercado BR (referencia)',data:REG.map(r=>m[r]),backgroundColor:COL.slate}]},options:optBar(false,0,null,true)});
  document.getElementById('n-regional').textContent='📌 '+D.regional.nota;cap('regional_olist_vs_mercado');}
const NICE={n_items:'nº de ítems',product_category_name_english:'categoría',freight_total:'flete total',distancia_seller_customer_km:'distancia',region:'región',payment_value:'valor pago',ratio_flete_precio:'ratio flete/precio',price_total:'precio total',payment_installments:'cuotas',payment_type:'método pago',tiempo_entrega_dias:'⏱ tiempo de entrega',dias_retraso:'⏱ días de retraso',n_pedidos:'volumen (nº pedidos)',ratio_flete_precio_promedio:'ratio flete/precio',distancia_promedio_a_clientes:'distancia'};
function renderSegunda(){const rk=D.segunda_causa.ranking.filter(r=>r.valor>0).slice(0,9);const win=D.segunda_causa.ganador.var;
  mk('segunda_causa',{type:'bar',data:{labels:rk.map(r=>NICE[r.var]||r.var),datasets:[{data:rk.map(r=>r.valor),backgroundColor:rk.map(r=>r.temporal?COL.r:(r.var===win?COL.g:COL.a2))}]},options:Object.assign(optBar(false,0),{indexAxis:'y'})});
  const g=D.segunda_causa.ganador;document.getElementById('n-segunda').textContent='🔴 tiempo = referencia (domina) · 🟢 segunda causa NO temporal: '+(NICE[g.var]||g.var)+'. '+g.interpretacion;cap('segunda_causa');}

// ============ VENDEDOR ============
const V={regs:new Set(REG.map((_,i)=>i)),min:5};
function filtVen(){return VEN.filter(r=>V.regs.has(r[0])&&r[7]>=V.min);}
function bandVol(r){return r[7]<=20?0:r[7]<=100?1:2;}
function renderVen(){
  const rows=filtVen();
  document.getElementById('ven-kpis').innerHTML=kpi(rows.length.toLocaleString('es'),'vendedores')+kpi(fmt(median(rows.map(r=>r[3]/10)))+'%','mediana % despachos tardíos')+kpi(fmt(median(rows.filter(r=>r[5]!=null).map(r=>r[5]/10)))+' d','mediana tiempo de despacho')+kpi(fmt(median(rows.map(r=>r[4]/10)))+'%','mediana % cancelaciones');
  const vt=rows.map(r=>r[3]/10).filter(v=>v!=null);kdeChart('comp_tardios_dist',vt,0,Math.max(40,quantile([...vt].sort((a,b)=>a-b),.98)||40));cap('comp_tardios_dist');
  const bl=['5–20','21–100','>100'];
  mk('comp_volumen_vs_tardios',{type:'bar',data:{labels:bl,datasets:[{label:'mediana % tardíos',data:[0,1,2].map(b=>median(rows.filter(r=>bandVol(r)===b).map(r=>r[3]/10))),backgroundColor:COL.y}]},options:optBar(false,0)});cap('comp_volumen_vs_tardios');
  mk('comp_volumen_vs_dispersion',{type:'bar',data:{labels:bl,datasets:[{label:'IQR % tardíos',data:[0,1,2].map(b=>{const v=rows.filter(r=>bandVol(r)===b).map(r=>r[3]/10).sort((a,z)=>a-z);return v.length>3?+(quantile(v,.75)-quantile(v,.25)).toFixed(2):null;}),backgroundColor:COL.p}]},options:optBar(false,0)});cap('comp_volumen_vs_dispersion');
  const dd=rows.filter(r=>r[8]!=null&&r[5]!=null);const ds=dd.map(r=>r[8]).sort((a,b)=>a-b);const dq=[0,.25,.5,.75,1].map(q=>quantile(ds,q));const dm=[];
  for(let k=0;k<4;k++){const lo=dq[k],hi=dq[k+1];dm.push(median(dd.filter(r=>k<3?(r[8]>=lo&&r[8]<hi):(r[8]>=lo&&r[8]<=hi)).map(r=>r[5]/10)));}
  mk('comp_distancia_vs_despacho',{type:'line',data:{labels:['Cerca (Q1)','Q2','Q3','Lejos (Q4)'],datasets:[{label:'mediana tiempo despacho (d)',data:dm,borderColor:COL.slate,backgroundColor:'rgba(100,116,139,.12)',fill:true,tension:.25,pointRadius:4,pointBackgroundColor:COL.slate}]},options:optLine(0,null)});cap('comp_distancia_vs_despacho');
  const cb=[{l:'0%',f:r=>r[4]===0},{l:'0–5%',f:r=>r[4]>0&&r[4]<=50},{l:'5–15%',f:r=>r[4]>50&&r[4]<=150},{l:'>15%',f:r=>r[4]>150}];
  mk('comp_cancel_vs_tardios',{type:'bar',data:{labels:cb.map(b=>b.l),datasets:[{label:'mediana % despachos tardíos',data:cb.map(b=>median(rows.filter(b.f).map(r=>r[3]/10))),backgroundColor:COL.r}]},options:optBar(false,0)});cap('comp_cancel_vs_tardios');
  mk('comp_region',{type:'bar',data:{labels:REG,datasets:[{data:REG.map((_,i)=>median(rows.filter(r=>r[0]===i).map(r=>r[3]/10))),backgroundColor:COL.a}]},options:optBar(false,0)});cap('comp_region');
  renderDrivers();
  const tb=[{l:'0%',f:r=>r[3]===0},{l:'0–5%',f:r=>r[3]>0&&r[3]<=50},{l:'5–15%',f:r=>r[3]>50&&r[3]<=150},{l:'15–30%',f:r=>r[3]>150&&r[3]<=300},{l:'>30%',f:r=>r[3]>300}];
  mk('comp_comportamiento_vs_review',{type:'line',data:{labels:tb.map(b=>b.l),datasets:[{label:'calificación media',data:tb.map(b=>median(rows.filter(b.f).map(r=>r[2]/100))),borderColor:COL.g,backgroundColor:'rgba(5,150,105,.12)',fill:true,tension:.25,pointRadius:4,pointBackgroundColor:COL.g}]},options:optLine(3,5)});cap('comp_comportamiento_vs_review');
}
function renderDrivers(){const rk=D.comportamiento.ranking.map(r=>({var:r.var,valor:Math.max(0,r.valor)}));const win=D.comportamiento.driver.var;
  mk('comp_drivers',{type:'bar',data:{labels:rk.map(r=>NICE[r.var]||r.var),datasets:[{data:rk.map(r=>r.valor),backgroundColor:rk.map(r=>r.var===win?COL.g:COL.a2)}]},options:Object.assign(optBar(false,0),{indexAxis:'y'})});
  document.getElementById('n-drivers').textContent='🟢 driver dominante: '+(NICE[win]||win)+'. '+D.comportamiento.nota;cap('comp_drivers');}

function kdeChart(id,vals,mn,mx){if(!vals.length){mk(id,{type:'line',data:{labels:[],datasets:[]},options:optLine(0,null)});return;}
  const n=vals.length,me=vals.reduce((s,x)=>s+x,0)/n,sd=Math.sqrt(vals.reduce((s,x)=>s+(x-me)*(x-me),0)/n)||1,bw=1.06*sd*Math.pow(n,-.2)||1,steps=60,grid=[],dens=[];
  for(let i=0;i<=steps;i++){const x=mn+(mx-mn)*i/steps;let d=0;for(const v of vals){const u=(x-v)/bw;d+=Math.exp(-.5*u*u);}dens.push(d/(n*bw*Math.sqrt(2*Math.PI)));grid.push(Math.round(x));}
  mk(id,{type:'line',data:{labels:grid,datasets:[{data:dens,borderColor:COL.a,backgroundColor:'rgba(37,99,235,.12)',fill:true,tension:.3,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{grid:{display:false},title:{display:true,text:'% despachos tardíos'}},y:{display:false}}}});}

function optBar(count,ymin,ymax,legend){return{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:!!legend},tooltip:{callbacks:{label:c=>(c.dataset.label?c.dataset.label+': ':'')+fmt(c.chart.options.indexAxis==='y'?c.parsed.x:c.parsed.y)}}},scales:{x:{grid:{display:false}},y:{beginAtZero:!!count,suggestedMin:ymin,suggestedMax:ymax,grid:{color:'#eef2f7'}}}};}
function optLine(ymin,ymax){return{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmt(c.parsed.y)}}},scales:{x:{grid:{display:false}},y:{suggestedMin:ymin,suggestedMax:ymax,grid:{color:'#eef2f7'}}}};}

// ===== INIT =====
chipHost(document.getElementById('cli-regiones'),REG,F.regs,false,renderCli);
chipHost(document.getElementById('cli-macro'),MACROS,F.macros,false,renderCli);
chipHost(document.getElementById('cli-rating'),['1★','2★','3★','4★','5★'],F.rating,true,renderCli);
chipHost(document.getElementById('cli-pay'),PAYS,F.pays,false,renderCli);
fillSelect(document.getElementById('cli-from'),MESES);fillSelect(document.getElementById('cli-to'),MESES);document.getElementById('cli-to').value=MESES.length-1;
document.getElementById('cli-from').onchange=e=>{F.from=+e.target.value;if(F.from>F.to){F.to=F.from;document.getElementById('cli-to').value=F.to;}renderCli();};
document.getElementById('cli-to').onchange=e=>{F.to=+e.target.value;if(F.to<F.from){F.from=F.to;document.getElementById('cli-from').value=F.from;}renderCli();};
document.getElementById('cli-reset').onclick=()=>{F.regs=new Set(REG.map((_,i)=>i));F.macros=new Set(MACROS.map((_,i)=>i));F.rating=new Set([1,2,3,4,5]);F.pays=new Set(PAYS.map((_,i)=>i));F.from=0;F.to=MESES.length-1;
  document.querySelectorAll('#cli-regiones .chip,#cli-macro .chip,#cli-rating .chip,#cli-pay .chip').forEach(c=>c.classList.add('on'));document.getElementById('cli-from').value=0;document.getElementById('cli-to').value=MESES.length-1;renderCli();};

chipHost(document.getElementById('ven-regiones'),REG,V.regs,false,renderVen);
document.getElementById('ven-min').onchange=e=>{V.min=+e.target.value;renderVen();};
document.getElementById('ven-reset').onclick=()=>{V.regs=new Set(REG.map((_,i)=>i));V.min=5;document.getElementById('ven-min').value=5;document.querySelectorAll('#ven-regiones .chip').forEach(c=>c.classList.add('on'));renderVen();};

document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');const tab=t.dataset.tab;
  document.getElementById('tab-cliente').classList.toggle('hidden',tab!=='cliente');
  document.getElementById('tab-vendedor').classList.toggle('hidden',tab!=='vendedor');
  document.getElementById('tab-pitch').classList.toggle('hidden',tab!=='pitch');
  if(tab==='cliente')renderCli();else if(tab==='vendedor')renderVen();else renderPitch();});
renderCli();renderSim();renderMC();renderMapa('mapa_muebles',D.mapa_muebles);renderMapa('mapa_tecnologia',D.mapa_tecnologia);
</script></body></html>"""
HTML = HTML.replace("__CHARTJS__", chartjs).replace("__BRAZIL__", brazil_js).replace("__PAYLOAD__", payload)
out = DASH + r"\index.html"; open(out, "w", encoding="utf-8").write(HTML)
print("Guardado:", out, "(", round(os.path.getsize(out)/1e6, 2), "MB )")
