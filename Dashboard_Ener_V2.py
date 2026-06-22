import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path

# python -m streamlit run Dashboard_Ener_V2.py

# ============================================================
# CONFIGURACIÓN GENERAL – Tema NOC Oscuro
# ============================================================
st.set_page_config(
    page_title="Centro de Monitoreo Electromovilidad – VES",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Paleta NOC ──────────────────────────────────────────────
NOC_BG        = "#0D1117"   # fondo oscuro
NOC_PANEL     = "#161B22"   # fondo paneles
NOC_BORDER    = "#21262D"   # bordes sutiles
NOC_BLUE      = "#58A6FF"   # azul eléctrico
NOC_GREEN     = "#3FB950"   # verde operativo
NOC_YELLOW    = "#D29922"   # amarillo alerta
NOC_RED       = "#F85149"   # rojo crítico
NOC_TEXT      = "#C9D1D9"   # texto principal
NOC_MUTED     = "#8B949E"   # texto secundario

# ── CSS Global ───────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Fondo general */
    .stApp {{
        background-color: {NOC_BG};
        color: {NOC_TEXT};
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {NOC_PANEL};
        border-right: 1px solid {NOC_BORDER};
    }}
    section[data-testid="stSidebar"] * {{
        color: {NOC_TEXT} !important;
    }}
    /* Encabezado ejecutivo */
    .noc-header {{
        background: linear-gradient(135deg, {NOC_PANEL} 0%, #0D1F2D 100%);
        border: 1px solid {NOC_BLUE};
        border-radius: 8px;
        padding: 18px 24px;
        margin-bottom: 20px;
    }}
    .noc-header h1 {{
        color: {NOC_BLUE};
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}
    .noc-header p {{
        color: {NOC_MUTED};
        font-size: 0.82rem;
        margin: 4px 0 0 0;
        letter-spacing: 0.08em;
    }}
    /* Tarjetas KPI */
    .kpi-card {{
        background: {NOC_PANEL};
        border: 1px solid {NOC_BORDER};
        border-top: 3px solid {NOC_BLUE};
        border-radius: 8px;
        padding: 16px 18px;
        text-align: center;
    }}
    .kpi-label {{
        color: {NOC_MUTED};
        font-size: 0.72rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        color: {NOC_BLUE};
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.1;
    }}
    /* Divisor de sección */
    .section-title {{
        color: {NOC_MUTED};
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        border-bottom: 1px solid {NOC_BORDER};
        padding-bottom: 6px;
        margin: 20px 0 14px 0;
    }}
    /* Ocultar decoraciones de Streamlit */
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{padding-top: 1rem; padding-bottom: 2rem;}}
</style>
""", unsafe_allow_html=True)

# Layout Plotly base oscuro
PLOTLY_LAYOUT = dict(
    paper_bgcolor=NOC_PANEL,
    plot_bgcolor=NOC_BG,
    font=dict(color=NOC_TEXT, family="monospace"),
    title_font=dict(color=NOC_BLUE, size=14),
    xaxis=dict(gridcolor=NOC_BORDER, linecolor=NOC_BORDER, tickcolor=NOC_MUTED),
    yaxis=dict(gridcolor=NOC_BORDER, linecolor=NOC_BORDER, tickcolor=NOC_MUTED),
    margin=dict(l=50, r=20, t=50, b=50),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=NOC_TEXT))
)

# ============================================================
# 1. ENCABEZADO EJECUTIVO
# ============================================================
st.markdown(f"""
<div class="noc-header">
    <h1>⚡ Centro de Monitoreo de Electromovilidad — VES</h1>
    <p>Operación de infraestructura de carga &nbsp;|&nbsp; Estación Villa El Salvador</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 2. CARGA DE DATOS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def cargar_datos():
    transacciones = pd.read_excel(BASE_DIR / "Transacciones.xlsx", header=2)
    maestro       = pd.read_excel(BASE_DIR / "Maestro_MVES.xlsx")
    return transacciones, maestro

transacciones, maestro = cargar_datos()

# ============================================================
# 3. LIMPIEZA Y PREPARACIÓN
# ============================================================
transacciones = transacciones.dropna(
    subset=["INICIO (UTC-05:00)", "ENERGIA CARGADA (kWh)", "VEHÍCULO", "ID"]
)
transacciones["FECHA"] = pd.to_datetime(transacciones["INICIO (UTC-05:00)"]).dt.date

vehiculos_validos = maestro["VEHÍCULO"].unique()
df = transacciones[transacciones["VEHÍCULO"].isin(vehiculos_validos)].copy()
df["INICIO_DT"] = pd.to_datetime(df["INICIO (UTC-05:00)"])
df["FIN_DT"]    = pd.to_datetime(df["TÉRMINO (UTC-05:00)"], errors="coerce")

# ============================================================
# 4. SIDEBAR – FILTROS
# ============================================================
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    st.markdown("---")

    fecha_min = df["FECHA"].min()
    fecha_max = df["FECHA"].max()

    rango_fechas = st.date_input(
        "Rango de fechas",
        [fecha_min, fecha_max],
        min_value=fecha_min,
        max_value=fecha_max
    )

    vehiculos_sel = st.multiselect(
        "Vehículos",
        options=sorted(df["VEHÍCULO"].unique()),
        default=sorted(df["VEHÍCULO"].unique())
    )

    st.markdown("---")
    st.markdown(f"<span style='color:{NOC_MUTED};font-size:0.75rem;'>⚡ VES Energy Monitor v2.0</span>",
                unsafe_allow_html=True)

# ── Aplicar filtros ──────────────────────────────────────────
df = df[
    (df["FECHA"] >= rango_fechas[0]) &
    (df["FECHA"] <= rango_fechas[1]) &
    (df["VEHÍCULO"].isin(vehiculos_sel))
]
num_dias = (pd.to_datetime(rango_fechas[1]) - pd.to_datetime(rango_fechas[0])).days + 1

# ============================================================
# 5. KPIs
# ============================================================
kwh_total        = df["ENERGIA CARGADA (kWh)"].sum()
total_sesiones   = df["ID"].count()
vehiculos_activos = df["VEHÍCULO"].nunique()
kwh_dia          = kwh_total / num_dias if num_dias > 0 else 0
ses_dia          = total_sesiones / num_dias if num_dias > 0 else 0

st.markdown('<div class="section-title">■ Indicadores Clave de Operación</div>', unsafe_allow_html=True)

kpi_cols = st.columns(5)
kpis = [
    ("⚡ Energía Total",         f"{kwh_total:,.1f} kWh"),
    ("🔌 Sesiones Totales",      f"{total_sesiones:,}"),
    ("🚗 Vehículos Activos",     f"{vehiculos_activos}"),
    ("📅 kWh Promedio / Día",    f"{kwh_dia:,.1f}"),
    ("📈 Sesiones Promedio / Día", f"{ses_dia:.1f}"),
]
for col, (label, value) in zip(kpi_cols, kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 6. CONSUMO DIARIO
# ============================================================
st.markdown('<div class="section-title">■ Análisis de Consumo</div>', unsafe_allow_html=True)

df["FECHA"] = pd.to_datetime(df["FECHA"])

calendario = pd.DataFrame({
    "FECHA": pd.date_range(
        start=pd.to_datetime(rango_fechas[0]),
        end=pd.to_datetime(rango_fechas[1]),
        freq="D"
    )
})

consumo_diario = (
    df.groupby("FECHA", as_index=False)
    .agg(KWH_CONSUMIDOS=("ENERGIA CARGADA (kWh)", "sum"), SESIONES=("ID", "count"))
)
consumo_diario = (
    calendario.merge(consumo_diario, on="FECHA", how="left").fillna(0)
)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=consumo_diario["FECHA"],
    y=consumo_diario["KWH_CONSUMIDOS"],
    mode="lines+markers",
    line=dict(color=NOC_BLUE, width=2),
    marker=dict(color=NOC_BLUE, size=5),
    fill="tozeroy",
    fillcolor=f"rgba(88,166,255,0.12)",
    customdata=consumo_diario[["SESIONES"]],
    hovertemplate="<b>%{x|%d-%m-%Y}</b><br>Energía: %{y:.1f} kWh<br>Sesiones: %{customdata[0]}<extra></extra>"
))
fig1.update_layout(
    title="Consumo diario de energía (kWh)",
    xaxis_title="Fecha",
    yaxis_title="Energía (kWh)",
    **PLOTLY_LAYOUT
)
st.plotly_chart(fig1, use_container_width=True)

# ============================================================
# 7. TENDENCIA MENSUAL
# ============================================================
df["MES"] = df["FECHA"].dt.to_period("M").astype(str)
tendencia_mensual = (
    df.groupby("MES", as_index=False)
    .agg(KWH_MES=("ENERGIA CARGADA (kWh)", "sum"), SESIONES_MES=("ID", "count"))
)

fig_tend = make_subplots(specs=[[{"secondary_y": True}]])
fig_tend.add_trace(
    go.Bar(x=tendencia_mensual["MES"], y=tendencia_mensual["KWH_MES"],
           name="kWh / Mes", marker_color=NOC_BLUE, opacity=0.8),
    secondary_y=False
)
fig_tend.add_trace(
    go.Scatter(x=tendencia_mensual["MES"], y=tendencia_mensual["SESIONES_MES"],
               name="Sesiones / Mes", mode="lines+markers",
               line=dict(color=NOC_GREEN, width=2), marker=dict(size=6)),
    secondary_y=True
)
fig_tend.update_layout(
    title="Tendencia mensual – Energía y Sesiones",
    **PLOTLY_LAYOUT
)
fig_tend.update_yaxes(title_text="kWh", secondary_y=False,
                      gridcolor=NOC_BORDER, tickcolor=NOC_MUTED, color=NOC_TEXT)
fig_tend.update_yaxes(title_text="Sesiones", secondary_y=True,
                      gridcolor="rgba(0,0,0,0)", tickcolor=NOC_MUTED, color=NOC_TEXT)
st.plotly_chart(fig_tend, use_container_width=True)

# ============================================================
# 8. DISTRIBUCIONES – 2 COLUMNAS
# ============================================================
st.markdown('<div class="section-title">■ Distribuciones de Sesiones</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

# ── Rangos kWh ──
with col_a:
    bins_kwh   = [0, 10, 20, 30, 40, 50, 60, float("inf")]
    labels_kwh = ["0–10", "10–20", "20–30", "30–40", "40–50", "50–60", "60+"]
    df["RANGO_KWH"] = pd.cut(df["ENERGIA CARGADA (kWh)"], bins=bins_kwh, labels=labels_kwh)
    tabla_kwh = (
        df.groupby("RANGO_KWH").size()
        .reindex(labels_kwh, fill_value=0).reset_index(name="SESIONES")
    )
    fig2 = go.Figure(go.Bar(
        x=tabla_kwh["RANGO_KWH"], y=tabla_kwh["SESIONES"],
        marker_color=NOC_GREEN, opacity=0.85,
        hovertemplate="Rango: %{x} kWh<br>Sesiones: %{y}<extra></extra>"
    ))
    fig2.update_layout(title="Distribución por Rango de kWh",
                       xaxis_title="kWh", yaxis_title="Sesiones", **PLOTLY_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

# ── Duración sesiones ──
with col_b:
    df_dur = df.dropna(subset=["INICIO_DT", "FIN_DT"]).copy()
    df_dur["DURACION_MIN"] = (df_dur["FIN_DT"] - df_dur["INICIO_DT"]).dt.total_seconds() / 60
    df_dur = df_dur[df_dur["DURACION_MIN"] > 0]

    bins_dur   = [0, 10, 20, 30, 40, 50, 60, float("inf")]
    labels_dur = ["0–10", "10–20", "20–30", "30–40", "40–50", "50–60", "60+"]
    df_dur["RANGO_DURACION"] = pd.cut(df_dur["DURACION_MIN"], bins=bins_dur, labels=labels_dur)
    tabla_dur = (
        df_dur.groupby("RANGO_DURACION").size()
        .reindex(labels_dur, fill_value=0).reset_index(name="SESIONES")
    )
    fig3 = go.Figure(go.Bar(
        x=tabla_dur["RANGO_DURACION"], y=tabla_dur["SESIONES"],
        marker_color=NOC_YELLOW, opacity=0.85,
        hovertemplate="Rango: %{x} min<br>Sesiones: %{y}<extra></extra>"
    ))
    fig3.update_layout(title="Duración de Sesiones (minutos)",
                       xaxis_title="Minutos", yaxis_title="Sesiones", **PLOTLY_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# 9. FRECUENCIA DE RECARGA + DISTRIBUCIÓN HORARIA – 2 COLUMNAS
# ============================================================
st.markdown('<div class="section-title">■ Comportamiento Operacional</div>', unsafe_allow_html=True)

col_c, col_d = st.columns(2)

# ── Frecuencia de recarga ──
with col_c:
    ses_veh = (
        df.groupby("VEHÍCULO").agg(SESIONES=("ID", "count")).reset_index()
    )
    bins_ses   = [0, 10, 20, 30, 40, 50, float("inf")]
    labels_ses = ["0–10", "10–20", "20–30", "30–40", "40–50", "50+"]
    ses_veh["RANGO_SESIONES"] = pd.cut(ses_veh["SESIONES"], bins=bins_ses,
                                       labels=labels_ses, include_lowest=True)
    freq_ses = (
        ses_veh.groupby("RANGO_SESIONES", observed=True)
        .size().reset_index(name="VEHÍCULOS")
    )
    freq_ses["PCT"] = (freq_ses["VEHÍCULOS"] / freq_ses["VEHÍCULOS"].sum() * 100).round(1)

    fig4 = go.Figure(go.Bar(
        x=freq_ses["RANGO_SESIONES"], y=freq_ses["VEHÍCULOS"],
        text=freq_ses["PCT"].astype(str) + "%",
        textposition="outside",
        marker_color=NOC_BLUE, opacity=0.85,
        hovertemplate="Rango: %{x}<br>Vehículos: %{y}<extra></extra>"
    ))
    fig4.update_layout(title="Frecuencia de Recarga por Vehículo",
                       xaxis_title="Sesiones / Vehículo", yaxis_title="N° Vehículos",
                       **PLOTLY_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

# ── Distribución horaria ──
with col_d:
    df_dur2 = df_dur.copy()
    df_dur2 = df_dur2.dropna(subset=["INICIO_DT", "FIN_DT"])
    df_dur2 = df_dur2[df_dur2["FIN_DT"] >= df_dur2["INICIO_DT"]]
    df_dur2["INICIO_H"] = df_dur2["INICIO_DT"].dt.floor("h")
    df_dur2["FIN_H"]    = df_dur2["FIN_DT"].dt.floor("h")

    horas = df_dur2.loc[
        df_dur2.index.repeat(
            ((df_dur2["FIN_H"] - df_dur2["INICIO_H"]).dt.total_seconds() // 3600 + 1)
        )
    ].copy()
    horas["HORA"] = (
        horas["INICIO_H"] + pd.to_timedelta(horas.groupby(level=0).cumcount(), unit="h")
    )
    horas["HORA_DIA"] = horas["HORA"].dt.hour
    horas["FECHA_H"]  = horas["HORA"].dt.date

    tabla_horas_total = (
        horas.groupby("HORA_DIA")["ID"].nunique()
        .reindex(range(24), fill_value=0).reset_index(name="SESIONES_TOTALES")
    )

    tabla_dia_hora = (
        horas.groupby(["FECHA_H", "HORA_DIA"])["ID"].nunique().reset_index(name="SESIONES")
    )
    dias_u = tabla_dia_hora["FECHA_H"].unique()
    idx_full = pd.DataFrame([(d, h) for d in dias_u for h in range(24)],
                            columns=["FECHA_H", "HORA_DIA"])
    tabla_dia_hora_full = (
        idx_full.merge(tabla_dia_hora, on=["FECHA_H", "HORA_DIA"], how="left").fillna(0)
    )
    tabla_horas_prom = (
        tabla_dia_hora_full.groupby("HORA_DIA")["SESIONES"]
        .mean().reset_index(name="PROMEDIO_SESIONES")
    )

    fig5 = make_subplots(specs=[[{"secondary_y": True}]])
    fig5.add_trace(
        go.Bar(x=tabla_horas_total["HORA_DIA"], y=tabla_horas_total["SESIONES_TOTALES"],
               name="Sesiones totales", marker_color=NOC_BLUE, opacity=0.7,
               hovertemplate="Hora: %{x}:00<br>Total: %{y}<extra></extra>"),
        secondary_y=False
    )
    fig5.add_trace(
        go.Scatter(x=tabla_horas_prom["HORA_DIA"], y=tabla_horas_prom["PROMEDIO_SESIONES"],
                   name="Promedio diario", mode="lines+markers",
                   line=dict(color=NOC_GREEN, width=2), marker=dict(size=5),
                   hovertemplate="Hora: %{x}:00<br>Promedio: %{y:.2f}<extra></extra>"),
        secondary_y=True
    )
    fig5.update_layout(title="Distribución Horaria de Sesiones", **PLOTLY_LAYOUT)
    fig5.update_xaxes(tickmode="array", tickvals=list(range(24)),
                      ticktext=[f"{h:02d}h" for h in range(24)])
    fig5.update_yaxes(title_text="Sesiones totales", secondary_y=False,
                      gridcolor=NOC_BORDER, color=NOC_TEXT)
    fig5.update_yaxes(title_text="Promedio / día", secondary_y=True,
                      gridcolor="rgba(0,0,0,0)", color=NOC_TEXT)
    st.plotly_chart(fig5, use_container_width=True)

# ============================================================
# 10. HEATMAP HORARIO (HORA × DÍA DE SEMANA)
# ============================================================
st.markdown('<div class="section-title">■ Mapa de Calor — Intensidad de Uso</div>',
            unsafe_allow_html=True)

df["HORA_DIA"]    = df["INICIO_DT"].dt.hour
df["DIA_SEMANA"]  = df["INICIO_DT"].dt.dayofweek   # 0=Lunes

dias_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

heatmap_data = (
    df.groupby(["DIA_SEMANA", "HORA_DIA"])["ID"]
    .count().reset_index(name="SESIONES")
)

pivot = (
    heatmap_data.pivot(index="DIA_SEMANA", columns="HORA_DIA", values="SESIONES")
    .reindex(index=range(7), columns=range(24))
    .fillna(0)
)

fig_hm = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[f"{h:02d}:00" for h in range(24)],
    y=dias_labels,
    colorscale=[
        [0.0,  NOC_BG],
        [0.25, "#0D2A4A"],
        [0.5,  "#1A5276"],
        [0.75, NOC_BLUE],
        [1.0,  "#A8D8FF"],
    ],
    showscale=True,
    colorbar=dict(
        tickcolor=NOC_MUTED,
        tickfont=dict(color=NOC_MUTED),
        title=dict(text="Sesiones", font=dict(color=NOC_MUTED))
    ),
    hovertemplate="Día: %{y}<br>Hora: %{x}<br>Sesiones: %{z}<extra></extra>"
))
fig_hm.update_layout(
    title="Heatmap — Sesiones por Día de Semana y Hora",
    xaxis_title="Hora del día",
    yaxis_title="",
    **PLOTLY_LAYOUT
)
fig_hm.update_yaxes(autorange="reversed")
st.plotly_chart(fig_hm, use_container_width=True)

# ── Pie de página ────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; color:{NOC_MUTED}; font-size:0.72rem;
            margin-top:30px; letter-spacing:0.1em;">
    ⚡ CENTRO DE MONITOREO VES &nbsp;|&nbsp; Electromovilidad &nbsp;|&nbsp; v2.0
</div>
""", unsafe_allow_html=True)
