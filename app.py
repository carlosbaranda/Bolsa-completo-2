import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date
import io

st.set_page_config(page_title="Top Bolsas", layout="wide")
st.title("Top Activos - NYSE, Bolsa Española y ETFs")
st.markdown("Selecciona un **mercado** y tipo de **activo** para ver las mayores subidas del **día**, la **semana** y lo que va del **año (YTD)**.")

# Tickers por mercado y tipo de activo
acciones_nyse = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "WMT", "UNH", "KO", "PEP", "V", "BAC", "HD"]
acciones_espana = ["SAN.MC", "BBVA.MC", "ITX.MC", "IBE.MC", "REP.MC", "AMS.MC", "ANA.MC", "CABK.MC", "CLNX.MC", "ENG.MC", "FER.MC", "GRF.MC", "IAG.MC", "MAP.MC", "TEF.MC"]
etfs = ["SPY", "QQQ", "DIA", "VTI", "IWM", "EFA", "EEM", "VNQ", "LQD", "HYG", "XLF", "XLK", "XLE", "XLY", "XLV"]

mercado = st.selectbox("Selecciona el mercado", ["NYSE (EEUU)", "Bolsa Española (BME)", "EuroStoxx"])
tipo = st.radio("Selecciona el tipo de activo", ["Acciones", "ETFs"])

if tipo == "ETFs":
    tickers = etfs
elif mercado == "EuroStoxx":
    tickers = ['AIR.PA', 'ADS.DE', 'ALV.DE', 'BN.PA', 'ENEL.MI', 'ENGI.PA', 'OR.PA', 'SAP.DE', 'SIE.DE', 'SU.PA', 'TTE.PA', 'VOW3.DE', 'DTE.DE', 'DPW.DE', 'BAS.DE']
elif mercado == "NYSE (EEUU)":
    tickers = acciones_nyse
else:
    tickers = acciones_espana

@st.cache_data(ttl=3600)
def obtener_datos(tickers):
    data = []
    inicio_ano = datetime(datetime.now().year, 1, 1)

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(start=inicio_ano)

            if len(hist) >= 7:
                hoy = (hist['Close'][-1] - hist['Open'][-1]) / hist['Open'][-1] * 100
                semana = (hist['Close'][-1] - hist['Close'][-6]) / hist['Close'][-6] * 100
                ytd = (hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100
                actual = hist['Close'][-1]

                data.append({
                    "Ticker": ticker,
                    "Nombre": info.get("shortName", ""),
                    "Cambio Día (%)": round(hoy, 2),
                    "Cambio Semana (%)": round(semana, 2),
                    "Cambio YTD (%)": round(ytd, 2),
                    "Precio actual": round(actual, 2),
                    "Sector": info.get("sector", "N/A"),
                    "País": info.get("country", "N/A"),
                    "Volumen": int(hist["Volume"][-1]),
                    "Volumen Promedio 75": int(hist["Volume"].rolling(75).mean().iloc[-1]),
                    "Diferencia Volumen (%)": round((hist["Volume"][-1] - hist["Volume"].rolling(75).mean().iloc[-1]) / hist["Volume"].rolling(75).mean().iloc[-1] * 100, 2)
                })
        except:
            continue
    return pd.DataFrame(data)

df = obtener_datos(tickers)

if not df.empty and "Cambio Día (%)" in df.columns:
    st.subheader("📅 Variación del Día")
    st.dataframe(df.sort_values("Cambio Día (%)", ascending=False), use_container_width=True)
else:
    st.warning("No se pudieron obtener datos para mostrar la variación del día.")

if not df.empty and "Cambio Semana (%)" in df.columns:
    st.subheader("📅 Variación de la Semana")
    st.dataframe(df.sort_values("Cambio Semana (%)", ascending=False), use_container_width=True)
else:
    st.warning("No se pudieron obtener datos para mostrar la variación semanal.")

if not df.empty and "Cambio YTD (%)" in df.columns:
    st.subheader("📅 Variación del Año (YTD)")
    st.dataframe(df.sort_values("Cambio YTD (%)", ascending=False), use_container_width=True)
else:
    st.warning("No se pudieron obtener datos para mostrar la variación del año.")

st.subheader("📅 Variación de la Semana")
st.dataframe(df.sort_values("Cambio Semana (%)", ascending=False), use_container_width=True)

st.subheader("📅 Variación del Año (YTD)")
st.dataframe(df.sort_values("Cambio YTD (%)", ascending=False), use_container_width=True)

# Filtro
st.subheader("🔍 Filtrar por nombre o ticker")
busqueda = st.text_input("Escribe parte del nombre o ticker para filtrar:")
df_filtrado = df[df["Ticker"].str.contains(busqueda.upper())] if busqueda else df

st.subheader("📋 Resultados filtrados")
st.dataframe(df_filtrado.sort_values("Cambio Día (%)", ascending=False), use_container_width=True)

# Orden por precio
st.subheader("🔽 Ordenar por precio actual")
orden_descendente = st.checkbox("Orden descendente", value=True)
df_ordenado = df.sort_values("Precio actual", ascending=not orden_descendente)
st.dataframe(df_ordenado, use_container_width=True)

# Exportar a Excel
st.subheader("📥 Exportar datos a Excel")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Datos Bolsa")
    

st.download_button(
    label="📤 Descargar Excel",
    data=buffer,
    file_name=f"datos_bolsa_{date.today()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Gráfico
st.subheader("📊 Evolución del precio de una acción o ETF")
opcion_ticker = st.selectbox("Selecciona un activo para ver su gráfico:", df["Ticker"])
if opcion_ticker:
    stock = yf.Ticker(opcion_ticker)
    hist = stock.history(period="6mo")
    st.line_chart(hist["Close"], use_container_width=True, height=300)


# --- Gráfico por sector ---
st.subheader("📊 Distribución por sector")

sectores = df["Sector"].value_counts()
if not sectores.empty:
    fig, ax = plt.subplots()
    sectores.plot(kind="bar", ax=ax)
    ax.set_ylabel("Número de activos")
    ax.set_xlabel("Sector")
    ax.set_title("Cantidad de activos por sector")
    st.pyplot(fig)
else:
    st.info("No hay información de sector disponible para estos activos.")


# --- Gráfico por país ---
st.subheader("🌍 Distribución por país")

paises = df["País"].value_counts()
if not paises.empty:
    fig2, ax2 = plt.subplots()
    paises.plot(kind="bar", ax=ax2)
    ax2.set_ylabel("Número de activos")
    ax2.set_xlabel("País")
    ax2.set_title("Cantidad de activos por país")
    st.pyplot(fig2)
else:
    st.info("No hay información de país disponible para estos activos.")


# --- Tabla de diferencia de volumen actual vs media 75 sesiones ---
st.subheader("📊 Comparativa de volumen actual vs media 75 sesiones")

columnas_vol = ["Ticker", "Nombre", "Volumen", "Volumen Promedio 75", "Diferencia Volumen (%)"]
df_vol = df[columnas_vol].sort_values("Diferencia Volumen (%)", ascending=False)
import numpy as np
styled_df_vol = df_vol.style.apply(
    lambda x: ["background-color: lightgreen" if v > 0 else "background-color: salmon" for v in x["Diferencia Volumen (%)"]],
    axis=1
)
st.dataframe(styled_df_vol, use_container_width=True)
