import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
#python -m streamlit run Dashboard.Ener.py
#https://dashboard-ves-udkkcnf6n3dvtyuqzguzw6.streamlit.app/
# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(
    page_title="Dashboard de Cargas VES",
    layout="wide"
)

st.title("⚡ Dashboard de Cargas Eléctricas – VES")

# -----------------------------
# 1. Cargar datos
# -----------------------------
transacciones = pd.read_excel(
    "Transacciones.xlsx",
    header=2
)

maestro = pd.read_excel(
    "Maestro_MVES.xlsx"
)

# -----------------------------
# 2. Limpieza y preparación
# -----------------------------
transacciones = transacciones.dropna(
    subset=["INICIO (UTC-05:00)", "ENERGIA CARGADA (kWh)", "VEHÍCULO", "ID"]
)

transacciones["FECHA"] = pd.to_datetime(
    transacciones["INICIO (UTC-05:00)"]
).dt.date

vehiculos_validos = maestro["VEHÍCULO"].unique()

df = transacciones[
    transacciones["VEHÍCULO"].isin(vehiculos_validos)
].copy()

df["INICIO_DT"] = pd.to_datetime(df["INICIO (UTC-05:00)"])
df["FIN_DT"] = pd.to_datetime(df["TÉRMINO (UTC-05:00)"], errors="coerce")

# -----------------------------
# 3. Sidebar – filtros
# -----------------------------
st.sidebar.header("🎛️ Filtros")

fecha_min = df["FECHA"].min()
fecha_max = df["FECHA"].max()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    [fecha_min, fecha_max]
)

vehiculos_sel = st.sidebar.multiselect(
    "Vehículos",
    options=sorted(df["VEHÍCULO"].unique()),
    default=sorted(df["VEHÍCULO"].unique())
)

df = df[
    (df["FECHA"] >= rango_fechas[0]) &
    (df["FECHA"] <= rango_fechas[1]) &
    (df["VEHÍCULO"].isin(vehiculos_sel))
]
num_dias = (pd.to_datetime(rango_fechas[1]) - pd.to_datetime(rango_fechas[0])).days + 1
# -----------------------------
# 4. KPIs
# -----------------------------
kwh_total = df["ENERGIA CARGADA (kWh)"].sum()
total_sesiones = df["ID"].count()
vehiculos_activos = df["VEHÍCULO"].nunique()
kwh_promedio_dia = kwh_total / num_dias if num_dias > 0 else 0
sesion_promedio = total_sesiones / num_dias if num_dias > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("⚡ kWh Totales", f"{kwh_total:,.1f}")
col2.metric("🔌 Sesiones", total_sesiones)
col3.metric("🚗 Vehículos activos", vehiculos_activos)
col4.metric("📅 kWh promedio / día", f"{kwh_promedio_dia:,.1f}")
col5.metric("📈 sesiones promedio / día", f"{sesion_promedio:.1f}")

# -----------------------------
# 5. Consumo diario
# -----------------------------
df["FECHA"] = pd.to_datetime(df["FECHA"])

# calendario completo
calendario = pd.DataFrame({
    "FECHA": pd.date_range(
        start=pd.to_datetime(rango_fechas[0]),
        end=pd.to_datetime(rango_fechas[1]),
        freq="D"
    )
})

# Agrupar consumo real
consumo_diario = (
    df.groupby("FECHA", as_index=False)
    .agg(
        KWH_CONSUMIDOS=("ENERGIA CARGADA (kWh)", "sum"),
        SESIONES=("ID", "count")
    )
)

# Unir con calendario y rellenar ceros
consumo_diario = (
    calendario
    .merge(consumo_diario, on="FECHA", how="left")
    .fillna(0)
)

fig1 = px.line(
    consumo_diario,
    x="FECHA",
    y="KWH_CONSUMIDOS",
    markers=True,
    title="Consumo diario de energía (kWh)",
    custom_data=["SESIONES"]  # 
)

# Tooltip personalizado
fig1.update_traces(
    hovertemplate=
    "<b>Fecha:</b> %{x|%d-%m-%Y}<br>"
    "<b>Energía consumida:</b> %{y:.1f} kWh<br>"
    "<b>Sesiones de carga:</b> %{customdata[0]}<br>"
    "<extra></extra>"
)

# Etiquetas de ejes
fig1.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Energía consumida (kWh)"
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# 6. Rangos de consumo por sesión (kWh)
# -----------------------------
bins_kwh = [0, 10, 20, 30, 40, 50, 60, float("inf")]
labels_kwh = ["0–10", "10–20", "20–30", "30–40", "40–50", "50–60", "60+"]

df["RANGO_KWH"] = pd.cut(
    df["ENERGIA CARGADA (kWh)"],
    bins=bins_kwh,
    labels=labels_kwh
)

tabla_kwh = (
    df.groupby("RANGO_KWH")
    .size()
    .reindex(labels_kwh, fill_value=0)
    .reset_index(name="SESIONES")
)

fig2 = px.bar(
    tabla_kwh,
    x="RANGO_KWH",
    y="SESIONES",
    title="Distribución de sesiones por rango de kWh"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# 7. Duración de sesiones
# -----------------------------
df_dur = df.dropna(subset=["INICIO_DT", "FIN_DT"]).copy()

df_dur["DURACION_MIN"] = (
    (df_dur["FIN_DT"] - df_dur["INICIO_DT"])
    .dt.total_seconds() / 60
)

df_dur = df_dur[df_dur["DURACION_MIN"] > 0]

bins_dur = [0, 10, 20, 30, 40, 50, 60, float("inf")]
labels_dur = ["0–10", "10–20", "20–30", "30–40","40–50", "50–60", "60+"]

df_dur["RANGO_DURACION"] = pd.cut(
    df_dur["DURACION_MIN"],
    bins=bins_dur,
    labels=labels_dur
)

tabla_duracion = (
    df_dur.groupby("RANGO_DURACION")
    .size()
    .reindex(labels_dur, fill_value=0)
    .reset_index(name="SESIONES")
)

fig3 = px.bar(
    tabla_duracion,
    x="RANGO_DURACION",
    y="SESIONES",
    title="Duración de sesiones de carga (minutos)"
)

st.plotly_chart(fig3, use_container_width=True)

# -------------------------------------
# 8. Frecuencia de recarga de vehículos
# -------------------------------------
sesiones_por_vehiculo = (
    df.groupby("VEHÍCULO")
    .agg(SESIONES=("ID", "count"))
    .reset_index()
)

bins_ses = [0, 5, 10, 15, 20, 25, 30, float("inf")]
labels_ses = ["0–5", "5–10", "10–15", "15–20", "20–25", "25–30", "30+"]

sesiones_por_vehiculo["RANGO_SESIONES"] = pd.cut(
    sesiones_por_vehiculo["SESIONES"],
    bins=bins_ses,
    labels=labels_ses,
    include_lowest=True
)

frecuencia_sesiones = (
    sesiones_por_vehiculo
    .groupby("RANGO_SESIONES", observed=True)
    .size()
    .reset_index(name="VEHÍCULOS")
)

frecuencia_sesiones["PORCENTAJE (%)"] = (
    frecuencia_sesiones["VEHÍCULOS"]
    / frecuencia_sesiones["VEHÍCULOS"].sum()
    * 100
).round(2).astype(str) + "%"

fig4 = px.bar(
    frecuencia_sesiones,
    x="RANGO_SESIONES",
    y="VEHÍCULOS",
    text="PORCENTAJE (%)",
    title="Frecuencia de recarga de vehículos"
)

fig4.update_traces(textposition="outside")

st.plotly_chart(fig4, use_container_width=True)


# -----------------------------
# 9. Sesiones por hora del día
# -----------------------------

# Expandir cada sesión por hora ocupada
def horas_ocupadas(row):
    return pd.date_range(
        row["INICIO_DT"].replace(minute=0, second=0),
        row["FIN_DT"].replace(minute=0, second=0),
        freq="h"
    )

horas = (
    df_dur
    .assign(HORA=df_dur.apply(horas_ocupadas, axis=1))
    .explode("HORA")
)

horas["HORA_DIA"] = horas["HORA"].dt.hour
horas["FECHA"] = horas["HORA"].dt.date


# A. SESIONES TOTALES POR HORA
tabla_horas_total = (
    horas.groupby("HORA_DIA")["ID"]
    .nunique()
    .reindex(range(24), fill_value=0)
    .reset_index(name="SESIONES_TOTALES")
)

# B. SESIONES POR DÍA Y HORA (BASE DEL PROMEDIO)
tabla_dia_hora = (
    horas
    .groupby(["FECHA", "HORA_DIA"])["ID"]
    .nunique()
    .reset_index(name="SESIONES")
)

# C. COMPLETAR TODAS LAS HORAS PARA TODOS LOS DÍAS
dias = tabla_dia_hora["FECHA"].unique()

index_completo = pd.DataFrame(
    [(d, h) for d in dias for h in range(24)],
    columns=["FECHA", "HORA_DIA"]
)

tabla_dia_hora_full = (
    index_completo
    .merge(tabla_dia_hora, on=["FECHA", "HORA_DIA"], how="left")
    .fillna({"SESIONES": 0})
)

# D. PROMEDIO REAL POR HORA (TODOS LOS DÍAS)
tabla_horas_promedio = (
    tabla_dia_hora_full
    .groupby("HORA_DIA")["SESIONES"]
    .mean()
    .reset_index(name="PROMEDIO_SESIONES")
)

# E. GRÁFICO CON EJE Y SECUNDARIO
fig4 = make_subplots(
    specs=[[{"secondary_y": True}]]
)

# Barras → sesiones totales
fig4.add_trace(
    go.Bar(
        x=tabla_horas_total["HORA_DIA"],
        y=tabla_horas_total["SESIONES_TOTALES"],
        name="Sesiones totales",
        opacity=0.75
    ),
    secondary_y=False
)

# Línea → promedio diario
fig4.add_trace(
    go.Scatter(
        x=tabla_horas_promedio["HORA_DIA"],
        y=tabla_horas_promedio["PROMEDIO_SESIONES"],
        name="Promedio diario",
        mode="lines+markers",
        line=dict(width=3, color='lime')
    ),
    secondary_y=True
)

# F. CONFIGURACIÓN FINAL
fig4.update_layout(
    title="Distribución horaria de sesiones de carga(Total acumulado y promedio diario)",
    xaxis_title="Hora del día",
    legend=dict(
        orientation="h",
        y=1.15,
        x=0.25
    )
)

fig4.update_xaxes(
    tickmode="array",
    tickvals=list(range(24)),
    ticktext=[f"{h:02d}:00" for h in range(24)],
    title="Hora del día"
)

fig4.update_traces(
    hovertemplate=
    "<b>Hora:</b> %{x}:00<br>"
    "<b>Total de sesiones:</b> %{y}"
    "<extra></extra>",
    selector=dict(type="bar")
)

fig4.update_traces(
    hovertemplate=
    "<b>Hora:</b> %{x}:00<br>"
    "<b>Promedio diario:</b> %{y:.2f}"
    "<extra></extra>",
    selector=dict(type="scatter")
)

st.plotly_chart(fig4, use_container_width=True)


