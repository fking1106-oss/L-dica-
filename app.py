import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Inventario Inteligente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PARA ESTÉTICA PREMIUM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #00d4ff; }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

def load_data(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la fuente de datos: {e}")
        return None

def draw_gauge(current_val, reorder_val, title, max_val=100):
    if current_val <= reorder_val:
        bar_color = "#FF4B4B"
    elif current_val <= reorder_val * 1.3:
        bar_color = "#FFAA00"
    else:
        bar_color = "#00CC96"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_val,
        title={'text': f"<b>{title}</b>", 'font': {'size': 20, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 40}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': bar_color, 'thickness': 0.6},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, reorder_val], 'color': 'rgba(255, 75, 75, 0.3)'},
                {'range': [reorder_val, max_val], 'color': 'rgba(0, 204, 150, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': reorder_val
            }
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=30, r=30, t=50, b=20), height=280)
    return fig

def main():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=80)
        st.title("Configuración")
        
        # --- NUEVA SECCIÓN: CÁLCULO DE STOCK DE SEGURIDAD (LÚDICA) ---
        st.divider()
        st.subheader("🛠️ Calculadora de Stock")
        with st.expander("Ingresar Parámetros", expanded=True):
            d1 = st.number_input("Demanda Cliente 1", 0, 20, 5)
            d2 = st.number_input("Demanda Cliente 2", 0, 20, 5)
            d3 = st.number_input("Demanda Cliente 3", 0, 20, 5)
            lead_time = st.number_input("Tiempo Reposición (seg)", 1, 60, 5)
            
            # Cálculo lógico para la lúdica
            promedio_demanda = (d1 + d2 + d3) / 3
            # El stock de seguridad sugerido es la demanda esperada durante el tiempo de espera
            ss_calculado = round(promedio_demanda * (lead_time / 10), 2) # Factor de escala para lúdica
            
        st.metric("Stock de Seguridad Sugerido", f"{ss_calculado} ud")
        
        # Vinculamos el slider al cálculo automático si el usuario lo desea
        usar_calculo = st.checkbox("Usar este stock en Dashboard", value=False)
        
        if usar_calculo:
            reorder_point = ss_calculado
        else:
            reorder_point = st.slider("Punto de Reorden Manual", 0, 100, 15)
        
        refresh_rate = st.select_slider("Actualización (seg)", options=[5, 10, 30, 60], value=5)
        st.divider()

    # --- LÓGICA DE DATOS ---
    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    df_raw = load_data(SHEET_ID)

    if df_raw is not None and not df_raw.empty:
        latest_data = df_raw.iloc[-1]
        numeric_cols = df_raw.select_dtypes(include=['number']).columns.tolist()

        # --- ENCABEZADO ---
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.title("🚀 Monitor de Inventario en Tiempo Real")
        with col_t2:
            st.markdown(f"<p style='text-align:right; color:#888;'>Actualizado: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

        st.divider()

        # --- VISUALIZACIÓN ---
        if len(numeric_cols) > 0:
            cols_gauges = st.columns(min(len(numeric_cols), 4))
            for i, col_name in enumerate(numeric_cols[:4]):
                current_value = latest_data[col_name]
                with cols_gauges[i]:
                    st.plotly_chart(draw_gauge(current_value, reorder_point, col_name), use_container_width=True)

        st.divider()
        col_list, col_graph = st.columns([1, 2])

        with col_list:
            st.subheader("📋 Estado Actual")
            for col_name in numeric_cols[:5]:
                val = latest_data[col_name]
                status = "🔴 Crítico" if val <= reorder_point else "🟢 Normal"
                st.metric(label=col_name, value=val, delta=status, delta_color="normal" if val > reorder_point else "inverse")

        with col_graph:
            st.subheader("📈 Tendencia Reciente")
            st.line_chart(df_raw[numeric_cols].tail(20))

        with st.expander("Ver base de datos completa"):
            st.dataframe(df_raw.sort_index(ascending=False), use_container_width=True)

    else:
        st.warning("Esperando conexión con Google Sheets...")

    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()
