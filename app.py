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
    h1, h2, h3 { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    .stNumberInput div div input { color: #00d4ff !important; }
    </style>
    """, unsafe_allow_html=True)

def load_data(sheet_id):
    """Carga datos desde Google Sheets con bypass de caché."""
    ts = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&cb={ts}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la fuente de datos: {e}")
        return None

def draw_gauge(current_val, reorder_val, title, max_val=100):
    """Genera un velocímetro estilizado con zonas de color."""
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
            'axis': {'range': [0, max(max_val, current_val + 10)], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': bar_color, 'thickness': 0.6},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, reorder_val], 'color': 'rgba(255, 75, 75, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': reorder_val
            }
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      margin=dict(l=30, r=30, t=50, b=20), height=280)
    return fig

def main():
    # --- BARRA LATERAL: CALCULADORA DE STOCK DE SEGURIDAD ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=80)
        st.title("Configuración")
        
        st.subheader("🛠️ Calculadora de Stock")
        with st.expander("Ingresar Demanda de Clientes", expanded=True):
            demanda_c1 = st.number_input("Cliente 1 (uds/día)", min_value=0, value=10)
            demanda_c2 = st.number_input("Cliente 2 (uds/día)", min_value=0, value=15)
            demanda_c3 = st.number_input("Cliente 3 (uds/día)", min_value=0, value=5)
            lead_time = st.number_input("Tiempo de Reposición (días)", min_value=1, value=3)
            
            # Cálculo de Stock de Seguridad (Demanda Total Diaria * Lead Time)
            # Este es un cálculo simplificado de punto de pedido
            demanda_total = demanda_c1 + demanda_c2 + demanda_c3
            safety_stock_calculado = demanda_total * lead_time
            
            st.info(f"**Stock de Seguridad Sugerido: {safety_stock_calculado} unidades**")

        # Usar el stock calculado como punto de reorden
        manual_override = st.checkbox("¿Usar stock calculado como límite?", value=True)
        if manual_override:
            reorder_point = safety_stock_calculado
        else:
            reorder_point = st.slider("Punto de Reorden Manual", 0, 200, 15)
        
        refresh_rate = st.select_slider("Velocidad de actualización (seg)", options=[2, 5, 10, 30, 60], value=5)
        
        st.divider()
        st.caption("Los datos se toman de la última fila del historial.")

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

        # --- VELOCÍMETROS ---
        if len(numeric_cols) > 0:
            cols_gauges = st.columns(min(len(numeric_cols), 4))
            for i, col_name in enumerate(numeric_cols[:4]):
                current_value = latest_data[col_name]
                # Ajustamos el máximo del velocímetro para que no se vea pequeño si el stock es alto
                max_gauge = max(100, current_value * 1.5, reorder_point * 1.5)
                with cols_gauges[i]:
                    st.plotly_chart(draw_gauge(current_value, reorder_point, col_name, max_gauge), use_container_width=True)

        # --- SECCIÓN DE ANÁLISIS ---
        st.divider()
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Demanda Agregada", f"{demanda_total} uds/día")
        with col_m2:
            st.metric("Tiempo Reposición", f"{lead_time} días")
        with col_m3:
            st.metric("Stock Crítico", f"{reorder_point} uds")

        # Histórico
        st.subheader("📈 Evolución del Inventario")
        st.line_chart(df_raw[numeric_cols].tail(20))

        with st.expander("Ver historial completo"):
            st.dataframe(df_raw.sort_index(ascending=False), use_container_width=True)

    else:
        st.warning("Conectando con Google Sheets...")

    # --- REFRESH ---
    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()
