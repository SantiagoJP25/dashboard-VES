#python -m streamlit run C:\Users\jsantiago\Documents\TRANSACCIONES\REPORTE_ENERLINK\Dashboard_Ener_V2.py
import pandas as pd
import streamlit as st
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

NOC_BG     = "#0D1117"
NOC_PANEL  = "#161B22"
NOC_BORDER = "#21262D"
NOC_BLUE   = "#58A6FF"
NOC_GREEN  = "#3FB950"
NOC_YELLOW = "#D29922"
NOC_TEXT   = "#C9D1D9"
NOC_MUTED  = "#8B949E"

st.markdown(f"""
<style>
    .stApp {{ background-color:{NOC_BG}; color:{NOC_TEXT}; }}
    section[data-testid="stSidebar"] {{
        background-color:{NOC_PANEL};
        border-right:1px solid {NOC_BORDER};
    }}
    section[data-testid="stSidebar"] * {{ color:{NOC_TEXT} !important; }}
    section[data-testid="stSidebar"] label {{ color:{NOC_BLUE} !important; font-size:0.78rem !important; letter-spacing:0.06em; }}
    section[data-testid="stSidebar"] h3 {{ color:{NOC_BLUE} !important; font-size:0.95rem !important; }}
    section[data-testid="stSidebar"] .stMultiSelect span {{ background-color:{NOC_BG} !important; border:1px solid {NOC_BORDER} !important; }}
    .noc-header {{
        background:linear-gradient(135deg,{NOC_PANEL} 0%,#0D1F2D 100%);
        border:1px solid {NOC_BLUE}; border-radius:6px;
        padding:10px 20px; margin-bottom:8px;
    }}
    .noc-header h1 {{
        color:{NOC_BLUE}; font-size:1.15rem; font-weight:700;
        margin:0; letter-spacing:0.05em; text-transform:uppercase;
    }}
    .noc-header p {{
        color:{NOC_MUTED}; font-size:0.75rem; margin:2px 0 0 0; letter-spacing:0.08em;
    }}
    .kpi-card {{
        background:{NOC_PANEL}; border:1px solid {NOC_BORDER};
        border-top:2px solid {NOC_BLUE}; border-radius:6px;
        padding:8px 12px; text-align:center;
    }}
    .kpi-label {{
        color:{NOC_MUTED}; font-size:0.65rem; letter-spacing:0.1em;
        text-transform:uppercase; margin-bottom:3px;
    }}
    .kpi-value {{
        color:{NOC_BLUE}; font-size:1.3rem; font-weight:700; line-height:1.1;
    }}
    /* Tabs NOC */
    .stTabs [data-baseweb="tab-list"] {{
        background:{NOC_PANEL}; border-radius:6px; padding:2px 4px;
        border:1px solid {NOC_BORDER};
    }}
    .stTabs [data-baseweb="tab"] {{
        color:{NOC_MUTED}; font-size:0.78rem; letter-spacing:0.08em;
        padding:6px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        color:{NOC_BLUE} !important;
        border-bottom:2px solid {NOC_BLUE} !important;
        background:transparent !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top:10px;
    }}
    #MainMenu, footer, header {{ visibility:hidden; }}
    .block-container {{ padding-top:0.6rem; padding-bottom:0.5rem; }}
</style>
""", unsafe_allow_html=True)

# Layout Plotly: altura reducida para caber en pantalla
def noc_layout(title="", h=300):
    return dict(
        paper_bgcolor=NOC_PANEL, plot_bgcolor=NOC_BG,
        font=dict(color=NOC_TEXT, family="monospace", size=11),
        title_text=title, title_font=dict(color=NOC_BLUE, size=12),
        xaxis=dict(gridcolor=NOC_BORDER, linecolor=NOC_BORDER, tickcolor=NOC_MUTED),
        yaxis=dict(gridcolor=NOC_BORDER, linecolor=NOC_BORDER, tickcolor=NOC_MUTED),
        margin=dict(l=45, r=15, t=38, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=NOC_TEXT), orientation="h", y=1.12),
        height=h
    )

# ============================================================
# CARGA DE DATOS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def cargar_datos():
    transacciones = pd.read_excel(BASE_DIR / "Transacciones.xlsx", header=2)
    maestro       = pd.read_excel(BASE_DIR / "Maestro_MVES.xlsx")
    return transacciones, maestro

transacciones, maestro = cargar_datos()

transacciones = transacciones.dropna(
    subset=["INICIO (UTC-05:00)", "ENERGIA CARGADA (kWh)", "VEHÍCULO", "ID"]
)
transacciones["FECHA"] = pd.to_datetime(transacciones["INICIO (UTC-05:00)"]).dt.date

vehiculos_validos = maestro["VEHÍCULO"].unique()
df_base = transacciones[transacciones["VEHÍCULO"].isin(vehiculos_validos)].copy()
df_base["INICIO_DT"] = pd.to_datetime(df_base["INICIO (UTC-05:00)"])
df_base["FIN_DT"]    = pd.to_datetime(df_base["TÉRMINO (UTC-05:00)"], errors="coerce")

# ============================================================
# SIDEBAR – FILTROS
# ============================================================
with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    st.markdown("---")
    fecha_min = df_base["FECHA"].min()
    fecha_max = df_base["FECHA"].max()
    rango_fechas = st.date_input("Rango de fechas", [fecha_min, fecha_max],
                                 min_value=fecha_min, max_value=fecha_max)
    vehiculos_sel = st.multiselect("Vehículos",
        options=sorted(df_base["VEHÍCULO"].unique()),
        default=sorted(df_base["VEHÍCULO"].unique()))
    st.markdown("---")
    st.markdown(f"<span style='color:{NOC_MUTED};font-size:0.72rem;'>⚡ VES Energy Monitor v2.0</span>",
                unsafe_allow_html=True)

df = df_base[
    (df_base["FECHA"] >= rango_fechas[0]) &
    (df_base["FECHA"] <= rango_fechas[1]) &
    (df_base["VEHÍCULO"].isin(vehiculos_sel))
].copy()

num_dias = (pd.to_datetime(rango_fechas[1]) - pd.to_datetime(rango_fechas[0])).days + 1

# ============================================================
# ENCABEZADO + KPIs  (siempre visibles)
# ============================================================
st.markdown(f"""
<div class="noc-header">
    <h1>⚡ Centro de Monitoreo de Electromovilidad — VES</h1>
    <p>Operación de infraestructura de carga &nbsp;|&nbsp; Estación Villa El Salvador</p>
</div>
""", unsafe_allow_html=True)

kwh_total         = df["ENERGIA CARGADA (kWh)"].sum()
total_sesiones    = df["ID"].count()
vehiculos_activos = df["VEHÍCULO"].nunique()
kwh_dia           = kwh_total / num_dias if num_dias > 0 else 0
ses_dia           = total_sesiones / num_dias if num_dias > 0 else 0

kpis = [
    ("⚡ Energía Total",            f"{kwh_total:,.1f} kWh"),
    ("🔌 Sesiones Totales",         f"{total_sesiones:,}"),
    ("🚗 Vehículos Activos",        f"{vehiculos_activos}"),
    ("📅 kWh Promedio / Día",       f"{kwh_dia:,.1f}"),
    ("📈 Sesiones Promedio / Día",  f"{ses_dia:.1f}"),
]
for col, (label, value) in zip(st.columns(5), kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ============================================================
# TABS – cada pestaña = 1 pantalla
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Consumo & Tendencia",
    "⚡  Distribuciones",
    "🚗  Comportamiento",
    "🔥  Heatmap Horario"
])

# ──────────────────────────────────────────────────────────────
# TAB 1 – Consumo diario + Tendencia mensual
# ──────────────────────────────────────────────────────────────
with tab1:
    df["FECHA_DT"] = pd.to_datetime(df["FECHA"])
    calendario = pd.DataFrame({
        "FECHA": pd.date_range(
            start=pd.to_datetime(rango_fechas[0]),
            end=pd.to_datetime(rango_fechas[1]), freq="D")
    })
    consumo_diario = (
        df.groupby("FECHA_DT", as_index=False)
        .agg(KWH=("ENERGIA CARGADA (kWh)", "sum"), SES=("ID", "count"))
        .rename(columns={"FECHA_DT": "FECHA"})
    )
    consumo_diario = calendario.merge(consumo_diario, on="FECHA", how="left").fillna(0)

    df["MES"] = df["FECHA_DT"].dt.to_period("M").astype(str)
    tendencia = (
        df.groupby("MES", as_index=False)
        .agg(KWH_MES=("ENERGIA CARGADA (kWh)", "sum"), SES_MES=("ID", "count"))
    )

    col1, col2 = st.columns(2)

    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=consumo_diario["FECHA"], y=consumo_diario["KWH"],
            mode="lines+markers", line=dict(color=NOC_BLUE, width=1.8),
            marker=dict(size=4), fill="tozeroy",
            fillcolor="rgba(88,166,255,0.10)",
            customdata=consumo_diario[["SES"]],
            hovertemplate="<b>%{x|%d-%m-%Y}</b><br>kWh: %{y:.1f}<br>Sesiones: %{customdata[0]}<extra></extra>"
        ))
        fig1.update_layout(**noc_layout("Consumo diario de energía (kWh)"))
        fig1.update_xaxes(title_text="Fecha")
        fig1.update_yaxes(title_text="kWh")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig_t = make_subplots(specs=[[{"secondary_y": True}]])
        fig_t.add_trace(
            go.Bar(x=tendencia["MES"], y=tendencia["KWH_MES"],
                   name="kWh / Mes", marker_color=NOC_BLUE, opacity=0.8,
                   hovertemplate="Mes: %{x}<br>kWh: %{y:,.0f}<extra></extra>"),
            secondary_y=False)
        fig_t.add_trace(
            go.Scatter(x=tendencia["MES"], y=tendencia["SES_MES"],
                       name="Sesiones / Mes", mode="lines+markers",
                       line=dict(color=NOC_GREEN, width=2), marker=dict(size=5),
                       hovertemplate="Mes: %{x}<br>Sesiones: %{y}<extra></extra>"),
            secondary_y=True)
        fig_t.update_layout(**noc_layout("Tendencia mensual – Energía y Sesiones"))
        fig_t.update_yaxes(title_text="kWh", secondary_y=False,
                           gridcolor=NOC_BORDER, color=NOC_TEXT)
        fig_t.update_yaxes(title_text="Sesiones", secondary_y=True,
                           gridcolor="rgba(0,0,0,0)", color=NOC_TEXT)
        st.plotly_chart(fig_t, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# TAB 2 – Rangos kWh + Duración
# ──────────────────────────────────────────────────────────────
with tab2:
    bins_kwh   = [0, 10, 20, 30, 40, 50, 60, float("inf")]
    labels_kwh = ["0–10", "10–20", "20–30", "30–40", "40–50", "50–60", "60+"]
    df["RANGO_KWH"] = pd.cut(df["ENERGIA CARGADA (kWh)"], bins=bins_kwh, labels=labels_kwh)
    tabla_kwh = (
        df.groupby("RANGO_KWH").size()
        .reindex(labels_kwh, fill_value=0).reset_index(name="SESIONES")
    )

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

    col_a, col_b = st.columns(2)

    with col_a:
        fig2 = go.Figure(go.Bar(
            x=tabla_kwh["RANGO_KWH"], y=tabla_kwh["SESIONES"],
            marker_color=NOC_GREEN, opacity=0.85,
            hovertemplate="Rango: %{x} kWh<br>Sesiones: %{y}<extra></extra>"
        ))
        fig2.update_layout(**noc_layout("Distribución por Rango de kWh"))
        fig2.update_xaxes(title_text="kWh por sesión")
        fig2.update_yaxes(title_text="Sesiones")
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        fig3 = go.Figure(go.Bar(
            x=tabla_dur["RANGO_DURACION"], y=tabla_dur["SESIONES"],
            marker_color=NOC_YELLOW, opacity=0.85,
            hovertemplate="Rango: %{x} min<br>Sesiones: %{y}<extra></extra>"
        ))
        fig3.update_layout(**noc_layout("Duración de Sesiones (minutos)"))
        fig3.update_xaxes(title_text="Duración (min)")
        fig3.update_yaxes(title_text="Sesiones")
        st.plotly_chart(fig3, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# TAB 3 – Frecuencia recarga + Distribución horaria
# ──────────────────────────────────────────────────────────────
with tab3:
    # Frecuencia de recarga
    ses_veh = df.groupby("VEHÍCULO").agg(SESIONES=("ID", "count")).reset_index()
    bins_ses   = [0, 10, 20, 30, 40, 50, float("inf")]
    labels_ses = ["0–10", "10–20", "20–30", "30–40", "40–50", "50+"]
    ses_veh["RANGO"] = pd.cut(ses_veh["SESIONES"], bins=bins_ses,
                              labels=labels_ses, include_lowest=True)
    freq_ses = ses_veh.groupby("RANGO", observed=True).size().reset_index(name="VEHÍCULOS")
    freq_ses["PCT"] = (freq_ses["VEHÍCULOS"] / freq_ses["VEHÍCULOS"].sum() * 100).round(1)

    # Distribución horaria
    if "df_dur" not in dir():
        df_dur = df.dropna(subset=["INICIO_DT", "FIN_DT"]).copy()
        df_dur["DURACION_MIN"] = (df_dur["FIN_DT"] - df_dur["INICIO_DT"]).dt.total_seconds() / 60
        df_dur = df_dur[df_dur["DURACION_MIN"] > 0]

    df_h = df_dur[df_dur["FIN_DT"] >= df_dur["INICIO_DT"]].copy()
    df_h["INICIO_H"] = df_h["INICIO_DT"].dt.floor("h")
    df_h["FIN_H"]    = df_h["FIN_DT"].dt.floor("h")
    horas = df_h.loc[
        df_h.index.repeat(
            ((df_h["FIN_H"] - df_h["INICIO_H"]).dt.total_seconds() // 3600 + 1)
        )
    ].copy()
    horas["HORA"] = (
        horas["INICIO_H"] + pd.to_timedelta(horas.groupby(level=0).cumcount(), unit="h")
    )
    horas["HORA_DIA"] = horas["HORA"].dt.hour
    horas["FECHA_H"]  = horas["HORA"].dt.date

    tabla_total = (
        horas.groupby("HORA_DIA")["ID"].nunique()
        .reindex(range(24), fill_value=0).reset_index(name="SESIONES_TOTALES")
    )
    tabla_dh = horas.groupby(["FECHA_H", "HORA_DIA"])["ID"].nunique().reset_index(name="SESIONES")
    dias_u = tabla_dh["FECHA_H"].unique()
    idx_full = pd.DataFrame([(d, h) for d in dias_u for h in range(24)],
                            columns=["FECHA_H", "HORA_DIA"])
    tabla_prom = (
        idx_full.merge(tabla_dh, on=["FECHA_H", "HORA_DIA"], how="left").fillna(0)
        .groupby("HORA_DIA")["SESIONES"].mean().reset_index(name="PROMEDIO")
    )

    col_c, col_d = st.columns(2)

    with col_c:
        fig4 = go.Figure(go.Bar(
            x=freq_ses["RANGO"], y=freq_ses["VEHÍCULOS"],
            text=freq_ses["PCT"].astype(str) + "%", textposition="outside",
            marker_color=NOC_BLUE, opacity=0.85,
            hovertemplate="Rango: %{x}<br>Vehículos: %{y}<extra></extra>"
        ))
        fig4.update_layout(**noc_layout("Frecuencia de Recarga por Vehículo"))
        fig4.update_xaxes(title_text="Sesiones / Vehículo")
        fig4.update_yaxes(title_text="N° Vehículos")
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        fig5 = make_subplots(specs=[[{"secondary_y": True}]])
        fig5.add_trace(
            go.Bar(x=tabla_total["HORA_DIA"], y=tabla_total["SESIONES_TOTALES"],
                   name="Total", marker_color=NOC_BLUE, opacity=0.7,
                   hovertemplate="Hora: %{x}:00<br>Total: %{y}<extra></extra>"),
            secondary_y=False)
        fig5.add_trace(
            go.Scatter(x=tabla_prom["HORA_DIA"], y=tabla_prom["PROMEDIO"],
                       name="Promedio/día", mode="lines+markers",
                       line=dict(color=NOC_GREEN, width=2), marker=dict(size=4),
                       hovertemplate="Hora: %{x}:00<br>Prom: %{y:.2f}<extra></extra>"),
            secondary_y=True)
        fig5.update_layout(**noc_layout("Distribución Horaria de Sesiones"))
        fig5.update_xaxes(tickmode="array", tickvals=list(range(0,24,2)),
                          ticktext=[f"{h:02d}h" for h in range(0,24,2)])
        fig5.update_yaxes(title_text="Sesiones totales", secondary_y=False,
                          gridcolor=NOC_BORDER, color=NOC_TEXT)
        fig5.update_yaxes(title_text="Promedio/día", secondary_y=True,
                          gridcolor="rgba(0,0,0,0)", color=NOC_TEXT)
        st.plotly_chart(fig5, use_container_width=True)

# ──────────────────────────────────────────────────────────────
# TAB 4 – Heatmap horario
# ──────────────────────────────────────────────────────────────
with tab4:
    df["HORA_DIA"]   = df["INICIO_DT"].dt.hour
    df["DIA_SEMANA"] = df["INICIO_DT"].dt.dayofweek
    dias_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    pivot = (
        df.groupby(["DIA_SEMANA", "HORA_DIA"])["ID"]
        .count().reset_index(name="SESIONES")
        .pivot(index="DIA_SEMANA", columns="HORA_DIA", values="SESIONES")
        .reindex(index=range(7), columns=range(24)).fillna(0)
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
        colorbar=dict(tickcolor=NOC_MUTED, tickfont=dict(color=NOC_MUTED),
                      title=dict(text="Sesiones", font=dict(color=NOC_MUTED))),
        hovertemplate="Día: %{y}<br>Hora: %{x}<br>Sesiones: %{z}<extra></extra>"
    ))
    fig_hm.update_layout(**noc_layout("Heatmap — Sesiones por Día de Semana y Hora", h=340))
    fig_hm.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_hm, use_container_width=True)

# ── Pie ──────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:{NOC_MUTED};font-size:0.68rem;
            margin-top:6px;letter-spacing:0.1em;">
    ⚡ CENTRO DE MONITOREO VES &nbsp;|&nbsp; Electromovilidad &nbsp;|&nbsp; v2.0
</div>
""", unsafe_allow_html=True)