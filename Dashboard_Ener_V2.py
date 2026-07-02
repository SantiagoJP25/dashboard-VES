#python -m streamlit run C:\Users\jsantiago\Documents\TRANSACCIONES\REPORTE_ENERLINK\Dashboard_Ener_V2.py
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
# python -m streamlit run Dashboard_Ener_v2.py

# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(
    page_title="Centro de Monitoreo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS compacto
st.markdown("""
<style>
    .main .block-container {
        padding-top: 0.0rem;
        padding-bottom: 0.4rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f1f3d;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: white !important;
    }
    [data-testid="stSidebarNav"] {display: none;}

    /* Header personalizado */
    .dash-header {
        background: linear-gradient(90deg, #0f1f3d 0%, #1a3a6b 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .dash-header h2 { margin: 0; font-size: 15px; font-weight: 700; }
    .dash-header span { font-size: 13px; opacity: 0.75; }

    /* Tabs compactas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #f0f2f6;
        border-radius: 6px;
        padding: 3px;
    }
    .stTabs [data-baseweb="tab"] { padding: 4px 10px; font-size: 12px; border-radius: 4px; }
    .stTabs [aria-selected="true"] { background: white; font-weight: 600; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 4px; }

    /* Métricas compactas */
    .kpi-card {
        background: #0f1f3d;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
    }
    .kpi-label {
        color: rgba(255,255,255,0.65);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: white;
        font-size: 22px;
        font-weight: 700;
        line-height: 1.1;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 1. Cargar datos
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent

transacciones = pd.read_excel(BASE_DIR / "Transacciones.xlsx", header=2)
maestro       = pd.read_excel(BASE_DIR / "Maestro_MVES.xlsx")

# -----------------------------
# 2. Limpieza y preparación
# -----------------------------
transacciones = transacciones.dropna(
    subset=["INICIO (UTC-05:00)", "ENERGIA CARGADA (kWh)", "VEHÍCULO", "ID"]
)
transacciones["FECHA"] = pd.to_datetime(transacciones["INICIO (UTC-05:00)"]).dt.date

vehiculos_validos = maestro["VEHÍCULO"].unique()
df = transacciones[transacciones["VEHÍCULO"].isin(vehiculos_validos)].copy()
df["INICIO_DT"] = pd.to_datetime(df["INICIO (UTC-05:00)"])
df["FIN_DT"]    = pd.to_datetime(df["TÉRMINO (UTC-05:00)"], errors="coerce")

# -----------------------------
# 3. Sidebar – Filtros
# -----------------------------
fecha_min = df["FECHA"].min()
fecha_max = df["FECHA"].max()

st.sidebar.markdown("## 🎛️ Filtros")
st.sidebar.markdown("---")

rango_fechas = st.sidebar.date_input(
    "📅 Rango de fechas",
    [fecha_min, fecha_max]
)

st.sidebar.markdown(" ")

vehiculos_sel = st.sidebar.multiselect(
    "🚗 Vehículos",
    options=sorted(df["VEHÍCULO"].unique()),
    default=sorted(df["VEHÍCULO"].unique())
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Total vehículos: {df['VEHÍCULO'].nunique()}")

# Aplicar filtros
if len(rango_fechas) == 2:
    f0, f1 = rango_fechas
else:
    f0 = f1 = rango_fechas[0]

if not vehiculos_sel:
    vehiculos_sel = sorted(df["VEHÍCULO"].unique())

df = df[
    (df["FECHA"] >= f0) &
    (df["FECHA"] <= f1) &
    (df["VEHÍCULO"].isin(vehiculos_sel))
]
num_dias = (pd.to_datetime(f1) - pd.to_datetime(f0)).days + 1

# -----------------------------
# 4. Header
# -----------------------------
st.markdown("""
<div class="dash-header">
  <h2>⚡ CENTRO DE MONITOREO DE ELECTROMOVILIDAD </h2>
  <span>FLOTA &nbsp;|&nbsp; MUNICIPALIDAD VILLA EL SALVADOR</span>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# 5. KPIs
# -----------------------------
kwh_total         = df["ENERGIA CARGADA (kWh)"].sum()
total_sesiones    = df["ID"].count()
vehiculos_activos = df["VEHÍCULO"].nunique()
kwh_prom_dia      = kwh_total / num_dias if num_dias > 0 else 0
ses_prom_dia      = total_sesiones / num_dias if num_dias > 0 else 0

st.markdown(f"""
<div style="display:flex; gap:8px; margin-bottom:6px;">
  <div class="kpi-card" style="flex:1">
    <div class="kpi-label">⚡ MWh Totales</div>
    <div class="kpi-value">{kwh_total/1000:,.2f}</div>
  </div>
  <div class="kpi-card" style="flex:1">
    <div class="kpi-label">🔌 Sesiones</div>
    <div class="kpi-value">{total_sesiones:,}</div>
  </div>
  <div class="kpi-card" style="flex:1">
    <div class="kpi-label">🚗 Vehículos activos</div>
    <div class="kpi-value">{vehiculos_activos}</div>
  </div>
  <div class="kpi-card" style="flex:1">
    <div class="kpi-label">📐 kWh / día</div>
    <div class="kpi-value">{kwh_prom_dia:,.1f}</div>
  </div>
  <div class="kpi-card" style="flex:1">
    <div class="kpi-label">📈 Sesiones / día</div>
    <div class="kpi-value">{ses_prom_dia:.1f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Preparar datos
# ─────────────────────────────────────────

ALTO   = 280
COLORES = {"azul": "#1a3a6b", "verde": "#00c49f", "naranja": "#ff7300"}
layout_base = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=30, r=10, t=30, b=30),
    font=dict(size=10),
    title_font_size=11,
)

# Consumo diario
df["FECHA"] = pd.to_datetime(df["FECHA"])
calendario = pd.DataFrame({"FECHA": pd.date_range(pd.to_datetime(f0), pd.to_datetime(f1), freq="D")})
consumo_diario = df.groupby("FECHA", as_index=False).agg(
    KWH=("ENERGIA CARGADA (kWh)", "sum"), SESIONES=("ID", "count"))
consumo_diario = calendario.merge(consumo_diario, on="FECHA", how="left").fillna(0)

# Rangos kWh
bins_kwh   = [0, 10, 20, 30, 40, 50, 60, float("inf")]
labels_kwh = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60+"]
df["RANGO_KWH"] = pd.cut(df["ENERGIA CARGADA (kWh)"], bins=bins_kwh, labels=labels_kwh)
tabla_kwh = df.groupby("RANGO_KWH").size().reindex(labels_kwh, fill_value=0).reset_index(name="SESIONES")

# Duracion
df_dur = df.dropna(subset=["INICIO_DT", "FIN_DT"]).copy()
df_dur["DURACION_MIN"] = (df_dur["FIN_DT"] - df_dur["INICIO_DT"]).dt.total_seconds() / 60
df_dur = df_dur[df_dur["DURACION_MIN"] > 0]
bins_dur   = [0, 10, 20, 30, 40, 50, 60, float("inf")]
labels_dur = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60+"]
df_dur["RANGO_DUR"] = pd.cut(df_dur["DURACION_MIN"], bins=bins_dur, labels=labels_dur)
tabla_dur = df_dur.groupby("RANGO_DUR").size().reindex(labels_dur, fill_value=0).reset_index(name="SESIONES")

# Frecuencia recarga
ses_veh = df.groupby("VEHÍCULO").agg(SESIONES=("ID", "count")).reset_index()
bins_ses   = [0, 10, 20, 30, 40, 50, float("inf")]
labels_ses = ["0-10", "10-20", "20-30", "30-40", "40-50", "50+"]
ses_veh["RANGO"] = pd.cut(ses_veh["SESIONES"], bins=bins_ses, labels=labels_ses, include_lowest=True)
frec_ses = ses_veh.groupby("RANGO", observed=True).size().reset_index(name="VEHÍCULOS")
frec_ses["PCT"] = (frec_ses["VEHÍCULOS"] / frec_ses["VEHÍCULOS"].sum() * 100).round(1).astype(str) + "%"

# Distribucion horaria
df_h = df_dur[df_dur["FIN_DT"] >= df_dur["INICIO_DT"]].copy()
df_h["INICIO_H"] = df_h["INICIO_DT"].dt.floor("h")
df_h["FIN_H"]    = df_h["FIN_DT"].dt.floor("h")
n_rep = ((df_h["FIN_H"] - df_h["INICIO_H"]).dt.total_seconds() // 3600 + 1).astype(int)
horas = df_h.loc[df_h.index.repeat(n_rep)].copy()
horas["HORA"] = horas["INICIO_H"] + pd.to_timedelta(horas.groupby(level=0).cumcount(), unit="h")
horas["HORA_DIA"] = horas["HORA"].dt.hour
horas["FECHA_H"]  = horas["HORA"].dt.date

tabla_horas_total = (
    horas.groupby("HORA_DIA")["ID"].nunique()
    .reindex(range(24), fill_value=0).reset_index(name="TOTAL")
)
tabla_dia_hora = horas.groupby(["FECHA_H", "HORA_DIA"])["ID"].nunique().reset_index(name="SESIONES")
dias = tabla_dia_hora["FECHA_H"].unique()
idx  = pd.DataFrame([(d, h) for d in dias for h in range(24)], columns=["FECHA_H", "HORA_DIA"])
tabla_full = idx.merge(tabla_dia_hora, on=["FECHA_H", "HORA_DIA"], how="left").fillna({"SESIONES": 0})
tabla_prom = tabla_full.groupby("HORA_DIA")["SESIONES"].mean().reset_index(name="PROMEDIO")

# Heatmap
horas["DIA_SEM"] = pd.to_datetime(horas["FECHA_H"]).dt.dayofweek
heatmap_data = horas.groupby(["DIA_SEM", "HORA_DIA"])["ID"].nunique().reset_index(name="SESIONES")
dias_nombres = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
heatmap_pivot = heatmap_data.pivot(index="DIA_SEM", columns="HORA_DIA", values="SESIONES").fillna(0)
heatmap_pivot.index = [dias_nombres[i] for i in heatmap_pivot.index]
heatmap_pivot = heatmap_pivot.reindex(columns=range(24), fill_value=0)

# Tendencia mensual
df["MES"] = df["FECHA"].dt.to_period("M").astype(str)
tendencia = df.groupby("MES", as_index=False).agg(
    KWH=("ENERGIA CARGADA (kWh)", "sum"), SESIONES=("ID", "count")).sort_values("MES")

# ─────────────────────────────────────────
# FILA 1: Consumo diario | Rangos kWh
# ─────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    tab1a, tab1b = st.tabs(["📐 Consumo diario", "🕐 Distribucion horaria"])
    with tab1a:
        fig = go.Figure(go.Scatter(
            x=consumo_diario["FECHA"], y=consumo_diario["KWH"],
            mode="lines+markers", line=dict(color=COLORES["azul"], width=2), marker=dict(size=4),
            customdata=consumo_diario["SESIONES"],
            hovertemplate="<b>%{x|%d-%m-%Y}</b><br>%{y:.1f} kWh<br>%{customdata} sesiones<extra></extra>"
        ))
        fig.update_layout(**layout_base, height=ALTO, title="Consumo diario de energia",
                          xaxis_title="", yaxis_title="kWh")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

    with tab1b:
        fig_h = make_subplots(specs=[[{"secondary_y": True}]])
        fig_h.add_trace(go.Bar(
            x=tabla_horas_total["HORA_DIA"], y=tabla_horas_total["TOTAL"],
            name="Total", opacity=0.7, marker_color=COLORES["azul"],
            hovertemplate="<b>%{x}:00</b><br>Total: %{y}<extra></extra>"
        ), secondary_y=False)
        fig_h.add_trace(go.Scatter(
            x=tabla_prom["HORA_DIA"], y=tabla_prom["PROMEDIO"],
            name="Promedio", mode="lines+markers",
            line=dict(width=2, color=COLORES["verde"]), marker=dict(size=4),
            hovertemplate="<b>%{x}:00</b><br>Prom: %{y:.2f}<extra></extra>"
        ), secondary_y=True)
        fig_h.update_layout(**layout_base, height=ALTO, title="Distribucion horaria de sesiones",
                            xaxis=dict(tickmode="array",
                                       tickvals=list(range(0, 24, 2)),
                                       ticktext=[f"{h:02d}" for h in range(0, 24, 2)]),
                            legend=dict(orientation="h", y=1.08, x=0.1, font_size=9))
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

with col_b:
    tab2a, tab2b = st.tabs(["⚡ Rangos kWh", "⏱️ Duracion sesiones"])
    with tab2a:
        fig2 = px.bar(tabla_kwh, x="RANGO_KWH", y="SESIONES",
                      color_discrete_sequence=[COLORES["azul"]])
        fig2.update_layout(**layout_base, height=ALTO, title="Distribución de kWh por Sesión",
                           xaxis_title="kWh", yaxis_title="Sesiones")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

    with tab2b:
        fig3 = px.bar(tabla_dur, x="RANGO_DUR", y="SESIONES",
                      color_discrete_sequence=["#e07b00"])
        fig3.update_layout(**layout_base, height=ALTO, title="Distribución de Sesiones según Duración (minutos)",
                           xaxis_title="Minutos", yaxis_title="Sesiones")
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# FILA 2: Frecuencia | Heatmap | Tendencia
# ─────────────────────────────────────────
col_c, col_d, col_e = st.columns(3)

with col_c:
    tab3a, = st.tabs(["🚗 Frecuencia recarga"])
    with tab3a:
         fig4 = px.bar(
            frec_ses,
            x="RANGO",
            y="VEHÍCULOS",
            text="PCT",
            color_discrete_sequence=[COLORES["azul"]]
           )

         fig4.update_traces(
           textposition="auto",
           textfont=dict(
           size=15,
           color="white"
           ),
           cliponaxis=False
)

         fig4.update_layout(**layout_base, height=ALTO, title="Frecuencia de sesiones de la flota",
                           xaxis_title="Sesiones", yaxis_title="Vehiculos")
         st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

with col_d:
    tab4a, = st.tabs(["🔥 Heatmap horario"])
    with tab4a:
        fig5 = go.Figure(go.Heatmap(
            z=heatmap_pivot.values,
            x=[f"{h:02d}:00" for h in range(24)],
            y=heatmap_pivot.index.tolist(),
            colorscale="Blues",
            hovertemplate="<b>%{y} %{x}</b><br>Sesiones: %{z}<extra></extra>"
        ))
        fig5.update_layout(**layout_base, height=ALTO, title="Sesiones: dia x hora",
                           xaxis=dict(tickangle=-45,
                                      tickmode="array",
                                      tickvals=[f"{h:02d}:00" for h in range(0, 24, 3)],
                                      ticktext=[f"{h:02d}" for h in range(0, 24, 3)]))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})

with col_e:
    tab5a, = st.tabs(["📐 Tendencia mensual"])
    with tab5a:
        fig6 = make_subplots(specs=[[{"secondary_y": True}]])
        fig6.add_trace(go.Bar(
            x=tendencia["MES"], y=tendencia["KWH"],
            name="kWh", opacity=0.8, marker_color=COLORES["azul"],
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} kWh<extra></extra>"
        ), secondary_y=False)
        fig6.add_trace(go.Scatter(
            x=tendencia["MES"], y=tendencia["SESIONES"],
            name="Sesiones", mode="lines+markers",
            line=dict(color=COLORES["naranja"], width=2), marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>%{y} sesiones<extra></extra>"
        ), secondary_y=True)
        fig6.update_layout(**layout_base, height=ALTO, title="Tendencia mensual",
                           xaxis=dict(tickangle=-30),
                           legend=dict(orientation="h", y=1.08, x=0, font_size=9))
        fig6.update_yaxes(title_text="kWh", secondary_y=False)
        fig6.update_yaxes(title_text="Sesiones", secondary_y=True)
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": "hover", "displaylogo": False, "modeBarButtonsToAdd": ["toggleFullScreen"]})