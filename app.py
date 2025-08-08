# =============================
# Dashboard Premium de Trading Automatizado
# Autor: ChatGPT (OpenAI) para Mauricio
# =============================

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ---------- CONFIGURACIÓN GENERAL ---------- #
TICKER = "XAU/USD"
SCORE_THRESHOLD = 9.0
RISK_PCT = 0.01

# Claves API proporcionadas por el usuario
API_TWELVE = "40bc61c44af5415f949ca5e1aa5c1967"
API_FRED = "8ba8c690ce390901ebc917d40fa80090"

# ---------- FUNCIONES DE CONEXIÓN DE DATOS ---------- #
def get_ohlcv(symbol="XAU/USD", interval="1h"):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={API_TWELVE}"
    r = requests.get(url).json()
    df = pd.DataFrame(r['values'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values("datetime")
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    return df

def get_vix():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1d&range=5d"
    r = requests.get(url).json()
    prices = r['chart']['result'][0]['indicators']['quote'][0]['close']
    return prices[-1]

def get_macro_fred(series_id="T10Y2Y"):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": API_FRED,
        "file_type": "json"
    }
    r = requests.get(url, params=params).json()
    values = r['observations']
    return float(values[-1]['value'])

# ---------- FACTORES CLAVE ---------- #
def calculate_factors(df):
    atr = (df['high'] - df['low']).rolling(window=14).mean().iloc[-1]
    vix = get_vix()
    macro = get_macro_fred()
    vol_trigger = 1 if vix > 20 else 0
    return {
        'ATR': round(atr, 2),
        'VIX': vix,
        'MACRO_SPREAD': macro,
        'VOL_TRIGGER': vol_trigger
    }

# ---------- SCORING ---------- #
def score_trade(factors):
    weights = {
        'ATR': 0.3,
        'VIX': 0.3,
        'MACRO_SPREAD': 0.3,
        'VOL_TRIGGER': 0.1
    }
    scaled = {
        'ATR': min(factors['ATR'] / 3, 1),
        'VIX': min(factors['VIX'] / 25, 1),
        'MACRO_SPREAD': 1 - abs(factors['MACRO_SPREAD']) / 2,
        'VOL_TRIGGER': factors['VOL_TRIGGER']
    }
    score = sum(weights[k] * scaled[k] for k in weights)
    return round(score * 10, 2)

# ---------- DASHBOARD UI ---------- #
st.set_page_config(page_title="Dashboard Trading Premium", layout="centered")
st.title("📊 Dashboard Premium de Trading Automatizado")

try:
    df = get_ohlcv()
    factors = calculate_factors(df)
    score = score_trade(factors)

    st.subheader("✅ Factores Clave")
    st.json(factors)

    st.subheader("📈 Score del Setup Actual")
    st.metric("Score", f"{score}/10")

    if score >= SCORE_THRESHOLD:
        st.success("✅ Condiciones óptimas para operar (Score ≥ 9)")
        st.markdown("**Tipo de orden sugerido:** Buy Limit sobre soporte + confirmación de VWAP")
    else:
        st.warning("⚠️ No operar. Score insuficiente")

    log = pd.DataFrame([{"timestamp": datetime.now(), "score": score, **factors}])
    st.download_button("📥 Descargar log", data=log.to_csv(index=False), file_name="log_trading.csv")

except Exception as e:
    st.error(f"Error en la carga de datos: {e}")
