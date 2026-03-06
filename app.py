import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard Tiempo Real",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00d4ff; }
    h1, h2, h3 { color: #ffffff !important; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

def load_data_fast(sheet_id):
    """Carga datos con bypass de caché para velocidad máxima."""
    # Añadimos un timestamp a la URL para forzar a Google a dar el dato más fresco
    ts = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&cache_buster={ts}"
    try:
        # Optimizamos la lectura cargando solo lo necesario si el archivo es muy grande
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

def draw_gauge(current_val, reorder_val, title, max_val=100):
    """Genera un velocímetro estilizado."""
    bar_color = "#FF4B4B" if current_val <= reorder_val else "#00CC96"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_val,
        title={'text': f"<b>{title}</b>", 'font': {'size': 18, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 35}},
        gauge={
            'axis': {'range': [0, max_val], 'tickcolor': "white"},
            'bar': {'color': bar_color},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, reorder_val], 'color': 'rgba(255, 75, 75, 0.3)'}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'value': reorder_val}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=40, b=10), height=220)
    return fig

def main():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("⚡ Ultra-Refresh")
        # Permitimos bajar hasta 2 segundos
        refresh_rate = st.slider("Segundos entre actualizaciones", 2, 30, 2)
        reorder_point = st.number_input("Punto de Reorden Global", 0, 100, 15)
        st.warning("⚠️ Valores menores a 5s pueden causar bloqueos temporales por parte de Google API.")

    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    df_raw = load_data_fast(SHEET_ID)

    if df_raw is not None and not df_raw.empty:
        # Tomar la última fila del historial
        latest_data = df_raw.iloc[-1]
        numeric_cols = df_raw.select_dtypes(include=['number']).columns.tolist()

        # Encabezado compacto
        c1, c2 = st.columns([3, 1])
        c1.title("🚀 Monitor en Vivo")
        c2.write(f"⏱️ Actualizado: {datetime.now().strftime('%H:%M:%S')}")

        # Velocímetros
        if numeric_cols:
            cols = st.columns(min(len(numeric_cols), 4))
            for i, col_name in enumerate(numeric_cols[:4]):
                with cols[i]:
                    st.plotly_chart(draw_gauge(latest_data[col_name], reorder_point, col_name), use_container_width=True)

        # Gráfico de tendencia (últimos 15 puntos)
        st.subheader("📈 Tendencia Instantánea")
        st.line_chart(df_raw[numeric_cols].tail(15))
    
    # Lógica de refresco
    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()
